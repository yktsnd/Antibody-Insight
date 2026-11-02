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
from .domain import SCHEMA, ValidationError, fields, new_id, now, require, validate_graph
from .fixtures import composition_bundle, example_bundle, numbering_bundle
from .numbering import cdr3_groups, observations
from .storage import Store
from .structures import structure_observation

WEB = Path(__file__).resolve().parent.parent / "web"
MAX_BODY = 32 * 1024 * 1024


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
            payload = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
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
                elif parsed.path == "/api/example-composition":
                    self.reply(200, composition_bundle())
                elif parsed.path == "/api/example-numbering":
                    count = parse_qs(parsed.query).get("count", ["8"])[0]
                    require(count in ("8", "800"), "Fixture count must be 8 or 800")
                    self.reply(200, numbering_bundle(int(count)))
                elif parsed.path == "/api/numbering":
                    project_id = parse_qs(parsed.query).get("project_id", [""])[0]
                    self.reply(200, observations(self.server.store.bundle(project_id)))
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
        files = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css", "/structures.js": "structures.js",
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
                fields(data, {"text", "format", "filename", "project_id", "title", "goal"}, "request", {"structure_options"})
                if data["format"] == "json":
                    project = None
                elif data["project_id"]:
                    project = self.server.store.bundle(data["project_id"])["project"]
                else:
                    project = new_project(data["title"], data["goal"])
                result = preview(data["text"], data["format"], data["filename"], project, data.get("structure_options"))
            elif route == "/api/import":
                result = self.server.store.import_bundle(data)
            elif route == "/api/shortlist":
                fields(data, {"project_id", "candidate_ids", "evidence_ids", "reason"}, "request")
                result = self.server.store.save_shortlist(data["project_id"], data["candidate_ids"],
                                                         data["evidence_ids"], data["reason"])
            elif route == "/api/cdr3-groups":
                fields(data, {"project_id", "map_choices"}, "request")
                result = cdr3_groups(self.server.store.bundle(data["project_id"]), data["map_choices"])
            elif route == "/api/structure-map-preview":
                fields(data, {"project_id", "definition"}, "request")
                fields(data["definition"], {"structure_id", "molecule_id", "source", "chain_assignments", "residues"}, "mapping definition")
                bundle = self.server.store.bundle(data["project_id"])
                candidate = {**data["definition"], "id": new_id("structure_map"), "type": "structure_map", "project_id": data["project_id"], "created_at": now()}
                validate_graph(bundle["project"], [*bundle["entities"], candidate])
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
        print("Local development build. Full researcher workflows are not yet complete. Ctrl+C to stop.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
