"""Independent negative contracts for the experimental offline semantic path.

These tests deliberately check *presentation and provenance*, not clinical
correctness. They do not promote bibliographic pointers into claim support.
"""
from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
OFFLINE = ROOT / "static" / "offline.html"
LOCAL = ROOT / "static" / "index.html"
CORE = ROOT / "static" / "semantic_core.js"


class _OfflineMarkup(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.scripts: list[dict[str, str]] = []
        self.forms: list[dict[str, str]] = []
        self.links: list[dict[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        data = dict(attrs)
        if tag == "script":
            self.scripts.append(data)
        if tag == "form":
            self.forms.append(data)
        if tag == "a":
            self.links.append(data)


class StaticProvenanceContracts(unittest.TestCase):
    def test_offline_page_has_no_remote_script_or_submission_target(self):
        markup = OFFLINE.read_text(encoding="utf-8")
        parsed = _OfflineMarkup()
        parsed.feed(markup)
        self.assertEqual([x.get("src") for x in parsed.scripts if x.get("src")], ["semantic_core.js"])
        self.assertFalse([x for x in parsed.forms if x.get("action")], "Offline page must not submit private text elsewhere")
        self.assertFalse(re.search(r"\b(?:google-analytics|gtag|segment|mixpanel|sentry|cdn\.jsdelivr)\b", markup, re.I))
        self.assertIn('referrer" content="no-referrer', markup)
        self.assertTrue(all(x.get("rel") == "noopener noreferrer" for x in parsed.links if x.get("target") == "_blank"))

    def test_user_input_is_rendered_as_text_not_executable_markup(self):
        for page in (OFFLINE, LOCAL):
            with self.subTest(page=page.name):
                markup = page.read_text(encoding="utf-8")
                self.assertNotRegex(markup, r"\.innerHTML\s*=")
                self.assertIn("textContent", markup)
        core = CORE.read_text(encoding="utf-8")
        self.assertNotIn("eval(", core)
        self.assertNotIn("new Function(", core)

    def test_source_links_must_be_explained_as_related_reading(self):
        """A bibliography is not proof for individualized model responses."""
        for page in (OFFLINE, LOCAL):
            with self.subTest(page=page.name):
                markup = page.read_text(encoding="utf-8")
                self.assertRegex(markup, r"(?i)related reading")
                self.assertRegex(markup, r"(?i)(?:not (?:proof|verification|validate)|does not (?:verify|validate))")


@unittest.skipUnless(shutil.which("node"), "Node needed for emitted-citation contracts")
class ExecutedProvenanceContracts(unittest.TestCase):
    def test_emitted_citations_match_the_repository_register_not_an_llm_claim(self):
        script = """
          const core=require('./static/semantic_core.js');
          const prompts=['My boss at work is demanding money.',
            'My sister and I argued.', 'My childhood trauma is difficult to discuss.',
            'I have anxiety.', 'I feel lonely.', 'I experienced a supernatural vision.',
            'What does consciousness mean?', 'I feel hopeless.', 'I am angry.'];
          const outputs=prompts.map(x=>core.reply(x));
          console.log(JSON.stringify(outputs));
        """
        run = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True,
                             text=True, encoding="utf-8", check=True, timeout=10)
        outputs = json.loads(run.stdout)
        register = {row["id"]: row for row in json.loads(
            (ROOT / "research" / "sources.json").read_text(encoding="utf-8"))}
        self.assertGreater(sum(bool(x.get("citations")) for x in outputs), 5)
        for result in outputs:
            self.assertEqual(result["mode"], "semantic-offline")
            self.assertIn("not verification", result["limitations"].lower())
            for citation in result.get("citations", []):
                with self.subTest(topic=result.get("topic"), id=citation.get("id")):
                    original = register[citation["id"]]
                    self.assertEqual(citation["title"], original["title"])
                    self.assertEqual(citation["url"], original["url"])
                    self.assertEqual(citation["source_type"], original["type"])

    def test_non_english_input_has_an_honest_coverage_boundary(self):
        script = """
          const core=require('./static/semantic_core.js');
          console.log(JSON.stringify(['Me siento muy solo y triste',
             '我感到孤独和悲伤','أنا حزين ووحيد'].map(x=>core.reply(x))));
        """
        run = subprocess.run(["node", "-e", script], cwd=ROOT, capture_output=True,
                             text=True, encoding="utf-8", check=True, timeout=10)
        for result in json.loads(run.stdout):
            self.assertFalse(result.get("citations"), "Unsupported language cannot get spurious references")
            self.assertRegex(result["reply"].lower(), r"(?:english|language|cannot reliably)")


if __name__ == "__main__":
    unittest.main()
