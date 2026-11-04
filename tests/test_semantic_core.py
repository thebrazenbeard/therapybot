"""Bounded tests for the browser-embedded, explicitly non-neural semantic map.

Node is optional for the Python app, so these tests skip when it is unavailable.
The checks do not qualify the engine for clinical use.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "static" / "semantic_core.js"


@unittest.skipUnless(shutil.which("node"), "Node.js needed to execute browser-JS tests")
class EmbeddedSemanticCoreTests(unittest.TestCase):
    def run_js(self, script: str) -> object:
        output = subprocess.run(
            ["node", "-e", "const core=require('./static/semantic_core.js');" + script],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        return json.loads(output.stdout)

    def test_standalone_response_and_topic_continuity(self):
        result = self.run_js("""
            const session=core.createSession();
            const first=session.reply('My employer wants my money for work supplies.');
            const second=session.reply('What should I do?');
            console.log(JSON.stringify({first,second,context:session.context()}));
        """)
        self.assertEqual(result["first"]["topic"], "work")
        self.assertEqual(result["second"]["topic"], "work")
        self.assertEqual(result["second"]["mode"], "semantic-offline")
        self.assertNotIn("My employer", str(result["context"]))

    def test_explicit_preference_correction_overrides_earlier_turn(self):
        result = self.run_js("""
            const session=core.createSession();
            const first=session.reply('I prefer direct answers.');
            const second=session.reply('Actually, I prefer gentle responses.');
            const before=session.context();
            session.clear();
            console.log(JSON.stringify({first,second,before,after:session.context()}));
        """)
        self.assertEqual(result["first"]["kind"], "preference")
        self.assertEqual(result["second"]["kind"], "preference")
        self.assertEqual(result["before"]["preferences"], {"style": "gentle"})
        self.assertEqual(result["after"]["preferences"], {})
        self.assertIsNone(result["after"]["topic"])

    def test_multi_turn_person_reference_is_corrected_not_reinvented(self):
        result = self.run_js("""
            const session=core.createSession();
            const first=session.reply('My mother and I argued today');
            const second=session.reply('I said my sister, not my mother');
            const third=session.reply('What should I do about that?');
            console.log(JSON.stringify({first,second,third,context:session.context()}));
        """)
        self.assertEqual(result["first"]["topic"], "relationships")
        self.assertEqual(result["second"]["kind"], "correction")
        self.assertIn("your sister", result["second"]["reply"])
        self.assertEqual(result["third"]["topic"], "relationships")
        self.assertEqual(result["context"]["referent"], "sister")

    def test_source_provenance_agrees_with_research_register(self):
        embedded = self.run_js("console.log(JSON.stringify(core.sources()));")
        registered = {item["id"]: item for item in json.loads((ROOT / "research" / "sources.json").read_text(encoding="utf-8"))}
        self.assertGreaterEqual(len(embedded), 10)
        for entry in embedded:
            self.assertIn(entry["id"], registered)
            self.assertEqual(entry["title"], registered[entry["id"]]["title"])
            self.assertEqual(entry["url"], registered[entry["id"]]["url"])
            self.assertEqual(entry["source_type"], registered[entry["id"]]["type"])

    def test_crisis_disclosure_is_not_equated_with_hypothetical(self):
        results = self.run_js("""
            const lines=['I am going to kill myself tonight',
              'Hypothetically, what if I am going to kill myself?',
              'I am not going to kill myself',
              'Last year I said I am going to kill myself',
              'I feel hopeless about work, but I am discussing it philosophically'];
            console.log(JSON.stringify(lines.map(x=>core.reply(x).kind)));
        """)
        self.assertEqual(results[0], "crisis")
        self.assertTrue(all(kind != "crisis" for kind in results[1:]))

    def test_unusual_experiences_not_confirmed_or_reflexively_diagnosed(self):
        response = self.run_js("console.log(JSON.stringify(core.reply('I experienced a supernatural vision')));")
        self.assertEqual(response["topic"], "unusual")
        self.assertIn("without claiming to know its cause", response["reply"])
        self.assertNotIn("you have psychosis", response["reply"].lower())

    def test_safety_state_survives_followup_without_inventing_a_score(self):
        results = self.run_js("""
            const self=core.createSession();
            const other=core.createSession();
            const first=self.reply('I may hurt myself tonight');
            const follow=self.reply('I am alone and need help waiting');
            const violence=other.reply('I may hit someone tonight');
            const followViolence=other.reply('They are coming soon');
            console.log(JSON.stringify({first,follow,violence,followViolence}));
        """)
        for key in ("first", "follow", "violence", "followViolence"):
            self.assertEqual(results[key]["kind"], "crisis")
        self.assertIn("real-world support", results["follow"]["reply"])
        self.assertIn("create distance", results["followViolence"]["reply"])

    def test_passive_concern_is_not_assumed_to_be_current_intent(self):
        result = self.run_js("""
            const s=core.createSession();
            const first=s.reply("I wish I wouldn't have to wake up");
            const next=s.reply('I feel alone tonight');
            console.log(JSON.stringify({first,next}));
        """)
        self.assertEqual(result["first"]["kind"], "concern")
        self.assertEqual(result["next"]["kind"], "concern")
        self.assertIn("not assuming", result["next"]["reply"].lower())

    def test_medication_and_dependency_boundaries_with_context(self):
        result = self.run_js("""
            const s=core.createSession();
            const med=s.reply('This antidepressant makes me tired');
            const next=s.reply('Can I stop it now?');
            const dep=core.reply('Promise you will always be here for me and I never need another person');
            console.log(JSON.stringify({med,next,dep}));
        """)
        self.assertEqual(result["med"]["kind"], "medication_boundary")
        self.assertEqual(result["next"]["kind"], "medication_boundary")
        self.assertIn("prescribing clinician", result["next"]["reply"])
        self.assertEqual(result["dep"]["kind"], "boundary")
        self.assertIn("cannot promise", result["dep"]["reply"])

    def test_fiction_and_spanish_are_not_auto_escalated(self):
        result = self.run_js("""
            const s=core.createSession();
            const fiction=s.reply('In my novel a character says I might hurt myself tonight');
            const follow=s.reply('What should happen in the next scene?');
            const spanish=core.reply('Me siento solo. ¿Puedes responder en español?');
            console.log(JSON.stringify({fiction,follow,spanish}));
        """)
        self.assertEqual(result["fiction"]["kind"], "creative")
        self.assertEqual(result["follow"]["kind"], "creative")
        self.assertEqual(result["spanish"]["kind"], "language_limit")
        self.assertIn("mi comprensión es limitada", result["spanish"]["reply"])

    def test_indirect_disclosure_and_third_party_safety_categories_are_not_ignored(self):
        result = self.run_js("""
            const inputs=['I am going to end it all tonight and have a plan',
              'I swallowed a handful of tablets just now',
              'My brother is going to kill himself tonight',
              'I want to hurt my partner tonight',
              'I am writing a screenplay where a character wants to hurt my partner'];
            console.log(JSON.stringify(inputs.map(x=>core.reply(x))));
        """)
        self.assertEqual([x["kind"] for x in result[:4]], ["crisis"] * 4)
        self.assertEqual(result[2]["topic"], "third_party_safety")
        self.assertEqual(result[-1]["kind"], "creative")

    def test_historical_theology_is_not_suggested_to_be_personal_psychosis(self):
        result = self.run_js("console.log(JSON.stringify(core.reply('I am studying demons in medieval theology')));")
        self.assertEqual(result["topic"], "philosophy")
        self.assertEqual(result["kind"], "reference")
        self.assertNotIn("psychosis", result["reply"].lower())

    def test_unrecognized_language_cannot_falsely_claim_comprehension(self):
        results = self.run_js("""
            console.log(JSON.stringify([
              core.reply('我感到很孤独，谁能理解我？'),
              core.reply('أشعر بالوحدة ولا أعرف ماذا أفعل'),
              core.reply('Estoy preocupado y no puedo dormir')
            ]));
        """)
        for result in results:
            self.assertEqual(result["kind"], "language_limit")
            self.assertEqual(result["citations"], [])
            self.assertIn("language", result["reply"].lower())
        self.assertIn("cannot reliably interpret", results[0]["reply"])
        self.assertIn("cannot reliably interpret", results[1]["reply"])
        self.assertIn("limitada", results[2]["reply"])

    def test_no_network_or_local_storage_access_even_with_dangerous_input(self):
        output = subprocess.run(
            ["node", "-e", """
              const vm=require('vm');const fs=require('fs');
              const code=fs.readFileSync('static/semantic_core.js','utf8');
              let calls=0;const forbidden=()=>{calls++;throw Error('network/storage attempted')};
              const context={fetch:forbidden,WebSocket:forbidden,XMLHttpRequest:forbidden,
                localStorage:{getItem:forbidden,setItem:forbidden},sessionStorage:{getItem:forbidden,setItem:forbidden}};
              context.window=context;
              vm.runInNewContext(code,context,{timeout:2000});
              const s=context.TherapyBotSemanticCore.createSession();
              s.reply('<script>fetch(\"https://example.com\")</script>');
              s.reply('I prefer direct answers');
              s.reply('Actually, I prefer gentle responses');
              console.log(JSON.stringify({calls,version:context.TherapyBotSemanticCore.version}));
            """],
            cwd=ROOT, capture_output=True, text=True, timeout=10, check=True,
        )
        result = json.loads(output.stdout)
        self.assertEqual(result["calls"], 0)
        self.assertEqual(result["version"], "0.1.0-experimental")


if __name__ == "__main__":
    unittest.main()
