"""Run: python3 -m unittest discover -s server -v"""
import base64
import copy
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from buffet_server import APIError, BuffetServer, DEFAULT_CONFIG, Store, export_csv

TOKEN = "a" * 64
PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aK1kAAAAASUVORK5CYII=")

def payload(sid="session-one", revision=1):
    return {
        "schemaVersion": 1, "sessionId": sid, "revision": revision, "participantId": "participant-test",
        "studyId": "study-test", "sourceSessionId": "submission-test", "condition": "default",
        "startedAt": "2026-09-15T00:00:00Z", "completedAt": "", "completed": False,
        "elapsedSeconds": 12.5, "config": dict(DEFAULT_CONFIG),
        "portions": [
            {"portionId": "p1", "foodId": "rice", "plateId": "main", "addedAt": 2.5},
            {"portionId": "p2", "foodId": "rice", "plateId": "main", "addedAt": 3.5},
            {"portionId": "p3", "foodId": "fruit", "plateId": "dessert", "addedAt": 4.5}],
        "events": [{"eventId": "e1", "eventType": "portion_added", "foodId": "rice", "portionId": "p1", "plateId": "main", "elapsedSeconds": 2.5}]
    }

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "buffet.db"
        self.store = Store(self.path)
    def tearDown(self):
        self.temp.cleanup()
    def assertAPI(self, status, function, *args):
        with self.assertRaises(APIError) as result:
            function(*args)
        self.assertEqual(status, result.exception.status)
    def test_durable_individual_portions_and_idempotent_retry(self):
        data = payload()
        self.store.save(data, TOKEN)
        self.store.save(data, TOKEN)
        reopened = Store(self.path)
        self.assertEqual(reopened.export()[0]["portions"], data["portions"])
        with reopened.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM portions").fetchone()[0], 3)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM events").fetchone()[0], 1)
        csv = export_csv(reopened.export())
        self.assertIn("main,rice,2,3,0", csv)
        self.assertIn("dessert,fruit,1,3,0", csv)
    def test_revision_conflict_and_stale_update_do_not_lose_data(self):
        first = payload()
        self.store.save(first, TOKEN)
        changed = payload(revision=2)
        changed["portions"].pop()
        self.store.save(changed, TOKEN)
        self.assertAPI(409, self.store.save, first, TOKEN)
        changed["portions"].clear()
        self.assertAPI(409, self.store.save, changed, TOKEN)
        self.assertEqual(2, len(self.store.export()[0]["portions"]))
    def test_wrong_session_secret_cannot_overwrite_or_capture(self):
        self.store.save(payload(), TOKEN)
        self.assertAPI(403, self.store.save, payload(revision=2), "b" * 64)
        self.assertAPI(403, self.store.screenshot, "session-one", "b" * 64, PNG)
    def test_completion_is_immutable_and_event_history_append_only(self):
        data = payload()
        data["completed"] = True
        data["completedAt"] = "2026-09-15T00:01:00Z"
        self.store.save(data, TOKEN)
        changed = copy.deepcopy(data)
        changed["revision"] = 2
        changed["portions"].pop()
        self.assertAPI(409, self.store.save, changed, TOKEN)
        changed = copy.deepcopy(data)
        changed["revision"] = 2
        changed["events"] = []
        self.assertAPI(409, self.store.save, changed, TOKEN)
    def test_duplicate_portions_nan_and_token_are_rejected(self):
        data = payload()
        data["portions"].append(data["portions"][0])
        self.assertAPI(400, self.store.save, data, TOKEN)
        data = payload()
        data["elapsedSeconds"] = float("nan")
        self.assertAPI(400, self.store.save, data, TOKEN)
        self.assertAPI(401, self.store.save, payload(), "bad")
    def test_screenshot_deduplicates_and_condition_rejects(self):
        self.store.save(payload(), TOKEN)
        a = self.store.screenshot("session-one", TOKEN, PNG)
        b = self.store.screenshot("session-one", TOKEN, PNG)
        self.assertEqual(a, b)
        self.assertEqual(len(self.store.export()[0]["screenshots"]), 1)
        data = payload("disabled")
        data["config"]["screenshotsEnabled"] = False
        self.store.save(data, TOKEN)
        self.assertAPI(403, self.store.screenshot, "disabled", TOKEN, PNG)
        self.assertAPI(400, self.store.screenshot, "session-one", TOKEN, b"not a PNG")
    def test_empty_session_remains_in_csv_and_formula_cells_are_escaped(self):
        data = payload()
        data["participantId"] = '=HYPERLINK("bad")'
        data["portions"] = []
        self.store.save(data, TOKEN)
        csv = export_csv(self.store.export())
        self.assertIn("'=HYPERLINK", csv)
        self.assertIn(",,,0,0,0", csv)

