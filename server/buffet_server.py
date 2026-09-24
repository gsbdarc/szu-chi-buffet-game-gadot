#!/usr/bin/env python3
"""Buffet research sandbox: stdlib HTTP + transactional SQLite. No dependencies."""
import argparse
import csv
from contextlib import contextmanager
import hashlib
import hmac
import io
import ipaddress
import json
import math
import mimetypes
import os
from pathlib import Path
import re
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
TOKEN = re.compile(r"^[A-Za-z0-9_-]{32,128}$")
PNG = b"\x89PNG\r\n\x1a\n"
MAX_JSON = 2 * 1024 * 1024
MAX_PNG = 8 * 1024 * 1024
DEFAULT_CONFIG = {
    "condition": "default", "screenshotsEnabled": True, "soundEnabled": True,
    "allowRemoval": True, "maxPortions": 40, "apiBaseUrl": "", "parentOrigin": "",
    "introSeconds": 4, "foodOrder": [], "studyTitle": "Welcome to the buffet",
    "instructions": "Imagine choosing a meal at a buffet. Explore the dishes and serve the amount you would like to eat. There are no right or wrong choices."
}

class APIError(Exception):
    def __init__(self, status, message):
        self.status, self.message = status, message


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def identifier(value, field):
    if not isinstance(value, str) or not ID.fullmatch(value):
        raise APIError(400, "Invalid " + field)
    return value


def number(value, field, maximum=8640000):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or not 0 <= value <= maximum:
        raise APIError(400, "Invalid " + field)
    return value


def validate_payload(data):
    if not isinstance(data, dict):
        raise APIError(400, "Expected an object")
    identifier(data.get("sessionId"), "sessionId")
    if type(data.get("revision")) is not int or not 1 <= data["revision"] <= 1000000:
        raise APIError(400, "Invalid revision")
    if type(data.get("completed")) is not bool:
        raise APIError(400, "Invalid completed")
    number(data.get("elapsedSeconds"), "elapsedSeconds")
    for key in ("participantId", "studyId", "sourceSessionId", "condition", "startedAt", "completedAt"):
        if not isinstance(data.get(key, ""), str) or len(data.get(key, "")) > 200:
            raise APIError(400, "Invalid " + key)
    if not isinstance(data.get("config"), dict):
        raise APIError(400, "Missing config")
    if type(data["config"].get("screenshotsEnabled")) is not bool:
        raise APIError(400, "Invalid screenshot setting")
    portions, events = data.get("portions"), data.get("events")
    if not isinstance(portions, list) or len(portions) > 200 or not isinstance(events, list) or len(events) > 20000:
        raise APIError(400, "Invalid portions or events")
    seen = set()
    for p in portions:
        if not isinstance(p, dict):
            raise APIError(400, "Invalid portion")
        for key in ("portionId", "foodId", "plateId"):
            identifier(p.get(key), key)
        number(p.get("addedAt"), "addedAt")
        if p["portionId"] in seen:
            raise APIError(400, "Duplicate portionId")
        seen.add(p["portionId"])
    seen.clear()
    for e in events:
        if not isinstance(e, dict):
            raise APIError(400, "Invalid event")
        for key in ("eventId", "eventType"):
            identifier(e.get(key), key)
        for key in ("foodId", "portionId", "plateId"):
            if e.get(key):
                identifier(e[key], key)
        number(e.get("elapsedSeconds"), "event elapsedSeconds")
        if e["eventId"] in seen:
            raise APIError(400, "Duplicate eventId")
        seen.add(e["eventId"])
    return data


