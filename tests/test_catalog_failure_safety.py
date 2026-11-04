"""A broken research catalog must never suppress model-independent crisis help."""

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest.mock import patch

from therapybot.app import create_server


class CatalogFailureTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.server = create_server(0, str(Path(self.folder.name) / "synthetic.sqlite3"))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self._close)

    def _close(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.vault.close()
        self.thread.join(timeout=2)
        self.folder.cleanup()

    def _post(self, message):
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.server.server_port}/api/chat",
            data=json.dumps({"message": message, "save": False}).encode(),
            headers={"Content-Type": "application/json", "X-TherapyBot-Token": self.server.csrf},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status, json.load(resp)
        except urllib.error.HTTPError as exc:
            return exc.code, json.load(exc)

    def test_urgent_resources_bypass_malformed_catalog(self):
        with patch("therapybot.app.source_search", side_effect=ValueError("secret-catalog-detail")) as search:
            code, body = self._post("I already swallowed forty tablets to die")
        self.assertEqual(200, code)
        self.assertEqual("immediate", body["safety"])
        self.assertEqual("safety", body["mode"])
        self.assertEqual([], body["citations"])
        search.assert_not_called()

    def test_normal_chat_fails_closed_without_leaking_source_error(self):
        with patch("therapybot.app.source_search", side_effect=ValueError("secret-catalog-detail")):
            code, body = self._post("Explain behavioral activation")
        self.assertEqual(503, code)
        self.assertNotIn("secret-catalog-detail", json.dumps(body))
        self.assertFalse(self.server.model_responded)

    def test_concern_resources_survive_catalog_failure(self):
        with patch("therapybot.app.source_search", side_effect=ValueError("secret-catalog-detail")):
            code, body = self._post("I wish I were dead")
        self.assertEqual(200, code)
        self.assertEqual("concern", body["safety"])
        self.assertEqual("safety", body["mode"])
        self.assertEqual([], body["citations"])
        self.assertFalse(self.server.model_responded)


if __name__ == "__main__":
    unittest.main()