class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "index.html").write_text("working")
        self.server = BuffetServer(("127.0.0.1", 0), Store(self.root / "private.db"), self.root, origins=["https://survey.example.edu"], conditions_path=self.root / "conditions.json")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp.cleanup()
    def request(self, method, path, data=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=5)
        headers = headers or {}
        if isinstance(data, dict):
            data = json.dumps(data)
            headers["Content-Type"] = "application/json"
        connection.request(method, path, data, headers)
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result
    def test_full_session_flow_and_exports(self):
        status, body, _ = self.request("POST", "/api/sessions", payload(), {"X-Session-Token": TOKEN})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["revision"], 1)
        status, body, _ = self.request("POST", "/api/screenshots/session-one", PNG, {"X-Session-Token": TOKEN, "Content-Type": "image/png"})
        self.assertEqual(status, 200)
        image_id = json.loads(body)["imageId"]
        self.assertEqual(self.request("GET", "/api/screenshots/session-one/" + image_id)[1], PNG)
        status, body, _ = self.request("GET", "/api/export.json")
        session = json.loads(body)["sessions"][0]
        self.assertEqual(len(session["portions"]), 3)
        self.assertNotIn("secret", body.decode())
        self.assertNotIn(TOKEN, body.decode())
    def test_foreign_origin_and_path_traversal_are_denied(self):
        self.assertEqual(self.request("POST", "/api/sessions", payload(), {"Origin": "https://attacker.invalid", "X-Session-Token": TOKEN})[0], 403)
        self.assertEqual(self.request("GET", "/%2e%2e/buffet_server.py")[0], 404)
        self.assertEqual(self.request("GET", "/api/config?condition=missing")[0], 400)
        status, _, headers = self.request("OPTIONS", "/api/sessions", headers={"Origin": "https://survey.example.edu"})
        self.assertEqual(status, 204)
        self.assertEqual(headers["Access-Control-Allow-Origin"], "https://survey.example.edu")
    def test_condition_cannot_override_screenshot_setting(self):
        data = payload()
        data["config"]["screenshotsEnabled"] = False
        self.assertEqual(self.request("POST", "/api/sessions", data, {"X-Session-Token": TOKEN})[0], 400)
    def test_public_exports_require_admin_secret(self):
        self.server.public = True
        self.server.admin_token = "researcher-secret" * 3
        self.assertEqual(self.request("GET", "/api/export.json")[0], 401)
        self.assertEqual(self.request("GET", "/api/export.json", headers={"Authorization": "Bearer " + self.server.admin_token})[0], 200)
    def test_researcher_condition_edit_is_durable_and_old_sessions_remain_valid(self):
        self.assertEqual(self.request("POST", "/api/sessions", payload(), {"X-Session-Token": TOKEN})[0], 200)
        config = dict(DEFAULT_CONFIG)
        config["foodOrder"] = ["pizza", "rice"]
        config["screenshotsEnabled"] = False
        status, _, _ = self.request("POST", "/api/admin/conditions", {"name": "default", "config": config})
        self.assertEqual(status, 200)
        self.assertEqual(json.loads((self.root / "conditions.json").read_text())["default"]["foodOrder"], ["pizza", "rice"])
        self.assertEqual(self.request("POST", "/api/sessions", payload(revision=2), {"X-Session-Token": TOKEN})[0], 200)
        status, body, _ = self.request("GET", "/api/config")
        self.assertFalse(json.loads(body)["screenshotsEnabled"])
        self.assertEqual(self.request("GET", "/researcher")[0], 200)
    def test_researcher_settings_reject_foreign_origin_and_unknown_food(self):
        body = {"name": "new_condition", "config": dict(DEFAULT_CONFIG)}
        self.assertEqual(self.request("POST", "/api/admin/conditions", body, {"Origin": "https://survey.example.edu"})[0], 401)
        body["config"]["foodOrder"] = ["invented-food"]
        self.assertEqual(self.request("POST", "/api/admin/conditions", body)[0], 400)
        body["name"] = "../escape"
        self.assertEqual(self.request("POST", "/api/admin/conditions", body)[0], 400)
    def test_json_mime_and_size_limits(self):
        self.assertEqual(self.request("POST", "/api/sessions", "{}", {"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.request("POST", "/api/sessions", "{", {"Content-Type": "application/json"})[0], 400)
        self.assertEqual(self.request("GET", "/")[1], b"working")

if __name__ == '__main__':
    unittest.main()
