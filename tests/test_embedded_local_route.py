"""Real loopback probes for the isolated repository-resident Council client.

These test exact asset delivery and HTTP boundaries, not browser behavior,
clinical safety, or the quality of the synthetic Council conversation.
"""

import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from therapybot.app import EMBEDDED, EMBEDDED_ASSETS, create_server


class EmbeddedLocalRouteTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix="therapybot-embedded-route-")
        self.addCleanup(temp.cleanup)
        self.server = create_server(0, str(Path(temp.name) / "synthetic-vault.sqlite3"))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.close_server)
        self.base = f"http://127.0.0.1:{self.server.server_port}"

    def close_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.server.vault.close()
        self.thread.join(timeout=2)

    def get(self, path, *, headers=None):
        req = urllib.request.Request(self.base + path, headers=headers or {})
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.status, response.headers, response.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.headers, exc.read()

    def test_exact_client_assets_are_bundled_and_mime_typed(self):
        self.assertFalse(self.server.vault.initialized)
        self.assertFalse(self.server.vault.unlocked)
        for asset, mime_type in EMBEDDED_ASSETS.items():
            with self.subTest(asset=asset):
                status, headers, raw = self.get("/embedded/" + asset)
                self.assertEqual(200, status)
                self.assertEqual((EMBEDDED / asset).read_bytes(), raw)
                self.assertEqual(mime_type, headers["Content-Type"])
                self.assertEqual("no-store", headers["Cache-Control"])
                self.assertEqual("nosniff", headers["X-Content-Type-Options"])
                self.assertEqual("no-referrer", headers["Referrer-Policy"])
                self.assertEqual("DENY", headers["X-Frame-Options"])
                self.assertNotIn(self.server.csrf.encode("ascii"), raw)
        self.assertFalse(self.server.vault.initialized)
        self.assertFalse(self.server.vault.unlocked)
        self.assertIsNone(self.server.session)

    def test_embedded_home_and_existing_app_are_separate(self):
        alias = self.get("/embedded/")
        self.assertEqual(200, alias[0])
        self.assertEqual((EMBEDDED / "index.html").read_bytes(), alias[2])
        self.assertEqual(alias[2], self.get("/embedded")[2])
        main = self.get("/")
        self.assertEqual(200, main[0])
        self.assertIn(b'href="/embedded/"', main[2])
        self.assertIn(b"{{CSRF_TOKEN}}", (Path(__file__).parents[1] / "static" / "index.html").read_bytes())
        self.assertNotIn(b"{{CSRF_TOKEN}}", main[2])

    def test_embedded_csp_prohibits_external_connections_and_native_form_submission(self):
        _, headers, _ = self.get("/embedded/")
        csp = headers["Content-Security-Policy"]
        self.assertIn("default-src 'none'", csp)
        self.assertIn("connect-src 'none'", csp)
        self.assertIn("form-action 'none'", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("'unsafe-inline'", csp)
        self.assertNotIn("'unsafe-eval'", csp)
        self.assertIn("base-uri 'none'", csp)
        self.assertIn("frame-ancestors 'none'", csp)
        self.assertEqual(1, len(headers.get_all("Content-Security-Policy")))

    def test_host_origin_and_path_allowlist_reject_untrusted_access(self):
        for headers in (
            {"Host": "attacker.invalid"},
            {"Origin": "https://attacker.invalid"},
            {"Origin": self.base.replace("http:", "https:")},
            {"Host": f"localhost:{self.server.server_port}", "Origin": self.base},
        ):
            with self.subTest(headers=headers):
                self.assertEqual(403, self.get("/embedded/engine.js", headers=headers)[0])

        for path in (
            "/embedded/secrets.txt",
            "/embedded/engine.js/extra",
            "/embedded/ENGINE.JS",
            "/embedded/%2e%2e/therapybot/app.py",
            "/embedded/%2fengine.js",
            "/embedded/%00engine.js",
            "/embedded/ui.js?profile=user-data",
            "/embedded/index.html?member-notes=private-data",
            "/embedded/index.html/",
            "/embedded/.git/config",
        ):
            with self.subTest(path=path):
                self.assertEqual(404, self.get(path)[0])


if __name__ == "__main__":
    unittest.main()
