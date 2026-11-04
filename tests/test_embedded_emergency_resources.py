"""Static emergency contacts must not depend on the unvalidated text router."""

import re
import unittest
from pathlib import Path


EMBEDDED = Path(__file__).resolve().parents[1] / "embedded"


class EmergencyResourcePanelContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = (EMBEDDED / "index.html").read_text(encoding="utf-8")
        cls.css = (EMBEDDED / "style.css").read_text(encoding="utf-8")

    def test_resources_exist_in_server_delivered_html_without_javascript(self):
        self.assertIn('id="immediate-help"', self.html)
        self.assertIn('aria-labelledby="emergency-title"', self.html)
        self.assertIn('id="emergency-title"', self.html)
        self.assertIn('href="#immediate-help"', self.html,
                      "The composer must offer a keyboard-usable route back to help")
        panel = self.html.split('id="immediate-help"', 1)[1].split('</section>', 1)[0]
        self.assertNotIn('<script', panel)
        self.assertNotIn('<form', panel)
        self.assertNotIn(' hidden', panel)
        self.assertNotIn('aria-hidden="true"', panel.split('class="safety-content"', 1)[-1])

    def test_distinct_911_poison_help_and_988_paths_are_readable(self):
        panel = self.html.split('id="immediate-help"', 1)[1].split('</section>', 1)[0]
        self.assertRegex(panel, r'(?s)Medical emergency.{0,250}911')
        self.assertRegex(panel, r'(?s)Possible poisoning.{0,350}1-800-222-1222')
        self.assertRegex(panel, r'(?s)Emotional crisis.{0,300}988')
        self.assertIn('local emergency services', panel)
        self.assertIn('cannot reliably identify emergencies', panel)
        self.assertIn('href="tel:911"', panel)
        self.assertIn('href="tel:18002221222"', panel)
        self.assertIn('href="tel:988"', panel)
        self.assertIn('https://poisonhelp.hrsa.gov/what-you-can-do', panel)
        self.assertIn('https://988lifeline.org/get-help/', panel)

    def test_links_require_a_user_action_and_maintain_focus_visibility(self):
        panel = self.html.split('id="immediate-help"', 1)[1].split('</section>', 1)[0]
        self.assertNotRegex(panel, r'(?i)on(?:click|load|error|submit)\s*=')
        self.assertNotIn('autofocus', panel)
        self.assertIn('rel="noopener noreferrer"', panel)
        self.assertIn('a:focus-visible', self.css)
        self.assertRegex(self.css, r'@media\s*\(max-width:\s*620px\)')
        self.assertIsNone(re.search(r'\b(?:fetch|XMLHttpRequest|sendBeacon)\s*\(', panel))

    def test_emergency_cards_use_three_two_one_columns_at_responsive_breakpoints(self):
        css = self.css
        wide = css.split('@media (max-width: 1080px)', 1)[0]
        tablet = css.split('@media (max-width: 1080px)', 1)[1].split('@media (max-width: 800px)', 1)[0]
        phone = css.split('@media (max-width: 800px)', 1)[1].split('@media (max-width: 620px)', 1)[0]
        self.assertRegex(wide, r'\.emergency-options\s*\{[^}]*grid-template-columns:\s*repeat\(3,\s*minmax\(0,\s*1fr\)\)')
        self.assertRegex(tablet, r'\.emergency-options\s*\{[^}]*grid-template-columns:\s*repeat\(2,\s*minmax\(0,\s*1fr\)\)')
        self.assertRegex(phone, r'\.emergency-options\s*\{[^}]*grid-template-columns:\s*1fr')


if __name__ == "__main__":
    unittest.main()
