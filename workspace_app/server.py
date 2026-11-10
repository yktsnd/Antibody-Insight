"""Loopback-only API and static UI. Intentionally not a shared-server deployment."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import secrets
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .adapters import new_project, parse_json, preview
from .domain import MAX_BUNDLE_BYTES, SCHEMA, ValidationError, fields, new_id, now, require, validate_extension
from .fixtures import composition_bundle, example_bundle, numbering_bundle, research_example_bundle
from .numbering import cdr3_groups, observations
from .observation import observation_order
from .storage import Store
from .structures import structure_observation
from .design import design_context, variant_preview
from .hypotheses import hypothesis_preview
from .assembly import composition_context, composition_preview
from .experiments import construct_context, metadata_preview
from .measurements import measurement_preview
from .decisions import decision_context, decision_review
from .predictions import prediction_preview, prediction_targets

WEB = Path(__file__).resolve().parent.parent / "web"
MAX_BODY = MAX_BUNDLE_BYTES


def default_database():
    base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
    return base / "AntibodyInsight" / "workspace.sqlite3"


class WorkspaceServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, store):
        super().__init__(address, Handler)
        self.store = store
        self.session = secrets.token_urlsafe(32)
        self.csrf = secrets.token_urlsafe(32)
        self.origin = f"http://127.0.0.1:{self.server_port}"


class Handler(BaseHTTPRequestHandler):
    server_version = "AntibodyInsight"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(15)

    def log_message(self, fmt, *args):
        # Paths, filenames, headers and user data are deliberately not logged.
        pass

    def reply(self, status, payload, content_type="application/json; charset=utf-8", session=False):
        if not isinstance(payload, bytes):
            if isinstance(payload, dict):
                reviewed = payload.get("bundle")
                if isinstance(reviewed, dict) and reviewed.get("schema_version") == SCHEMA and isinstance(reviewed.get("entities"), list):
                    # Keep approved number representations across the JavaScript UI.
                    # This is envelope metadata, never an extra awx/1 entity field.
                    payload = {**payload, "serialized_bundle": json.dumps(reviewed, ensure_ascii=False, allow_nan=False)}
            # Rejected input can contain escaped lone surrogate code points in
            # diagnostic keys. Escape error JSON so a validation failure cannot
            # itself break UTF-8 transport; successful source bundles stay exact.
            payload = json.dumps(payload, ensure_ascii=status >= 400, allow_nan=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; "
                         "connect-src 'self'; img-src 'self' data:; object-src 'none'; base-uri 'none'; "
                         "frame-ancestors 'none'; form-action 'self'")
        if session:
            self.send_header("Set-Cookie", f"aw_session={self.server.session}; HttpOnly; SameSite=Strict; Path=/")
        self.end_headers()
        self.wfile.write(payload)

    def host_ok(self):
        return self.headers.get("Host") == urlsplit(self.server.origin).netloc

    def authorized(self):
        try:
            cookies = SimpleCookie(self.headers.get("Cookie", ""))
            session = cookies.get("aw_session")
            return bool(session) and secrets.compare_digest(session.value, self.server.session)
        except Exception:
            return False

    def do_GET(self):
        if not self.host_ok():
            self.reply(403, {"error": "Untrusted Host"})
            return
        parsed = urlsplit(self.path)
        if parsed.path.startswith("/api/"):
            if not self.authorized() or self.headers.get("Sec-Fetch-Site") == "cross-site":
                self.reply(401, {"error": "Open the local application first"})
                return
            try:
                if parsed.path == "/api/bootstrap":
                    self.reply(200, {"csrf": self.server.csrf, "version": __version__,
                                     "projects": self.server.store.projects(), "external_network": False})
                elif parsed.path == "/api/bundle":
                    project_id = parse_qs(parsed.query).get("project_id", [""])[0]
                    self.reply(200, self.server.store.bundle(project_id))
                elif parsed.path == "/api/example":
                    self.reply(200, example_bundle())
                elif parsed.path == "/api/example-research":
                    self.reply(200, research_example_bundle())
                elif parsed.path == "/api/example-composition":
                    self.reply(200, composition_bundle())
                elif parsed.path == "/api/example-numbering":
                    count = parse_qs(parsed.query).get("count", ["8"])[0]
                    require(count in ("8", "800"), "Fixture count must be 8 or 800")
                    self.reply(200, numbering_bundle(int(count)))
                elif parsed.path == "/api/numbering":
                    project_id = parse_qs(parsed.query).get("project_id", [""])[0]
                    self.reply(200, observations(self.server.store.bundle(project_id)))
                elif parsed.path == "/api/composition-context":
                    query = parse_qs(parsed.query)
                    self.reply(200, composition_context(self.server.store.bundle(query.get("project_id", [""])[0]), query.get("molecule_id", [""])[0]))
                elif parsed.path == "/api/construct-context":
                    query = parse_qs(parsed.query, keep_blank_values=True)
                    require(set(query) <= {'project_id', 'molecule_id', 'left_id', 'right_id', 'cohort_id'}
                            and all(len(values) == 1 for values in query.values()), 'Unsupported or repeated construct context query')
                    self.reply(200, construct_context(self.server.store.bundle(query.get('project_id', [''])[0]),
                        query.get('molecule_id', [''])[0], query.get('left_id', [None])[0],
                        query.get('right_id', [None])[0], query.get('cohort_id', [None])[0]))
                elif parsed.path == "/api/example-structures":
                    from .structure_fixtures import structure_bundle
                    self.reply(200, structure_bundle())
                elif parsed.path == "/api/structure-view":
                    query = parse_qs(parsed.query)
                    bundle = self.server.store.bundle(query.get("project_id", [""])[0])
                    self.reply(200, structure_observation(bundle, query.get("structure_id", [""])[0], query.get("map_id", [None])[0]))
                else:
                    self.reply(404, {"error": "Unknown API route"})
            except ValidationError as exc:
                self.reply(422, {"error": str(exc), "details": exc.details})
            return
        files = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css", "/structures.js": "structures.js", "/design.js": "design.js", "/composition.js": "composition.js", "/experiments.js": "experiments.js", "/decisions.js": "decisions.js", "/predictions.js": "predictions.js",
                 "/vendor/3Dmol-2.5.5.min.js": "vendor/3Dmol-2.5.5.min.js"}
        filename = files.get(parsed.path)
        if filename is None:
            self.reply(404, {"error": "Not found"})
            return
        path = WEB / filename
        self.reply(200, path.read_bytes(), mimetypes.guess_type(filename)[0] + "; charset=utf-8", session=parsed.path == "/")

    def do_POST(self):
        if (not self.host_ok() or self.headers.get("Origin") != self.server.origin
                or not self.authorized() or self.headers.get("X-CSRF-Token") != self.server.csrf):
            self.reply(403, {"error": "Local session, matching Origin and CSRF token required"})
            return
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            self.reply(415, {"error": "Expected application/json"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            require(0 < length <= MAX_BODY, "Request must contain 1–33,554,432 bytes")
            raw = self.rfile.read(length).decode("utf-8")
            data = parse_json(raw)
            route = urlsplit(self.path).path
            if route == "/api/preview":
                fields(data, {"text", "format", "filename", "project_id", "title", "goal"}, "request", {"structure_options", "sequence_options", "data_class"})
                if data["format"] == "json":
                    project = None
                elif data["project_id"]:
                    project = self.server.store.bundle(data["project_id"])["project"]
                else:
                    project = new_project(data["title"], data["goal"], data.get("data_class", "research"))
                result = preview(data["text"], data["format"], data["filename"], project, data.get("structure_options"), data.get('sequence_options'))
                if any(e['type'] == 'structure_map' for e in result['bundle']['entities']):
                    # Resolve append-file maps against this local project too.
                    # Collision rejection remains transactional at commit.
                    incoming = result['bundle']['entities']
                    pid = result['bundle']['project']['id']
                    previous = self.server.store.bundle(pid)['entities'] if any(p['id'] == pid for p in self.server.store.projects()) else []
                    from .structures import validate_structure_references
                    validate_structure_references({e['id']: e for e in [*previous, *incoming]},
                                                  {e['id'] for e in previous} - {e['id'] for e in incoming})
            elif route == "/api/import":
                result = self.server.store.import_bundle(data)
            elif route == "/api/measurement-preview":
                fields(data, {'project_id', 'text', 'filename', 'mappings', 'file_source', 'mapping_text_sha256'}, 'request')
                result = measurement_preview(self.server.store.bundle(data['project_id']), data['text'], data['filename'],
                                             data['mappings'], data['file_source'], data['mapping_text_sha256'])
            elif route == "/api/metadata-preview":
                fields(data, {'project_id', 'definition'}, 'request')
                result = metadata_preview(self.server.store.bundle(data['project_id']), data['definition'])
            elif route == "/api/decision-context":
                fields(data, {'project_id', 'candidate_ids'}, 'request')
                result = decision_context(self.server.store.bundle(data['project_id']), data['candidate_ids'])
            elif route == "/api/decision-review":
                fields(data, {'project_id', 'definition'}, 'request')
                result = decision_review(self.server.store.bundle(data['project_id']), data['definition'])
            elif route == "/api/prediction-targets":
                fields(data, {'project_id'}, 'request')
                result = prediction_targets(self.server.store.bundle(data['project_id']))
            elif route == "/api/prediction-preview":
                fields(data, {'project_id', 'text', 'filename', 'file_format', 'bindings', 'options', 'bindings_text_sha256'}, 'request')
                result = prediction_preview(self.server.store.bundle(data['project_id']), data['text'], data['filename'],
                                            data['file_format'], data['bindings'], data['options'], data['bindings_text_sha256'])
            elif route == "/api/shortlist":
                fields(data, {"project_id", "candidate_ids", "evidence_ids", "reason"}, "request")
                result = self.server.store.save_shortlist(data["project_id"], data["candidate_ids"],
                                                         data["evidence_ids"], data["reason"])
            elif route == "/api/cdr3-groups":
                fields(data, {"project_id", "map_choices"}, "request")
                result = cdr3_groups(self.server.store.bundle(data["project_id"]), data["map_choices"])
            elif route == "/api/observation-order":
                fields(data, {"project_id", "cohort_id", "choices", "direction"}, "request")
                result = observation_order(self.server.store.bundle(data["project_id"]), data["cohort_id"], data["choices"], data["direction"])
            elif route == "/api/design-context":
                fields(data, {"project_id", "parent_id", "map_id", "reference_map_id"}, "request")
                result = design_context(self.server.store.bundle(data["project_id"]), data["parent_id"], data["map_id"], data["reference_map_id"])
            elif route == "/api/variant-preview":
                fields(data, {"project_id", "parent_id", "name", "external_id", "reason", "substitutions"}, "request")
                result = variant_preview(self.server.store.bundle(data["project_id"]), data["parent_id"], data["name"], data["external_id"], data["reason"], data["substitutions"])
            elif route == "/api/hypothesis-preview":
                fields(data, {"project_id", "definition"}, "request")
                result = hypothesis_preview(self.server.store.bundle(data["project_id"]), data["definition"])
            elif route == "/api/composition-preview":
                fields(data, {"project_id", "definition"}, "request")
                result = composition_preview(self.server.store.bundle(data["project_id"]), data["definition"])
            elif route == "/api/composition-review":
                fields(data, {"project_id", "definition"}, "request")
                original = self.server.store.bundle(data["project_id"])
                candidate = composition_preview(original, data["definition"])
                result = {"bundle": candidate, "context": composition_context({**original, "entities": original["entities"] + candidate["entities"]}, candidate["entities"][0]["id"])}
            elif route == "/api/structure-map-preview":
                fields(data, {"project_id", "definition"}, "request")
                fields(data["definition"], {"structure_id", "molecule_id", "source", "chain_assignments", "residues"}, "mapping definition")
                bundle = self.server.store.bundle(data["project_id"])
                candidate = {**data["definition"], "id": new_id("structure_map"), "type": "structure_map", "project_id": data["project_id"], "created_at": now()}
                validate_extension(bundle["project"], bundle["entities"], [candidate])
                result = {"schema_version": SCHEMA, "project": bundle["project"], "entities": [candidate]}
            else:
                self.reply(404, {"error": "Unknown API route"})
                return
            self.reply(200, result)
        except ValidationError as exc:
            self.reply(422, {"error": str(exc), "details": exc.details})
        except (UnicodeError, ValueError, TypeError, KeyError, RecursionError):
            self.reply(422, {"error": "Malformed request; no data saved"})


def make_server(database, port=8765):
    return WorkspaceServer(("127.0.0.1", port), Store(database))


def main():
    parser = argparse.ArgumentParser(description="Local Antibody Insight workspace (development)")
    parser.add_argument("--database", type=Path, default=default_database())
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    require(0 <= args.port <= 65535, "Invalid port")
    with make_server(args.database, args.port) as server:
        print(f"Antibody Insight {__version__}: {server.origin}", flush=True)
        print(f"Database: {args.database.resolve()}", flush=True)
        print("Local development build. Release 1.0 validation remains incomplete. Ctrl+C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
