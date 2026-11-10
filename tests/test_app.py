"""Live loopback HTTP tests with synthetic data and no external inference."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from therapybot.app import create_server
from therapybot.model import ModelClient, ModelError


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.server = create_server(0, str(Path(self.temp.name) / "vault.sqlite3"))
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.csrf = {"X-TherapyBot-Token": self.server.csrf}

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.vault.close()
        self.thread.join(timeout=2)

    def request(self, path, method="GET", data=None, headers=None):
        body = None if data is None else json.dumps(data).encode("utf-8")
        req = urllib.request.Request(self.base + path, method=method, data=body, headers={"Content-Type": "application/json", **(headers or {})})
        try:
            with urllib.request.urlopen(req, timeout=4) as resp:
                content = resp.read()
                if resp.headers.get("Content-Type", "").startswith("application/json"):
                    return resp.status, json.loads(content)
                return resp.status, content
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def unlock(self):
        code, result = self.request("/api/unlock", "POST", {"passphrase": "synthetic-passphrase-0001"}, self.csrf)
        self.assertEqual(200, code)
        return {**self.csrf, "X-TherapyBot-Session": result["session"]}

    def test_ui_and_source_retrieval(self):
        code, page = self.request("/")
        self.assertEqual(200, code)
        self.assertIn(b"TherapyBot", page)
        self.assertNotIn(b"{{CSRF_TOKEN}}", page)
        code, data = self.request("/api/sources")
        self.assertEqual(200, code)
        self.assertGreaterEqual(len(data["sources"]), 12)
        urls = [s["url"] for s in data["sources"]]
        self.assertEqual(len(urls), len(set(urls)))

    def test_record_access_requires_session_and_csrf(self):
        self.assertEqual(403, self.request("/api/history")[0])
        self.assertEqual(403, self.request("/api/journal", "POST", {"text": "CANARY"})[0])
        valid = self.unlock()
        self.assertEqual(403, self.request("/api/search?q=CANARY")[0])
        self.assertEqual(403, self.request("/api/backup", headers={"X-TherapyBot-Session": valid["X-TherapyBot-Session"]})[0])
        self.assertEqual(201, self.request("/api/journal", "POST", {"text": "SYNTHETIC_CANARY_0051", "mood": 4}, valid)[0])
        self.assertEqual(403, self.request("/api/journal", headers={**valid, "X-TherapyBot-Session": "invalid"})[0])
        self.assertEqual(1, len(self.request("/api/search?q=SYNTHETIC_CANARY_0051", headers=valid)[1]["results"]))
        code, backup = self.request("/api/backup", headers=valid)
        self.assertEqual(200, code)
        self.assertNotIn(b"SYNTHETIC_CANARY_0051", backup)
        self.assertEqual(400, self.request("/api/records", "DELETE", headers=valid)[0])
        self.assertEqual(200, self.request("/api/records", "DELETE", headers={**valid, "X-TherapyBot-Confirm": "DELETE"})[0])
        self.assertEqual([], self.request("/api/search?q=CANARY", headers=valid)[1]["results"])

    def test_no_cloud_fallback_and_immediate_gate(self):
        # Exercise the network fallback path only when an experimental reviewer
        # was explicitly injected; normal default mode does not call the model.
        self.server.output_reviewer = lambda **_kwargs: "allow"
        self.assertEqual(503, self.request("/api/chat", "POST", {"message": "Explain behavioral activation"}, self.csrf)[0])
        code, result = self.request("/api/chat", "POST", {"message": "I already swallowed forty tablets to die"}, self.csrf)
        self.assertEqual(200, code)
        self.assertEqual("immediate", result["safety"])
        self.assertEqual("safety", result["mode"])
        self.assertFalse(self.request("/api/status")[1]["ready"])

    def test_locked_save_returns_vault_status_not_invalid_input(self):
        # VaultError is a ValueError subtype; the specialized handler must
        # run first so the UI sees a locked-vault error, not a bad-request one.
        code, result = self.request("/api/chat", "POST", {"message": "Synthetic ordinary question", "save": True}, self.csrf)
        self.assertEqual(423, code)
        self.assertIn("Unlock your vault", result["error"])

    def test_forged_origin_or_host_denied(self):
        self.assertEqual(403, self.request("/api/status", headers={"Host": "attacker.invalid"})[0])
        self.assertEqual(403, self.request("/api/status", headers={"Origin": "https://attacker.invalid"})[0])


class ModelBoundaryTests(unittest.TestCase):
    def test_remote_hosts_and_query_secrets_rejected(self):
        for url in ("https://example.com/v1/chat/completions", "http://192.168.1.10:5001/api/v1/generate", "http://127.0.0.1:5001/api/v1/generate?token=SYNTHETIC_SECRET"):
            with self.subTest(url=url), self.assertRaises(ModelError):
                ModelClient(url)

    def test_mock_kobold_response(self):
        class LocalMock(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers["Content-Length"])
                payload = json.loads(self.rfile.read(length))
                assert "SYSTEM:" in payload["prompt"]
                body = json.dumps({"results": [{"text": "SYNTHETIC_LOCAL_REPLY"}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                return

        server = ThreadingHTTPServer(("127.0.0.1", 0), LocalMock)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            client = ModelClient(f"http://127.0.0.1:{server.server_port}/api/v1/generate")
            self.assertEqual("SYNTHETIC_LOCAL_REPLY", client.generate("Synthetic question"))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)
