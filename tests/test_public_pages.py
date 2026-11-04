"""Public documentation deployment must never expose the local vault interface."""

from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class _Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(tag)


class PublicPagesTests(unittest.TestCase):
    def test_pages_artifact_excludes_repository_root_and_app_ui(self):
        workflow = (ROOT / ".github/workflows/static.yml").read_text(encoding="utf-8")
        self.assertIn("path: 'pages'", workflow)
        self.assertNotIn("path: '.'", workflow)
        self.assertTrue((ROOT / "pages/index.html").is_file())

    def test_public_page_has_no_private_input_or_api_client(self):
        page = (ROOT / "pages/index.html").read_text(encoding="utf-8")
        parser = _Tags()
        parser.feed(page)
        self.assertFalse(set(parser.tags) & {"form", "input", "textarea", "select", "script"})
        for forbidden in ("{{CSRF_TOKEN}}", "fetch(", "/api/", "localStorage", "sessionStorage"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, page)
        self.assertIn("not TherapyBot itself", page)


if __name__ == "__main__":
    unittest.main()
