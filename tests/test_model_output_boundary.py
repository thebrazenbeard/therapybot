"""Model-output boundary CHARACTERIZATION, not a passed clinical safety gate.

These tests deliberately confirm that unsafe synthetic model canaries currently
pass through. They must not be construed as successful output moderation.
"""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from therapybot.app import create_server


class UntrustedLocalModel(BaseHTTPRequestHandler):
    def do_POST(self):
        self.server.calls += 1
        count = int(self.headers.get("Content-Length", "0"))
        _ = self.rfile.read(count)
        if self.server.fail:
            self.send_error(500, "synthetic model failure")
            return
        body = json.dumps({"results": [{"text": self.server.reply}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        return


class ModelOutputBoundaryCharacterization(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.model = ThreadingHTTPServer(("127.0.0.1", 0), UntrustedLocalModel)
        self.model.calls = 0
        self.model.fail = False
        self.model.reply = "SYNTHETIC_NEUTRAL_MODEL_REPLY"
        self.model_thread = threading.Thread(target=self.model.serve_forever, daemon=True)
        self.model_thread.start()
        self.server = create_server(
            0,
            str(Path(self.temp.name) / "synthetic-vault.sqlite3"),
            f"http://127.0.0.1:{self.model.server_port}/api/v1/generate",
        )
        self.base = f"http://127.0.0.1:{self.server.server_port}"
        self.csrf = {"X-TherapyBot-Token": self.server.csrf}
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close)

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.vault.close()
        self.thread.join(timeout=2)
        self.model.shutdown()
        self.model.server_close()
        self.model_thread.join(timeout=2)

    def request(self, path, method="GET", data=None, headers=None):
        payload = None if data is None else json.dumps(data).encode("utf-8")
        request = urllib.request.Request(
            self.base + path,
            data=payload,
            headers={"Content-Type": "application/json", **(headers or {})},
            method=method,
        )
        try:
            with urllib.request.urlopen(request, timeout=5) as response:
                return response.status, json.loads(response.read())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read())

    def chat(self, message):
        return self.request("/api/chat", "POST", {"message": message, "save": False}, self.csrf)

    def test_observes_unscreened_concern_reply(self):
        self.model.reply = "SYNTHETIC_FALSE_REASSURANCE_CANARY"
        status, result = self.chat("I sometimes wish I would never wake up.")
        self.assertEqual(200, status)
        self.assertEqual("concern", result["safety"])
        self.assertEqual("model", result["mode"])
        # Known defect: a warning prefix does not inspect the model completion.
        self.assertIn("SYNTHETIC_FALSE_REASSURANCE_CANARY", result["reply"])
        self.assertGreater(self.model.calls, 0)

    def test_observes_unscreened_diagnosis_and_spiritual_causality(self):
        for canary, prompt in (
            ("SYNTHETIC_DIAGNOSTIC_CERTAINTY_CANARY", "What are some possible causes of low motivation?"),
            ("SYNTHETIC_UNVERIFIED_SUPERNATURAL_CAUSE_CANARY", "Could a strange experience have a spiritual interpretation?"),
        ):
            with self.subTest(canary=canary):
                self.model.reply = canary
                status, result = self.chat(prompt)
                self.assertEqual(200, status)
                self.assertEqual("model", result["mode"])
                self.assertEqual(canary, result["reply"])

    def test_observes_unscreened_unsupported_reference(self):
        self.model.reply = "SYNTHETIC_FAKE_CITATION https://example.invalid/no-source"
        status, result = self.chat("Explain behavior and interpersonal patterns")
        self.assertEqual(200, status)
        self.assertIn("https://example.invalid/no-source", result["reply"])
        # The separately retrieved source list is not a verifier of model prose.
        self.assertNotIn("https://example.invalid/no-source", [s["url"] for s in result["citations"]])

    def test_immediate_static_response_does_not_consult_untrusted_model(self):
        self.model.reply = "SHOULD_NOT_BE_RETURNED_CANARY"
        status, result = self.chat("I already swallowed forty tablets to die")
        self.assertEqual(200, status)
        self.assertEqual("safety", result["mode"])
        self.assertEqual("immediate", result["safety"])
        self.assertNotIn("SHOULD_NOT_BE_RETURNED_CANARY", result["reply"])
        self.assertEqual(0, self.model.calls)

    def test_opt_in_storage_remains_off_but_model_status_updates(self):
        status, result = self.chat("What is behavioral activation?")
        self.assertEqual(200, status)
        self.assertEqual("model", result["mode"])
        self.assertFalse(self.server.vault.initialized)
        count = self.server.vault.db.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        self.assertEqual(0, count)
        code, system_status = self.request("/api/status")
        self.assertEqual(200, code)
        self.assertTrue(system_status["endpoint_reachable"])
        self.assertTrue(system_status["ready"])

    def test_model_failure_returns_local_503_without_cloud_fallback(self):
        self.model.fail = True
        status, result = self.chat("Explain behavioral activation")
        self.assertEqual(503, status)
        self.assertIn("no cloud fallback", result["error"].lower())
        self.assertEqual(0, self.server.vault.db.execute("SELECT COUNT(*) FROM records").fetchone()[0])


if __name__ == "__main__":
    unittest.main()
