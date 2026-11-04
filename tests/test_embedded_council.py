"""Developer-only contract tests for the voluntary, user-authored Council.

These synthetic Node VM probes check behavior and side-effect boundaries. They
do not establish clinical safety, validity, or real browser accessibility.
"""

import json
import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EMBEDDED = ROOT / "embedded"
# Windows CI can spend several seconds starting Node under a cold runner.
# Keep a finite outer timeout; each VM script also has its own 1.5s bound.
NODE_SUBPROCESS_TIMEOUT_SECONDS = 30

NODE_PROBE = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const requests = JSON.parse(fs.readFileSync(0, 'utf8'));
const forbiddenCalls = [];
const forbid = name => () => {
  forbiddenCalls.push(name);
  throw new Error('Forbidden external effect: ' + name);
};
const blocked = {
  fetch: forbid('fetch'),
  XMLHttpRequest: forbid('XMLHttpRequest'),
  WebSocket: forbid('WebSocket'),
  localStorage: { getItem: forbid('localStorage.getItem'), setItem: forbid('localStorage.setItem') },
  sessionStorage: { getItem: forbid('sessionStorage.getItem'), setItem: forbid('sessionStorage.setItem') },
  indexedDB: { open: forbid('indexedDB.open') },
  navigator: { sendBeacon: forbid('navigator.sendBeacon') }
};
const window = { ...blocked };
const context = vm.createContext({window, ...blocked});
for (const script of process.argv.slice(1)) {
  vm.runInContext(fs.readFileSync(script, 'utf8'), context, { filename: script, timeout: 1500 });
}
if (typeof window.TherapyBotCouncil?.respond !== 'function') throw new Error('Council engine missing');
const responses = requests.map(request => window.TherapyBotCouncil.respond(request));
console.log(JSON.stringify({ responses, forbiddenCalls }));
"""

MEMBERS = [
    {"id": "planner", "name": "Planner", "role": "Consequences",
     "focus": "feasible options", "question": "What evidence is missing?"},
    {"id": "rebel", "name": "Rebel", "role": "Integrity",
     "notes": "speaking up when a boundary is crossed"},
]


@unittest.skipUnless(shutil.which("node"), "Node.js required")
class CouncilContract(unittest.TestCase):
    def probe(self, *requests):
        completed = subprocess.run(
            [
                shutil.which("node"), "-e", NODE_PROBE,
                str(EMBEDDED / "engine.js"), str(EMBEDDED / "council.js")
            ],
            input=json.dumps(list(requests)),
            text=True,
            encoding="utf-8",
            capture_output=True,
            cwd=ROOT,
            timeout=NODE_SUBPROCESS_TIMEOUT_SECONDS,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(result["forbiddenCalls"], [])
        self.assertEqual(len(result["responses"]), len(requests))
        return result["responses"]

    def test_normal_chat_preserves_base_engine_and_does_not_add_persona(self):
        answer = self.probe({"message": "I am angry about my work schedule.", "members": MEMBERS})[0]
        self.assertEqual(answer["engine"], "embedded-semantic")
        self.assertEqual(answer["state"]["topic"], "work")
        self.assertNotIn("speakers", answer)
        self.assertNotIn("Inner Council", answer["reply"])

    def test_no_default_parts_or_user_history_assumptions(self):
        answer = self.probe({"message": "Council: Tell me what the group thinks."})[0]
        self.assertEqual(answer["state"]["councilMode"], "council")
        self.assertIn("no Inner Council configured", answer["reply"])
        self.assertEqual(answer["speakers"], [])
        self.assertNotIn("Patrick", answer["reply"])
        self.assertNotIn("Strategist", answer["reply"])

    def test_two_custom_members_and_transparent_facilitator(self):
        answer = self.probe({
            "message": "Council: Should I confront my supervisor?",
            "members": MEMBERS,
        })[0]
        self.assertEqual(answer["state"]["councilMode"], "council")
        self.assertEqual([x["name"] for x in answer["speakers"]], ["Perspective 1", "Perspective 2"])
        self.assertEqual([x["role"] for x in answer["speakers"]], ["Practical lens", "Values lens"])
        self.assertIn("not evidence of separate people or diagnoses", answer["introduction"])
        self.assertIn("different needs", answer["facilitator"])
        self.assertIn("reversible next step", answer["reply"])
        self.assertIn("your priorities", answer["reply"])
        self.assertNotIn("What evidence is missing?", answer["reply"])
        self.assertNotIn("speaking up when a boundary is crossed", answer["reply"])
        self.assertEqual(answer["safety"], {"route": "normal", "coverage": "unvalidated"})

    def test_ui_button_mode_without_typed_prefix(self):
        answer = self.probe({"message": "What if I set a boundary?", "mode": "council", "members": MEMBERS})[0]
        self.assertEqual(answer["state"]["councilMode"], "council")
        self.assertEqual(len(answer["speakers"]), 2)

    def test_solo_exact_member_and_unknown_member_rejected(self):
        accepted, rejected = self.probe(
            {"message": "Solo Planner: Consider my options.", "members": MEMBERS},
            {"message": "Solo Imaginary Friend: Consider my options.", "members": MEMBERS}
        )
        self.assertEqual([x["name"] for x in accepted["speakers"]], ["Perspective 1"])
        self.assertNotIn("Rebel", accepted["reply"])
        self.assertIn("user-defined lens", accepted["reply"])
        self.assertIn("What, if anything", accepted["facilitator"])
        self.assertEqual(rejected["speakers"], [])
        self.assertIn("will not invent", rejected["reply"])

    def test_solo_button_select_by_id(self):
        answer = self.probe({
            "message": "Please offer that perspective.",
            "mode": "solo",
            "memberId": "rebel",
            "members": MEMBERS,
        })[0]
        self.assertEqual([x["name"] for x in answer["speakers"]], ["Perspective 2"])

    def test_integration_preserves_user_decision_and_no_consensus_claim(self):
        answer = self.probe({
            "message": "Integrate: Should I speak up?",
            "members": MEMBERS,
        })[0]
        self.assertEqual(answer["state"]["councilMode"], "integration")
        self.assertIn("not a verdict", answer["reply"])
        self.assertIn("remains yours", answer["reply"])
        self.assertEqual(answer["speakers"], [])

    def test_containment_pauses_simulation(self):
        answer = self.probe({"message": "Containment:", "members": MEMBERS})[0]
        self.assertEqual(answer["state"]["councilMode"], "containment")
        self.assertIn("Council is paused", answer["reply"])
        self.assertEqual(answer["speakers"], [])
        self.assertNotIn("Planner:", answer["reply"])

    def test_base_safety_result_vetoes_member_simulation(self):
        answer = self.probe({
            "message": "Council: I swallowed 40 painkillers just now.",
            "members": MEMBERS,
        })[0]
        self.assertNotEqual(answer["safety"]["route"], "normal")
        self.assertNotIn("speakers", answer)
        self.assertNotIn("Planner:", answer["reply"])

    def test_precomputed_risk_result_also_vetoes(self):
        base = {
            "reply": "The base engine raised a caution.",
            "engine": "embedded-semantic",
            "safety": {"route": "concern", "coverage": "unvalidated"},
            "state": {"topic": None},
        }
        answer = self.probe({"message": "Council: What now?", "members": MEMBERS, "baseResult": base})[0]
        self.assertEqual(answer, base)

    def test_forged_normal_base_result_cannot_disable_actual_danger_route(self):
        fake_base = {
            "reply": "No risk detected.",
            "engine": "embedded-semantic",
            "safety": {"route": "normal", "coverage": "unvalidated"},
            "state": {"topic": None},
        }
        answer = self.probe({
            "message": "Council: I am going to kill myself tonight.",
            "members": MEMBERS,
            "baseResult": fake_base,
        })[0]
        self.assertNotEqual(answer["safety"]["route"], "normal")
        self.assertNotIn("speakers", answer)

    def test_member_profile_harm_directive_is_not_spoken_as_a_council_voice(self):
        answer = self.probe({
            "message": "Council: Help me reflect on an ordinary choice.",
            "members": [{"id": "x", "name": "Shadow", "role": "Reflection", "notes": "I should hurt people who disappoint me"}],
        })[0]
        self.assertNotEqual(answer["safety"]["route"], "normal")
        self.assertNotIn("speakers", answer)

    def test_coercive_user_authored_role_never_becomes_council_voice(self):
        role = "Lock my partner in a room until they obey"
        answer = self.probe({
            "message": "Council: What should I do in this relationship?",
            "members": [{"id": "force", "name": "Forceful", "role": role}],
        })[0]
        self.assertNotIn(role, answer["reply"])
        self.assertNotEqual(answer["safety"]["route"], "normal")

    def test_untrusted_role_note_focus_and_question_never_enter_generated_voice_verbatim(self):
        members = [{
            "id": "outsider", "name": "My Lens",
            "role": "Control their finances without permission",
            "notes": "Isolate the dissenters until they relent",
            "focus": "Coerce a relative to accept it",
            "question": "How can I threaten them into compliance?",
        }]
        answer = self.probe({"message": "Council: Should I change my plans?", "members": members})[0]
        for value in members[0].values():
            if value not in ("outsider", "My Lens"):
                self.assertNotIn(value, answer["reply"])
        self.assertTrue(answer["safety"]["route"] in ("normal", "concern"))
        if answer["safety"]["route"] == "normal":
            self.assertTrue(all(x["role"].endswith(" lens") for x in answer["speakers"]))

    def test_benign_creative_roles_keep_member_selection_but_use_generated_speaker_labels(self):
        members = [
            {"id": "skeptic", "name": "Inquirer", "role": "Skeptic", "notes": "Question my assumptions"},
            {"id": "mentor", "name": "North Star", "role": "Wise mentor", "notes": "Personal meaning"},
        ]
        answer = self.probe({"message": "Council: Is there another option?", "members": members})[0]
        self.assertEqual([x["name"] for x in answer["speakers"]], ["Perspective 1", "Perspective 2"])
        self.assertEqual([x["role"] for x in answer["speakers"]], ["Evidence lens", "Values lens"])
        self.assertNotIn("Question my assumptions", answer["reply"])
        self.assertNotIn("Personal meaning", answer["reply"])

    def test_hostile_member_names_cannot_be_laundered_as_speaker_in_any_mode(self):
        for name in (
            "Kill yourself",
            "You must punish her",
            "Lock your partner away until obedient",
        ):
            member = {"id": "m", "name": name, "role": "Skeptic"}
            responses = self.probe(
                {"message": "Council: What options do I have?", "members": [member]},
                {"message": "Solo m: What options do I have?", "members": [member]},
                {"message": "Integrate: What options do I have?", "members": [member]},
            )
            for answer in responses:
                self.assertNotIn(name, answer["reply"])
                for speaker in answer.get("speakers", []):
                    self.assertNotIn(name, speaker["name"])
                    self.assertNotIn(name, speaker["text"])
            self.assertEqual(responses[0]["speakers"][0]["name"], "Perspective 1")

    def test_council_solo_and_integration_do_not_launder_arbitrary_profile_directives(self):
        # Raw profile strings must not become the resident model's voice,
        # even if the incomplete unsafe-roster heuristics miss their meaning.
        hostile_profiles = [
            "Manufacture a false accusation to win an argument",
            "Gaslight my family until they doubt their memory",
            "Impersonate an expert to pressure the client",
            "Steal private financial records for leverage",
            "Manipulate someone until they have no friends",
        ]
        cases = []
        for i, phrase in enumerate(hostile_profiles):
            member = {"id": f"probe{i}", "name": f"Voice {i}", "role": "Reflection",
                      "focus": phrase, "notes": phrase, "question": phrase}
            for message in ("Council: Review this choice.", "Solo Voice 0: Review this choice.",
                            "Integrate: Review this choice."):
                cases.append((phrase, {"message": message.replace("Voice 0", f"Voice {i}"), "members": [member]}))
        answers = self.probe(*(case[1] for case in cases))
        for (phrase, _), answer in zip(cases, answers):
            self.assertNotIn(phrase, answer["reply"])
            for speaker in answer.get("speakers", []):
                self.assertNotIn(phrase, speaker["role"])
                self.assertNotIn(phrase, speaker["text"])

    def test_missing_safety_engine_fails_closed(self):
        answer = self.probe({"message": "Council: What now?", "members": MEMBERS,
                             "baseResult": {"reply": "I am definitely fine"}})[0]
        self.assertEqual(answer["safety"]["route"], "unknown")
        self.assertNotIn("speakers", answer)

    def test_deduplicated_members_and_bounded_roundtable(self):
        members = MEMBERS + [MEMBERS[0]] + [
            {"id": f"extra-{i}", "name": f"Extra {i}", "role": "Reflection"} for i in range(40)
        ]
        answer = self.probe({"message": "Council:", "members": members})[0]
        self.assertEqual(answer["state"]["availableMembers"], 31)
        self.assertEqual(len(answer["speakers"]), 4)
        self.assertEqual(len({x["name"] for x in answer["speakers"]}), 4)
        self.assertIn("first 4", answer["introduction"])

    def test_member_data_are_plain_text_not_html_or_executable(self):
        members = [
            {"id": "x", "name": "Helper", "role": "<script>alert(1)</script>",
             "notes": "<img src=x onerror=alert(1)>"},
            {"id": "y", "name": "<img src=x onerror=alert(1)>",
             "role": "invalid name"},
        ]
        answer = self.probe({"message": "Council: test", "members": members})[0]
        self.assertEqual(len(answer["speakers"]), 1)
        self.assertNotIn("<", answer["reply"])
        self.assertNotIn(">", answer["reply"])

    def test_calls_do_not_remember_prior_user_members(self):
        first, second = self.probe(
            {"message": "Council:", "members": MEMBERS},
            {"message": "Council:"}
        )
        self.assertEqual(len(first["speakers"]), 2)
        self.assertEqual(second["speakers"], [])
        self.assertIn("no Inner Council configured", second["reply"])


if __name__ == "__main__":
    unittest.main()
