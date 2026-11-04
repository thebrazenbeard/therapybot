"""Local-first integration and privacy invariants, using synthetic records only."""

import http.client
import json
import sqlite3
import tempfile
import threading
import unittest
from types import SimpleNamespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from therapybot.server import create_server
from therapybot.vault import LockedError, Vault, WrongPassphrase


PASS = "test-only-local-passphrase-1234"
SENTINEL = "SYNTHETIC_PRIVATE_JOURNAL_CANARY_91"


class VaultTests(unittest.TestCase):
    def test_atomic_chat_pair_rolls_back_if_second_insert_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Vault(Path(directory) / "atomic.sqlite3")
            vault.unlock(PASS)
            with patch("therapybot.vault.uuid.uuid4", return_value=SimpleNamespace(hex="a" * 32)):
                with self.assertRaises(sqlite3.IntegrityError):
                    vault.add_many([("chat", {"role": "user", "text": SENTINEL}),
                                    ("chat", {"role": "assistant", "text": "synthetic response"})])
            self.assertEqual(vault.list(), [], "The first record must roll back too")
            vault.lock()
    def test_sqlite_connection_is_closed_on_context_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Vault(Path(directory) / "connection.sqlite3")
            with vault._connect() as db:
                self.assertEqual(db.execute("SELECT 1").fetchone()[0], 1)
            with self.assertRaises(sqlite3.ProgrammingError):
                db.execute("SELECT 1")

    def test_records_encrypted_searchable_and_lockable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private.sqlite3"
            vault = Vault(path)
            with self.assertRaises(LockedError):
                vault.export()
            vault.unlock(PASS)
            record_id = vault.add("journal", {"text": SENTINEL, "mood": 4})
            self.assertEqual(vault.list(kind="journal", query="CANARY")[0]["id"], record_id)
            self.assertEqual(vault.export()[0]["data"]["text"], SENTINEL)
            self.assertNotIn(SENTINEL.encode(), path.read_bytes(), "Journal leaked into SQLite plaintext")
            vault.lock()
            with self.assertRaises(LockedError):
                vault.list()
            with self.assertRaises(WrongPassphrase):
                vault.unlock("incorrect-passphrase-12345")
            vault.unlock(PASS)
            self.assertTrue(vault.delete(record_id))
            self.assertEqual(vault.export(), [])


class LocalHttpTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.server = create_server(Path(self.tempdir.name) / "therapy.sqlite3", port=0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.token = self.server.csrf_token

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.tempdir.cleanup()

    def request(self, method, route, payload=None, token=None, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port, timeout=4)
        request_headers = dict(headers or {})
        if token is not None:
            request_headers["X-TherapyBot-Token"] = token
        if payload is not None:
            request_headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode() if payload is not None else None
        connection.request(method, route, body=body, headers=request_headers)
        response = connection.getresponse()
        content = response.read()
        status = response.status
        response_headers = dict(response.getheaders())
        connection.close()
        try:
            data = json.loads(content)
        except ValueError:
            try:
                data = content.decode("utf-8")
            except UnicodeDecodeError:
                data = content
        return status, data, response_headers

    def unlock(self):
        old_token = self.token
        status, data, _ = self.request("POST", "/api/vault", {"passphrase": PASS}, token=self.token)
        self.assertEqual(status, 200, data)
        self.token = data["token"]
        self.assertNotEqual(old_token, self.token)

    def test_html_and_public_sources_without_secret(self):
        status, page, headers = self.request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers["Content-Type"])
        self.assertIn("Content-Security-Policy", headers)
        self.assertNotIn(self.token, page)
        for route in ("/api/status", "/api/sources?q=stress"):
            status, payload, _ = self.request("GET", route)
            self.assertEqual(status, 200, payload)
        self.assertIsInstance(payload["sources"], list)

    def test_sensitive_gets_require_token_even_after_unlock(self):
        self.unlock()
        self.assertEqual(self.request("POST", "/api/journal", {"text": SENTINEL}, token=self.token)[0], 200)
        for route in ("/api/records", "/api/export"):
            self.assertEqual(self.request("GET", route)[0], 403)
            self.assertEqual(self.request("GET", route, token="wrong")[0], 403)
            self.assertEqual(self.request("GET", route, token=self.token)[0], 200)
        self.assertNotIn(SENTINEL.encode(), (Path(self.tempdir.name) / "therapy.sqlite3").read_bytes())

    def test_encrypted_backup_endpoint_requires_token_and_unlocked_vault(self):
        self.assertEqual(self.request("GET", "/api/backup")[0], 403)
        self.assertEqual(self.request("GET", "/api/backup", token=self.token)[0], 423)
        self.unlock()
        self.assertEqual(self.request("POST", "/api/journal", {"text": SENTINEL}, token=self.token)[0], 200)
        self.assertEqual(self.request("GET", "/api/backup", token="incorrect")[0], 403)
        status, backup, headers = self.request("GET", "/api/backup", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(headers["Content-Type"], "application/octet-stream")
        self.assertIsInstance(backup, bytes)
        self.assertNotIn(SENTINEL.encode(), backup)
        from therapybot.backup import MAGIC, restore_backup
        self.assertTrue(backup.startswith(MAGIC))
        destination = Path(self.tempdir.name) / "verified-restoration.sqlite3"
        restore_backup(backup, PASS, destination)
        recovered = Vault(destination)
        recovered.unlock(PASS)
        self.assertEqual(recovered.list()[0]["data"]["text"], SENTINEL)
        recovered.lock()

    def test_cross_origin_host_and_token_rotation(self):
        self.assertEqual(self.request("POST", "/api/vault", {"passphrase": PASS})[0], 403)
        self.assertEqual(self.request("POST", "/api/vault", {"passphrase": PASS}, token=self.token,
                                      headers={"Origin": "https://malicious.example"})[0], 403)
        self.assertEqual(self.request("GET", "/api/status", headers={"Host": "evil.example"})[0], 403)
        prior_token = self.token
        self.unlock()
        self.assertEqual(self.request("GET", "/api/export", token=prior_token)[0], 403)
        status, payload, _ = self.request("POST", "/api/lock", {}, token=self.token)
        self.assertEqual(status, 200)
        self.assertNotEqual(payload["token"], self.token)
        self.assertEqual(self.request("GET", "/api/export", token=self.token)[0], 403)
        self.token = payload["token"]
        self.assertEqual(self.request("GET", "/api/records", token=self.token)[0], 423)

    def test_chat_unconfigured_model_does_not_save(self):
        self.unlock()
        status, payload, _ = self.request("POST", "/api/chat", {"text": "How can I focus today?"}, token=self.token)
        self.assertEqual(status, 503, payload)
        status, payload, _ = self.request("GET", "/api/records", token=self.token)
        self.assertEqual(status, 200)
        self.assertEqual(payload["records"], [])

    def test_urgent_chat_responds_without_recording_by_default(self):
        self.unlock()
        status, payload, _ = self.request("POST", "/api/chat", {"text": "I want to kill myself right now."}, token=self.token)
        self.assertEqual(status, 200, payload)
        self.assertEqual(payload["mode"], "safety")
        self.assertFalse(payload["saved"])
        self.assertEqual(self.request("GET", "/api/records", token=self.token)[1]["records"], [])

        status, payload, _ = self.request("POST", "/api/chat", {
            "text": "I want to kill myself right now.", "save_history": True,
        }, token=self.token)
        self.assertEqual(status, 200, payload)
        self.assertTrue(payload["saved"])
        self.assertEqual(len(self.request("GET", "/api/records", token=self.token)[1]["records"]), 2)

    def test_mock_local_model_conversation_is_opt_in_for_storage(self):
        class FakeLocalModel(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def do_POST(self):
                if self.path != "/v1/chat/completions":
                    self.send_error(404)
                    return
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                assert body["messages"][-1]["role"] == "user"
                response = json.dumps({"choices": [{"message": {
                    "content": "A local answer with [fabricated_citation_000]."
                }}]}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(response)))
                self.end_headers()
                self.wfile.write(response)

        mock = ThreadingHTTPServer(("127.0.0.1", 0), FakeLocalModel)
        thread = threading.Thread(target=mock.serve_forever, daemon=True)
        thread.start()
        try:
            self.server.model_url = f"http://127.0.0.1:{mock.server_port}"
            self.unlock()
            status, payload, _ = self.request("POST", "/api/chat", {
                "text": "What are practical ways to reset a busy afternoon?"
            }, token=self.token)
            self.assertEqual(status, 200, payload)
            self.assertEqual(payload["mode"], "local-model")
            self.assertFalse(payload["saved"])
            self.assertNotIn("[fabricated_citation_000]", payload["reply"])
            self.assertEqual(self.request("GET", "/api/records", token=self.token)[1]["records"], [])

            status, payload, _ = self.request("POST", "/api/chat", {
                "text": "Please save this synthetic conversation.", "save_history": True,
            }, token=self.token)
            self.assertEqual(status, 200, payload)
            self.assertTrue(payload["saved"])
            saved = self.request("GET", "/api/records", token=self.token)[1]["records"]
            self.assertEqual([record["data"]["role"] for record in saved], ["user", "assistant"])
        finally:
            mock.shutdown()
            mock.server_close()
            thread.join(timeout=3)

    def test_nonlocal_model_url_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                create_server(Path(directory) / "a.sqlite3", model_url="https://external.example:443")


if __name__ == "__main__":
    unittest.main()
