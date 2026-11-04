"""Fail-closed Council editor controls with JavaScript unavailable.

Source-contract checks supplement, but do not replace, a real browser test.
"""

import unittest
from html.parser import HTMLParser
from pathlib import Path


EMBEDDED = Path(__file__).resolve().parents[1] / "embedded"


class _CouncilEditorMarkup(HTMLParser):
    def __init__(self):
        super().__init__()
        self.elements = {}

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get("id") in {"member-form", "member-name", "member-role", "member-notes", "save-member",
                                    "conversation-form", "message", "style", "depth", "send-message"}:
            self.elements[attributes["id"]] = (tag, attributes)


class CouncilEditorPrivacyContract(unittest.TestCase):
    def test_no_native_member_submission_or_serialized_profile_fields(self):
        parsed = _CouncilEditorMarkup()
        parsed.feed((EMBEDDED / "index.html").read_text(encoding="utf-8"))

        editor_tag, editor_attrs = parsed.elements["member-form"]
        self.assertEqual(editor_tag, "div", "Member editor must be inert when JavaScript does not load")
        self.assertEqual(editor_attrs.get("role"), "group")
        self.assertEqual(parsed.elements["save-member"][1].get("type"), "button")
        for field_id in ("member-name", "member-role", "member-notes"):
            self.assertNotIn("name", parsed.elements[field_id][1],
                             f"{field_id} must not serialize private notes into a native form request")

    def test_member_button_remains_javascript_driven(self):
        ui = (EMBEDDED / "ui.js").read_text(encoding="utf-8")
        self.assertIn("saveMemberButton.addEventListener('click'", ui)

    def test_conversation_cannot_natively_submit_private_text_without_javascript(self):
        parsed = _CouncilEditorMarkup()
        parsed.feed((EMBEDDED / "index.html").read_text(encoding="utf-8"))
        tag, attrs = parsed.elements["conversation-form"]
        self.assertEqual((tag, attrs.get("role")), ("div", "group"))
        self.assertEqual(parsed.elements["send-message"][1].get("type"), "button")
        for field_id in ("message", "style", "depth"):
            self.assertNotIn("name", parsed.elements[field_id][1])
        ui = (EMBEDDED / "ui.js").read_text(encoding="utf-8")
        self.assertNotIn("requestSubmit", ui)
        self.assertIn("sendButton.addEventListener('click', sendMessage)", ui)


if __name__ == "__main__":
    unittest.main()