class Store:
    def __init__(self, path):
        self.path = str(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.executescript("""
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS sessions(
              session_id TEXT PRIMARY KEY, secret_hash TEXT NOT NULL,
              revision INTEGER NOT NULL, payload TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS portions(
              session_id TEXT NOT NULL, portion_id TEXT NOT NULL, food_id TEXT NOT NULL,
              plate_id TEXT NOT NULL, added_at REAL NOT NULL,
              PRIMARY KEY(session_id,portion_id));
            CREATE TABLE IF NOT EXISTS events(
              session_id TEXT NOT NULL, event_id TEXT NOT NULL, payload TEXT NOT NULL,
              PRIMARY KEY(session_id,event_id));
            CREATE TABLE IF NOT EXISTS screenshots(
              session_id TEXT NOT NULL, image_id TEXT NOT NULL, png BLOB NOT NULL,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY(session_id,image_id));
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=20)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA synchronous=FULL")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def secret(token):
        if not isinstance(token, str) or not TOKEN.fullmatch(token):
            raise APIError(401, "A session token is required")
        return hashlib.sha256(token.encode()).hexdigest()

    def authorize(self, db, session_id, token):
        secret = self.secret(token)
        row = db.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if not row or not hmac.compare_digest(secret, row["secret_hash"]):
            raise APIError(403, "Session credentials do not match")
        return row

    def save(self, data, token):
        data = validate_payload(data)
        secret, raw, sid = self.secret(token), canonical(data), data["sessionId"]
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT * FROM sessions WHERE session_id=?", (sid,)).fetchone()
            if old:
                if not hmac.compare_digest(secret, old["secret_hash"]):
                    raise APIError(403, "Session credentials do not match")
                prior = json.loads(old["payload"])
                if data["revision"] < old["revision"]:
                    raise APIError(409, "A newer revision is already stored; recover the latest session")
                if data["revision"] == old["revision"]:
                    if raw != old["payload"]:
                        raise APIError(409, "Revision already contains different data")
                    return {"ok": True, "sessionId": sid, "revision": old["revision"]}
                for key in ("participantId", "studyId", "sourceSessionId", "condition", "startedAt", "config"):
                    if data.get(key) != prior.get(key):
                        raise APIError(409, "Session metadata cannot change")
                if data["elapsedSeconds"] < prior["elapsedSeconds"]:
                    raise APIError(409, "Elapsed time cannot decrease")
                if prior["completed"] and (not data["completed"] or data["portions"] != prior["portions"] or data.get("completedAt") != prior.get("completedAt")):
                    raise APIError(409, "Completed portions cannot change")
                previous_events = {e["eventId"]: e for e in prior["events"]}
                next_events = {e["eventId"]: e for e in data["events"]}
                if any(next_events.get(k) != value for k, value in previous_events.items()):
                    raise APIError(409, "Event history is append-only")
                db.execute("UPDATE sessions SET revision=?,payload=?,updated_at=CURRENT_TIMESTAMP WHERE session_id=?", (data["revision"], raw, sid))
            else:
                db.execute("INSERT INTO sessions(session_id,secret_hash,revision,payload) VALUES(?,?,?,?)", (sid, secret, data["revision"], raw))
            db.execute("DELETE FROM portions WHERE session_id=?", (sid,))
            db.executemany("INSERT INTO portions VALUES(?,?,?,?,?)", [(sid, p["portionId"], p["foodId"], p["plateId"], p["addedAt"]) for p in data["portions"]])
            db.executemany("INSERT OR IGNORE INTO events VALUES(?,?,?)", [(sid, e["eventId"], canonical(e)) for e in data["events"]])
        return {"ok": True, "sessionId": sid, "revision": data["revision"]}

    def screenshot(self, sid, token, png):
        identifier(sid, "sessionId")
        if len(png) < 24 or not png.startswith(PNG) or png[12:16] != b"IHDR":
            raise APIError(400, "Expected PNG image")
        width, height = int.from_bytes(png[16:20], "big"), int.from_bytes(png[20:24], "big")
        if not 1 <= width <= 8192 or not 1 <= height <= 8192 or width * height > 20000000:
            raise APIError(400, "Image dimensions exceed limits")
        image_id = hashlib.sha256(png).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = self.authorize(db, sid, token)
            if not json.loads(row["payload"])["config"]["screenshotsEnabled"]:
                raise APIError(403, "Screenshots are disabled for this session")
            count = db.execute("SELECT COUNT(*) FROM screenshots WHERE session_id=?", (sid,)).fetchone()[0]
            existing = db.execute("SELECT 1 FROM screenshots WHERE session_id=? AND image_id=?", (sid, image_id)).fetchone()
            if count >= 30 and not existing:
                raise APIError(429, "Session screenshot limit reached")
            db.execute("INSERT OR IGNORE INTO screenshots(session_id,image_id,png) VALUES(?,?,?)", (sid, image_id, png))
        return {"ok": True, "sessionId": sid, "imageId": image_id}

    def export(self):
        with self.connect() as db:
            rows = db.execute("SELECT payload,created_at,updated_at FROM sessions ORDER BY created_at,session_id").fetchall()
            result = []
            for row in rows:
                value = json.loads(row["payload"])
                value["serverCreatedAt"], value["serverUpdatedAt"] = row["created_at"], row["updated_at"]
                value["screenshots"] = [dict(x) for x in db.execute("SELECT image_id AS imageId,created_at AS createdAt FROM screenshots WHERE session_id=? ORDER BY created_at", (value["sessionId"],))]
                result.append(value)
            return result


def safe_csv(value):
    value = str(value)
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else value


def export_csv(sessions):
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(["session_id", "participant_id", "study_id", "source_session_id", "condition", "completed", "elapsed_seconds", "plate_id", "food_id", "portions", "total_portions", "screenshot_count"])
    for session in sessions:
        counts = {}
        for portion in session["portions"]:
            key = (portion["plateId"], portion["foodId"])
            counts[key] = counts.get(key, 0) + 1
        for (plate, food), count in sorted(counts.items()) or [(("", ""), 0)]:
            row = [session["sessionId"], session.get("participantId", ""), session.get("studyId", ""), session.get("sourceSessionId", ""), session.get("condition", ""), session["completed"], session["elapsedSeconds"], plate, food, count, len(session["portions"]), len(session["screenshots"])]
            writer.writerow([safe_csv(v) for v in row])
    return out.getvalue()


class BuffetServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, address, store, web_root, admin_token="", origins=(), conditions=None, conditions_path=None):
        super().__init__(address, Handler)
        self.store, self.web_root, self.admin_token = store, Path(web_root).resolve(), admin_token
        self.origins = set(origins)
        self.conditions = conditions or {"default": DEFAULT_CONFIG}
        self.conditions_path = Path(conditions_path) if conditions_path else None
        self.conditions_lock = threading.Lock()
        self.public = address[0] not in ("127.0.0.1", "localhost", "::1")


class Handler(BaseHTTPRequestHandler):
    server_version = "BuffetResearch/1"
    def log_message(self, fmt, *args):
        # Never log query strings containing participant IDs or authorization tokens.
        print("%s %s" % (self.command, urlsplit(self.path).path), flush=True)

    def send(self, status, body, content_type="application/json", extra=None):
        if not isinstance(body, bytes):
            body = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store" if self.path.startswith("/api/") else "no-cache")
        origin = self.headers.get("Origin")
        if origin in self.server.origins:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def json(self, value, status=200):
        self.send(status, canonical(value))

    def check_origin(self):
        if not self.server.public:
            host = urlsplit("//" + self.headers.get("Host", "")).hostname
            if host not in ("localhost", "127.0.0.1", "::1"):
                raise APIError(403, "Invalid local host")
        origin = self.headers.get("Origin")
        if origin:
            try:
                parsed = urlsplit(origin)
                same_host = parsed.netloc == self.headers.get("Host") and parsed.scheme in ("http", "https")
            except ValueError:
                same_host = False
            if not same_host and origin not in self.server.origins:
                raise APIError(403, "Origin is not allowed")

    def admin(self):
        token = self.headers.get("Authorization", "").removeprefix("Bearer ")
        local_client = ipaddress.ip_address(self.client_address[0]).is_loopback
        origin = self.headers.get("Origin", "")
        foreign_origin = bool(origin and urlsplit(origin).netloc != self.headers.get("Host"))
        if self.server.public or not local_client or self.server.admin_token or foreign_origin:
            if not self.server.admin_token or not hmac.compare_digest(token, self.server.admin_token):
                raise APIError(401, "Researcher authorization is required")

    def body(self, maximum):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise APIError(400, "Invalid Content-Length")
        if not 1 <= length <= maximum:
            raise APIError(413, "Request size exceeds limit")
        return self.rfile.read(length)

    def do_OPTIONS(self):
        try:
            self.check_origin()
            self.send(204, b"", extra={"Access-Control-Allow-Methods": "GET,POST,OPTIONS", "Access-Control-Allow-Headers": "Content-Type,X-Session-Token,Authorization"})
        except APIError as error:
            self.json({"ok": False, "error": error.message}, error.status)

    def do_POST(self):
        try:
            self.check_origin()
            path = urlsplit(self.path).path
            token = self.headers.get("X-Session-Token", "")
            if path == "/api/admin/conditions":
                self.admin()
                if self.headers.get_content_type() != "application/json":
                    raise APIError(415, "Expected application/json")
                data = json.loads(self.body(MAX_JSON))
                if not isinstance(data, dict):
                    raise APIError(400, "Expected condition object")
                name = identifier(data.get("name"), "condition name")
                config = data.get("config")
                if not isinstance(config, dict):
                    raise APIError(400, "Expected configuration")
                clean = dict(DEFAULT_CONFIG)
                clean["condition"] = name
                for key in ("screenshotsEnabled", "soundEnabled", "allowRemoval"):
                    if type(config.get(key)) is not bool:
                        raise APIError(400, "Invalid " + key)
                    clean[key] = config[key]
                for key, limit in (("studyTitle", 200), ("instructions", 3000)):
                    if not isinstance(config.get(key), str) or not 1 <= len(config[key]) <= limit:
                        raise APIError(400, "Invalid " + key)
                    clean[key] = config[key]
                for key, low, high in (("maxPortions", 1, 200), ("introSeconds", 0, 30)):
                    value = number(config.get(key), key, high)
                    if value < low or (key == "maxPortions" and type(value) is not int):
                        raise APIError(400, "Invalid " + key)
                    clean[key] = value
                menu = json.loads((ROOT / "web/assets/menu.json").read_text())["foods"]
                known = {food["id"] for food in menu}
                order = config.get("foodOrder")
                if not isinstance(order, list) or any(not isinstance(food, str) or food not in known for food in order) or len(order) != len(set(order)):
                    raise APIError(400, "Invalid food selection or order")
                clean["foodOrder"] = order
                if self.server.conditions_path is None:
                    raise APIError(503, "Condition file is not configured for writing")
                with self.server.conditions_lock:
                    updated = dict(self.server.conditions)
                    updated[name] = clean
                    path = self.server.conditions_path
                    path.parent.mkdir(parents=True, exist_ok=True)
                    temporary = path.with_suffix(path.suffix + ".tmp")
                    with temporary.open("w") as handle:
                        json.dump(updated, handle, indent=2)
                        handle.flush()
                        os.fsync(handle.fileno())
                    os.replace(temporary, path)
                    self.server.conditions = updated
                self.json({"ok": True, "condition": name, "config": clean})
            elif path == "/api/sessions":
                if self.headers.get_content_type() != "application/json":
                    raise APIError(415, "Expected application/json")
                data = validate_payload(json.loads(self.body(MAX_JSON)))
                condition = data.get("condition", "default")
                if condition not in self.server.conditions:
                    raise APIError(400, "Unknown study condition")
                with self.server.store.connect() as db:
                    existing = db.execute("SELECT payload FROM sessions WHERE session_id=?", (data["sessionId"],)).fetchone()
                expected = json.loads(existing["payload"])["config"] if existing else dict(DEFAULT_CONFIG, **self.server.conditions[condition])
                for key in ("screenshotsEnabled", "allowRemoval", "maxPortions", "foodOrder", "introSeconds"):
                    if data["config"].get(key) != expected[key]:
                        raise APIError(400, "Study setting does not match assigned condition: " + key)
                if len(data["portions"]) > expected["maxPortions"]:
                    raise APIError(400, "Portion limit exceeded")
                self.json(self.server.store.save(data, token))
            elif path.startswith("/api/screenshots/"):
                if self.headers.get_content_type() != "image/png":
                    raise APIError(415, "Expected image/png")
                self.json(self.server.store.screenshot(path[len("/api/screenshots/"):], token, self.body(MAX_PNG)))
            else:
                raise APIError(404, "Unknown endpoint")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.json({"ok": False, "error": "Invalid JSON"}, 400)
        except APIError as error:
            self.json({"ok": False, "error": error.message}, error.status)
        except Exception as error:
            print("Request failed:", type(error).__name__, flush=True)
            self.json({"ok": False, "error": "Storage failed; retry is safe"}, 500)

    def do_GET(self):
        try:
            self.check_origin()
            parsed = urlsplit(self.path)
            if parsed.path == "/api/admin/conditions":
                self.admin()
                menu = json.loads((ROOT / "web/assets/menu.json").read_text())["foods"]
                return self.json({"ok": True, "conditions": self.server.conditions, "defaults": DEFAULT_CONFIG, "foods": menu})
            if parsed.path == "/researcher":
                return self.send(200, (ROOT / "study/builder.html").read_bytes(), "text/html; charset=utf-8")
            if parsed.path == "/api/health":
                with self.server.store.connect() as db:
                    db.execute("SELECT 1").fetchone()
                return self.json({"ok": True, "service": "buffet", "schemaVersion": 1})
            if parsed.path == "/api/config":
                params = parse_qs(parsed.query)
                condition = params.get("condition", ["default"])[0]
                if condition not in self.server.conditions:
                    raise APIError(400, "Unknown study condition")
                config = dict(DEFAULT_CONFIG, **self.server.conditions[condition])
                config["condition"] = condition
                local_origins = {"http://127.0.0.1:%s" % self.server.server_port, "http://localhost:%s" % self.server.server_port} if not self.server.public else set()
                config["allowedParentOrigins"] = sorted(self.server.origins | local_origins)
                return self.json(config)
            if parsed.path in ("/api/export.json", "/api/export.csv"):
                self.admin()
                sessions = self.server.store.export()
                if parsed.path.endswith(".json"):
                    return self.json({"schemaVersion": 1, "sessions": sessions})
                return self.send(200, export_csv(sessions), "text/csv; charset=utf-8", {"Content-Disposition": 'attachment; filename="buffet-portions.csv"'})
            if parsed.path.startswith("/api/screenshots/"):
                self.admin()
                parts = parsed.path.split("/")
                if len(parts) != 5:
                    raise APIError(404, "Image not found")
                with self.server.store.connect() as db:
                    row = db.execute("SELECT png FROM screenshots WHERE session_id=? AND image_id=?", (parts[3], parts[4])).fetchone()
                if not row:
                    raise APIError(404, "Image not found")
                return self.send(200, row["png"], "image/png")
            if parsed.path.startswith("/api/"):
                raise APIError(404, "Unknown endpoint")
            if parsed.path.startswith("/study/"):
                base, relative = ROOT / "study", unquote(parsed.path[len("/study/"):])
            else:
                base, relative = self.server.web_root, unquote(parsed.path.lstrip("/")) or "index.html"
            candidate = (base / relative).resolve()
            if not candidate.is_relative_to(base.resolve()) or not candidate.is_file():
                if parsed.path == "/" and not (base / "index.html").exists():
                    return self.send(503, "The Godot web directory is missing. Restore the web folder, then reload.", "text/plain; charset=utf-8")
                raise APIError(404, "File not found")
            kind = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            extra = {}
            if candidate.suffix in (".gz", ".br"):
                extra["Content-Encoding"] = "gzip" if candidate.suffix == ".gz" else "br"
                kind = mimetypes.guess_type(candidate.stem)[0] or "application/octet-stream"
            if ".wasm" in candidate.name:
                kind = "application/wasm"
            return self.send(200, candidate.read_bytes(), kind, extra)
        except APIError as error:
            self.json({"ok": False, "error": error.message}, error.status)
        except Exception as error:
            print("Request failed:", type(error).__name__, flush=True)
            self.json({"ok": False, "error": "Server could not read requested data"}, 500)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8770)
    parser.add_argument("--db", default=str(ROOT / "server/data/buffet.sqlite3"))
    parser.add_argument("--web-root", default=str(ROOT / "web"))
    parser.add_argument("--conditions", default=str(ROOT / "study/conditions.json"))
    parser.add_argument("--allow-origin", action="append", default=[])
    args = parser.parse_args()
    admin_token = os.environ.get("BUFFET_ADMIN_TOKEN", "")
    if args.host not in ("127.0.0.1", "localhost", "::1") and len(admin_token) < 32:
        parser.error("Set BUFFET_ADMIN_TOKEN to a random secret of at least 32 characters before exposing the server")
    conditions = json.loads(Path(args.conditions).read_text()) if Path(args.conditions).exists() else None
    server = BuffetServer((args.host, args.port), Store(args.db), args.web_root, admin_token, args.allow_origin, conditions, args.conditions)
    print("Buffet sandbox: http://%s:%s\nDatabase: %s" % (args.host, args.port, args.db), flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
