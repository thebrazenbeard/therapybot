"""Guard the public Pages preview from accidental private-API publication.

These tests cover the repository's publication boundary, not what GitHub Pages
actually serves; verify the deployed artifact separately after a push.
"""

import re
import unittest
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class _PageStructure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag.lower(), dict(attrs)))


class PublicPagesBoundaryTests(unittest.TestCase):
    def test_workflow_only_uploads_public_site(self):
        workflow = (ROOT / ".github/workflows/static.yml").read_text(encoding="utf-8")
        self.assertRegex(workflow, r"(?m)^\s*path:\s*['\"]?pages['\"]?\s*$")
        self.assertNotRegex(workflow, r"(?m)^\s*path:\s*['\"]?\.[/'\"]?\s*$")

    def test_public_preview_has_no_sensitive_input_or_api_calls(self):
        html = (ROOT / "pages/interface-preview.html").read_text(encoding="utf-8")
        page = _PageStructure()
        page.feed(html)
        tags = {tag for tag, _ in page.elements}
        self.assertTrue({"html", "main", "title"}.issubset(tags))
        self.assertFalse(tags & {"form", "input", "textarea", "script", "iframe"})
        self.assertFalse(re.search(r"fetch\s*\(|XMLHttpRequest|/api/(?:chat|unlock|records)", html, re.I))
        self.assertRegex(html.lower(), r"local")
        self.assertRegex(html.lower(), r"preview")
        links = [attrs.get("href", "") for tag, attrs in page.elements if tag == "link"]
        self.assertIn("interface-preview.css", links)

    def test_public_preview_assets_are_local_and_no_scripts(self):
        stylesheet = (ROOT / "pages/interface-preview.css").read_text(encoding="utf-8")
        self.assertNotRegex(stylesheet, r"(?i)@import|url\s*\(\s*['\"]?https?://")
        self.assertTrue((ROOT / "static/index.html").is_file())


if __name__ == "__main__":
    unittest.main()
