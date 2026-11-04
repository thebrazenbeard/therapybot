"""Static accessibility and privacy contract for the actual local UI.

These checks are source-level guards, not automated assistive-technology or
browser validation. They intentionally do not inspect the public Pages preview.
"""

import unittest
from html.parser import HTMLParser
from pathlib import Path


PAGE = Path(__file__).resolve().parents[1] / "static" / "index.html"


class _Structure(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = []

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class LocalHTMLContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = PAGE.read_text(encoding="utf-8")
        parser = _Structure()
        parser.feed(cls.html)
        cls.elements = parser.elements

    def test_navigation_exposes_active_view(self):
        controls = [(tag, attrs) for tag, attrs in self.elements if attrs.get("data-tab")]
        self.assertEqual(5, len(controls))
        self.assertEqual(1, sum(attrs.get("aria-current") == "page" for _, attrs in controls))
        for tag, attrs in controls:
            self.assertEqual("button", tag)
            self.assertEqual("view-" + attrs["data-tab"], attrs.get("aria-controls"))
        self.assertIn("removeAttribute('aria-current')", self.html)
        self.assertIn("$('page-title').focus()", self.html)

    def test_immediate_help_stays_outside_hidden_tab_panels(self):
        start = self.html.index('aria-label="Immediate help resources"')
        first_view = self.html.index('id="view-talk"')
        self.assertLess(start, first_view)
        self.assertIn('href="https://988lifeline.org/get-help/"', self.html)
        self.assertIn("local emergency services", self.html)
        self.assertNotIn(".side-note{display:none}", self.html)

    def test_chat_can_stay_unsaved_without_unlocking(self):
        self.assertIn('id="chat-save" aria-describedby="chat-save-help"', self.html)
        self.assertIn("privateAccess:save", self.html)
        self.assertIn("if(save&&!session)", self.html)
        self.assertIn("Unsaved conversation works without a vault", self.html)

    def test_status_and_log_have_accessible_labels(self):
        elements = {a.get("id"): a for _, a in self.elements if a.get("id")}
        self.assertEqual("status", elements["model-badge"].get("role"))
        self.assertEqual("status", elements["vault-badge"].get("role"))
        self.assertEqual("log", elements["conversation"].get("role"))
        self.assertTrue(elements["conversation"].get("aria-label"))
        self.assertEqual("-1", elements["page-title"].get("tabindex"))

    def test_narrow_layout_does_not_hide_help_or_lock(self):
        self.assertIn("@media(max-width:480px)", self.html)
        self.assertIn(".side-note{display:block", self.html)
        self.assertIn('id="lock-button"', self.html)
        self.assertIn('id="backup-button"', self.html)


if __name__ == "__main__":
    unittest.main()
