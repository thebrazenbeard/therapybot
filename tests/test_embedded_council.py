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
            timeout=8,
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
        self.assertEqual([x["name"] for x in answer["speakers"]], ["Planner", "Rebel"])
        self.assertEqual([x["role"] for x in answer["speakers"]], ["Consequences", "Integrity"])
        self.assertIn("not evidence of separate people or diagnoses", answer["introduction"])
        self.assertIn("different needs", answer["facilitator"])
        self.assertIn("What evidence is missing?", answer["reply"])
        self.assertIn("speaking up", answer["reply"])
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
        self.assertEqual([x["name"] for x in accepted["speakers"]], ["Planner"])
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
        self.assertEqual([x["name"] for x in answer["speakers"]], ["Rebel"])

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
