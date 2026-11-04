"""Source-contract regressions for the browser-only Council keyboard repair.

These checks are deliberately narrow. Real-browser and screen-reader testing
remain separate acceptance gates.
"""

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EmbeddedAccessibilityContractTests(unittest.TestCase):
    def test_text_inputs_have_visible_three_pixel_keyboard_focus_outline(self):
        css = (ROOT / "embedded" / "style.css").read_text(encoding="utf-8")
        self.assertRegex(css, r"input:focus-visible[^\n]*outline:\s*3px")

    def test_member_removal_restores_focus_after_rerender(self):
        js = (ROOT / "embedded" / "ui.js").read_text(encoding="utf-8")
        handler = js.split("remove.addEventListener('click', () => {", 1)[1].split("});", 1)[0]
        self.assertIn("renderMembers();", handler)
        self.assertRegex(handler, r"\(nextEditAction \|\| manageButton\)\.focus\(\)")


if __name__ == "__main__":
    unittest.main()
