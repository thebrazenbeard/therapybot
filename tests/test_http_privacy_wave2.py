"""Independent loopback HTTP privacy probes using synthetic temporary data.

These tests exercise implementation boundaries, not a security certification.
"""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from therapybot.app import AppServer, create_server
from therapybot.model import ModelClient, ModelError
from therapybot.storage import Vault


class FakeModel:
    """No model request or external socket; deterministic output for persistence tests."""

    url = "http://127.0.0.1:1/api/v1/generate"
    model_name = "synthetic-mock"

    def generate(self, *args, **kwargs):
        return "SYNTHETIC_RESPONSE_NO_CLINICAL_ADVICE"


class HttpPrivacyWave2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="therapybot-http-privacy-")
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "vault.sqlite3"
        self.server = create_server(0, str(self.path))
        self.server.model = FakeModel()
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.csrf = {"X-TherapyBot-Token": self.server.csrf}
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.shutdown)

    def shutdown(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.vault.close()
        self.thread.join(timeout=2)

    def call(self, path, *, method="GET", payload=None, headers=None, raw=None):
        if raw is None and payload is not None:
            raw = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base + path, data=raw, method=method,
            headers={"Content-Type": "application/json", **(headers or {})},
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                body = response.read()
                return response.status, dict(response.headers), self.decode(body, response.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), self.decode(exc.read(), exc.headers)

    @staticmethod
    def decode(raw, headers):
        if headers.get("Content-Type", "").startswith("application/json"):
            return json.loads(raw)
        return raw

    def unlock(self):
        code, _, body = self.call(
            "/api/unlock", method="POST", payload={"passphrase": "SYNTHETIC-LOCAL-ONLY-PASSPHRASE"},
            headers=self.csrf,
        )
        self.assertEqual(200, code)
        return {**self.csrf, "X-TherapyBot-Session": body["session"]}

    def test_loopback_binding_rejects_externally_exposed_address(self):
        separate = Vault(Path(self.tmp.name) / "nonloopback.sqlite3")
        try:
            with self.assertRaises(ValueError):
                AppServer(("0.0.0.0", 0), separate, FakeModel())
        finally:
            separate.close()

    def test_host_origin_and_private_response_headers(self):
        for header in ({"Host": "attacker.example"},
                       {"Origin": "https://attacker.example"},
                       {"Origin": self.base.replace("http:", "https:")}):
            with self.subTest(header=header):
                self.assertEqual(403, self.call("/api/status", headers=header)[0])
        code, headers, page = self.call("/")
        self.assertEqual(200, code)
        self.assertIn(b"TherapyBot", page)
        self.assertEqual("no-store", headers.get("Cache-Control"))
        self.assertEqual("DENY", headers.get("X-Frame-Options"))
        self.assertEqual("nosniff", headers.get("X-Content-Type-Options"))

    def test_reject_mutation_without_process_token(self):
        cases = [
            ("/api/chat", "POST", {"message": "Synthetic ordinary question"}),
            ("/api/unlock", "POST", {"passphrase": "SYNTHETIC-LOCAL-ONLY-PASSPHRASE"}),
            ("/api/journal", "POST", {"text": "SYNTHETIC"}),
            ("/api/records", "DELETE", None),
        ]
        for path, method, payload in cases:
            with self.subTest(path=path):
                self.assertEqual(403, self.call(path, method=method, payload=payload)[0])
                self.assertEqual(
                    403, self.call(path, method=method, payload=payload,
                                   headers={"X-TherapyBot-Token": "bad-token"})[0],
                )

    def test_private_reads_require_valid_vault_session(self):
        for path in ("/api/history", "/api/journal", "/api/search?q=SYNTHETIC", "/api/backup"):
            with self.subTest(path=path):
                self.assertEqual(403, self.call(path, headers=self.csrf)[0])
        session = self.unlock()
        self.assertEqual(403, self.call("/api/history", headers=self.csrf)[0])
        self.assertEqual(403, self.call("/api/history", headers={**session, "X-TherapyBot-Session": "guessed"})[0])
        for path in ("/api/history", "/api/journal", "/api/search?q=SYNTHETIC"):
            with self.subTest(path=path):
                self.assertEqual(200, self.call(path, headers=session)[0])
        # Backup is a GET, but deliberately also requires the process mutation token.
        self.assertEqual(403, self.call("/api/backup", headers={"X-TherapyBot-Session": session["X-TherapyBot-Session"]})[0])
        self.assertEqual(200, self.call("/api/backup", headers=session)[0])

    def test_save_requires_positive_opt_in_and_unlocked_session(self):
        ordinary = {"message": "Explain what values mean in ACT", "save": False}
        self.assertEqual(200, self.call("/api/chat", method="POST", payload=ordinary, headers=self.csrf)[0])
        # Parent integration subsequently repaired the inherited ValueError
        # handler ordering. Locked saving is specifically a 423 denial now.
        self.assertEqual(423, self.call("/api/chat", method="POST", payload={**ordinary, "save": True}, headers=self.csrf)[0])
        valid = self.unlock()
        # Newly unlocked vault does not retroactively persist earlier unsaved chat.
        self.assertEqual([], self.call("/api/history", headers=valid)[2]["messages"])
        self.assertEqual(200, self.call("/api/chat", method="POST", payload=ordinary, headers=self.csrf)[0])
        self.assertEqual([], self.call("/api/history", headers=valid)[2]["messages"])
        self.assertEqual(403, self.call("/api/chat", method="POST", payload={**ordinary, "save": True}, headers=self.csrf)[0])
        self.assertEqual(200, self.call("/api/chat", method="POST", payload={**ordinary, "save": True}, headers=valid)[0])
        self.assertEqual(1, len(self.call("/api/history", headers=valid)[2]["messages"]))

    def test_backup_contains_ciphertext_and_delete_needs_confirmation(self):
        session = self.unlock()
        phrase = "SYNTHETIC_CONFIDENTIAL_CANARY_271828"
        self.assertEqual(201, self.call("/api/journal", method="POST", payload={"text": phrase}, headers=session)[0])
        self.assertNotIn(phrase.encode(), self.path.read_bytes())
        code, _, backup = self.call("/api/backup", headers=session)
        self.assertEqual(200, code)
        self.assertNotIn(phrase.encode(), backup)
        self.assertEqual(400, self.call("/api/records", method="DELETE", headers=session)[0])
        self.assertEqual(403, self.call("/api/records", method="DELETE", headers={**session, "X-TherapyBot-Session": "invalid", "X-TherapyBot-Confirm": "DELETE"})[0])
        self.assertEqual(200, self.call("/api/records", method="DELETE", headers={**session, "X-TherapyBot-Confirm": "DELETE"})[0])
        self.assertEqual([], self.call("/api/journal", headers=session)[2]["entries"])
        # Previously downloaded backup remains; the app cannot delete arbitrary copies.
        self.assertGreater(len(backup), 100)

    def test_second_unlock_rotates_single_process_wide_session(self):
        first = self.unlock()
        second = self.unlock()
        self.assertNotEqual(first["X-TherapyBot-Session"], second["X-TherapyBot-Session"])
        self.assertEqual(403, self.call("/api/history", headers=first)[0])
        self.assertEqual(200, self.call("/api/history", headers=second)[0])

    def test_request_body_size_and_json_type_are_enforced(self):
        self.assertEqual(400, self.call("/api/chat", method="POST", raw=b"{}" * 24_002, headers=self.csrf)[0])
        self.assertEqual(400, self.call("/api/chat", method="POST", raw=b"not-json", headers=self.csrf)[0])
        self.assertEqual(400, self.call("/api/chat", method="POST", payload={"message": "x" * 8001}, headers=self.csrf)[0])
        self.assertEqual(400, self.call("/api/chat", method="POST", raw=b"{}", headers={**self.csrf, "Content-Type": "text/plain"})[0])

    def test_reject_model_urls_that_could_send_private_text_off_host(self):
        for url in (
            "https://example.org/v1/chat/completions",
            "http://192.168.1.20:5001/api/v1/generate",
            "http://127.0.0.1:5001/api/v1/generate?token=SECRET",
            "http://127.0.0.1:5001/v1/chat/completions#fragment",
        ):
            with self.subTest(url=url), self.assertRaises(ModelError):
                ModelClient(url)


if __name__ == "__main__":
    unittest.main()
