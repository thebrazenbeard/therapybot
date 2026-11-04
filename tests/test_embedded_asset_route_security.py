"""Synthetic loopback security probes for the bundled browser model asset.

These verify the HTTP route, not browser execution or clinical behavior.
"""

import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from therapybot.app import STATIC, create_server


class EmbeddedAssetRouteSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="therapybot-asset-route-")
        self.addCleanup(self.temp.cleanup)
        self.server = create_server(0, str(Path(self.temp.name) / "synthetic-vault.sqlite3"))
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

    def test_exact_asset_is_local_bytes_without_token_injection(self):
        status, headers, data = self.get("/semantic_core.js")
        self.assertEqual(200, status)
        self.assertEqual((STATIC / "semantic_core.js").read_bytes(), data)
        self.assertTrue(headers["Content-Type"].startswith("text/javascript"))
        self.assertNotIn(self.server.csrf.encode("ascii"), data)
        self.assertEqual("no-store", headers["Cache-Control"])
        self.assertEqual("nosniff", headers["X-Content-Type-Options"])
        self.assertEqual("no-referrer", headers["Referrer-Policy"])
        self.assertEqual("DENY", headers["X-Frame-Options"])

    def test_asset_uses_narrow_browser_content_security_policy(self):
        status, headers, _ = self.get("/semantic_core.js")
        self.assertEqual(200, status)
        csp = headers["Content-Security-Policy"]
        self.assertIn("default-src 'self'", csp)
        self.assertIn("connect-src 'self'", csp)
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn("'unsafe-eval'", csp)
        self.assertIn("frame-ancestors 'none'", csp)

    def test_asset_access_does_not_bypass_dns_rebinding_checks(self):
        forbidden = (
            {"Host": "attacker.invalid"},
            {"Origin": "https://attacker.invalid"},
            {"Origin": self.base.replace("http:", "https:")},
            {"Host": f"localhost:{self.server.server_port}", "Origin": "http://127.0.0.1:9999"},
        )
        for header in forbidden:
            with self.subTest(header=header):
                self.assertEqual(403, self.get("/semantic_core.js", headers=header)[0])

    def test_only_exact_url_path_can_reach_asset(self):
        denied = (
            "/semantic_core.js/extra",
            "/semantic_core.js%2fextra",
            "/static/semantic_core.js",
            "/semantic_core.js/../index.html",
            "/%2e%2e/semantic_core.js",
            "/SEMANTIC_CORE.JS",
            "/semantic_core.js%00",
            "/does-not-exist.js",
        )
        for path in denied:
            with self.subTest(path=path):
                self.assertEqual(404, self.get(path)[0])

    def test_read_only_asset_has_no_private_session_dependency_or_eager_mutation(self):
        # A visitor can read the same static application code before and after
        # vault unlock. Reading code must not create or unlock private records.
        self.assertFalse(self.server.vault.initialized)
        self.assertFalse(self.server.vault.unlocked)
        first = self.get("/semantic_core.js")
        second = self.get("/semantic_core.js?cache=example")
        self.assertEqual((200, 200), (first[0], second[0]))
        self.assertEqual(first[2], second[2])
        self.assertFalse(self.server.vault.initialized)
        self.assertFalse(self.server.vault.unlocked)
        self.assertIsNone(self.server.session)


if __name__ == "__main__":
    unittest.main()
