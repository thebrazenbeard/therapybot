"""Offline HTML delivery and exact-path local serving checks.

These are source and localhost HTTP contract tests, not clinical validation.
"""

import re
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from therapybot.app import create_server


ROOT = Path(__file__).resolve().parents[1]
OFFLINE = ROOT / "static" / "offline.html"
LOCAL = ROOT / "static" / "index.html"
CORE = ROOT / "static" / "semantic_core.js"


class _Scripts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.srcs = []

    def handle_starttag(self, tag, attrs):
        if tag == "script":
            self.srcs.append(dict(attrs).get("src"))


class EmbeddedOfflineHTMLTests(unittest.TestCase):
    def test_double_clickable_html_uses_only_bundled_script_and_no_network_api(self):
        html = OFFLINE.read_text(encoding="utf-8")
        self.assertTrue(CORE.is_file())
        parsed = _Scripts()
        parsed.feed(html)
        self.assertEqual(["semantic_core.js", None], parsed.srcs)
        self.assertNotRegex(html, r"\bfetch\s*\(|\bXMLHttpRequest\b|\bsendBeacon\s*\(|\blocalStorage\b|\bsessionStorage\b")
        self.assertNotRegex(html, r"<script[^>]*src\s*=\s*['\"]https?://")
        self.assertNotIn("/api/chat", html)
        self.assertIn("core.createSession()", html)
        self.assertIn("session.reply(input,overrides)", html)
        self.assertIn("session.reset()", html)
        self.assertIn("Nothing is uploaded or written to browser storage", html)
        self.assertIn("Why this response?", html)
        self.assertIn("Related reading — not verification of this individual reply:", html)
        self.assertIn("unvalidated guide", html)

    def test_server_ui_preserves_explicit_gguf_and_embedded_modes(self):
        html = LOCAL.read_text(encoding="utf-8")
        self.assertIn('<script src="semantic_core.js"></script>', html)
        self.assertIn('value="embedded" selected', html)
        self.assertIn('value="local-model"', html)
        self.assertIn("embeddedSession.reply(message,overrides)", html)
        self.assertIn("Related reading — not verification of this individual reply:", html)
        self.assertIn("api('/api/chat'", html)
        self.assertIn("$('chat-save').disabled=embedded||!session", html)

    def test_exact_allowlisted_js_asset_served_without_user_data(self):
        with tempfile.TemporaryDirectory() as temp:
            server = create_server(0, str(Path(temp) / "vault.sqlite3"))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                base = f"http://127.0.0.1:{server.server_port}"
                with urllib.request.urlopen(base + "/semantic_core.js", timeout=3) as response:
                    data = response.read()
                    self.assertEqual(200, response.status)
                    self.assertEqual("text/javascript; charset=utf-8", response.headers["Content-Type"])
                    self.assertEqual("nosniff", response.headers["X-Content-Type-Options"])
                    self.assertEqual("no-store", response.headers["Cache-Control"])
                    self.assertIn("script-src 'self'", response.headers["Content-Security-Policy"])
                    self.assertEqual(CORE.read_bytes(), data)
                with self.assertRaises(urllib.error.HTTPError) as denied:
                    urllib.request.urlopen(base + "/static/semantic_core.js", timeout=3)
                self.assertEqual(404, denied.exception.code)
            finally:
                server.shutdown()
                server.server_close()
                server.vault.close()
                thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
