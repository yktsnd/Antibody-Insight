"""Transactional append-only storage, separate from scientific rules."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from pathlib import Path

from .domain import SCHEMA, ValidationError, fields, require, shortlist, validate_extension, validate_transport_size


class Store:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db, db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                INSERT OR IGNORE INTO metadata VALUES ('schema_version', 'awx/1');
                CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS entities(
                    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
                    kind TEXT NOT NULL, external_id TEXT, payload TEXT NOT NULL,
                    UNIQUE(project_id, external_id));
                CREATE INDEX IF NOT EXISTS project_entities ON entities(project_id, kind);
                CREATE TRIGGER IF NOT EXISTS immutable_entity_update BEFORE UPDATE ON entities
                    BEGIN SELECT RAISE(ABORT, 'Entities are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_entity_delete BEFORE DELETE ON entities
                    BEGIN SELECT RAISE(ABORT, 'Entities are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_project_update BEFORE UPDATE ON projects
                    BEGIN SELECT RAISE(ABORT, 'Projects are append-only'); END;
                CREATE TRIGGER IF NOT EXISTS immutable_project_delete BEFORE DELETE ON projects
                    BEGIN SELECT RAISE(ABORT, 'Projects are append-only'); END;
            """)
            require(db.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone()[0] == SCHEMA,
                    "Unsupported database schema; no migration performed")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.execute("PRAGMA foreign_keys=ON")
        return db

    @staticmethod
    def _bundle(db, project_id):
        row = db.execute("SELECT payload FROM projects WHERE id=?", (project_id,)).fetchone()
        require(row is not None, "Unknown project ID")
        return {"schema_version": SCHEMA, "project": json.loads(row[0]), "entities": [
            json.loads(r[0]) for r in db.execute("SELECT payload FROM entities WHERE project_id=? ORDER BY rowid", (project_id,))]}

    def bundle(self, project_id):
        with closing(self.connect()) as db, db:
            return self._bundle(db, project_id)

    def projects(self):
        with closing(self.connect()) as db:
            return [json.loads(r[0]) for r in db.execute("SELECT payload FROM projects ORDER BY rowid")]

    @staticmethod
    def _insert(db, entity):
        db.execute("INSERT INTO entities(id, project_id, kind, external_id, payload) VALUES(?,?,?,?,?)",
                   (entity["id"], entity["project_id"], entity["type"], entity.get("external_id"),
                    json.dumps(entity, ensure_ascii=False, allow_nan=False)))

    def import_bundle(self, bundle):
        fields(bundle, {"schema_version", "project", "entities"}, "bundle")
        require(bundle["schema_version"] == SCHEMA, "Unsupported bundle schema")
        project, incoming = bundle["project"], bundle["entities"]
        # Check standalone shapes first. References may point to existing entities.
        require(isinstance(project, dict) and isinstance(incoming, list), "Invalid bundle")
        require("id" in project and isinstance(project["id"], str), "Project ID required")
        try:
            with closing(self.connect()) as db, db:
                db.execute("BEGIN IMMEDIATE")
                current = db.execute("SELECT payload FROM projects WHERE id=?", (project["id"],)).fetchone()
                previous = []
                if current:
                    old = self._bundle(db, project["id"])
                    require(old["project"] == project, "Project ID collision: contents differ")
                    previous = old["entities"]
                validate_extension(project, previous, incoming)
                validate_transport_size(project, previous + incoming)
                existing_ids = {r[0] for r in db.execute("SELECT id FROM entities")}
                collisions = [e["id"] for e in incoming if e["id"] in existing_ids]
                if collisions:
                    raise ValidationError("Internal ID collision; nothing was imported", collisions)
                if not current:
                    db.execute("INSERT INTO projects VALUES (?,?)", (project["id"], json.dumps(project, ensure_ascii=False)))
                for entity in incoming:
                    self._insert(db, entity)
                return {"project_id": project["id"], "imported": len(incoming)}
        except sqlite3.IntegrityError as exc:
            raise ValidationError("ID collision; entire import rolled back") from exc

    def save_shortlist(self, project_id, candidate_ids, evidence_ids, reason):
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            bundle = self._bundle(db, project_id)
            decision = shortlist(bundle["project"], bundle["entities"], candidate_ids, evidence_ids, reason)
            validate_transport_size(bundle['project'], [*bundle['entities'], decision])
            self._insert(db, decision)
            return decision
