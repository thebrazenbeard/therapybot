"""Static accessibility contracts for the local-only HTML interface.

These checks supplement, rather than replace, keyboard and screen-reader trials.
"""

from html.parser import HTMLParser
from pathlib import Path
import json
import shutil
import subprocess
import unittest


HTML = (Path(__file__).resolve().parents[1] / "static" / "index.html").read_text(encoding="utf-8")


class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.items = []

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


class HtmlAccessibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        parser = Elements()
        parser.feed(HTML)
        cls.items = parser.items

    def element(self, id_):
        matches = [(tag, attrs) for tag, attrs in self.items if attrs.get("id") == id_]
        self.assertEqual(len(matches), 1, f"expected one element with id={id_}")
        return matches[0]

    def test_keyboard_skip_link_targets_main(self):
        _, main = self.element("main-content")
        self.assertEqual(main.get("tabindex"), "-1")
        skip = [attrs for tag, attrs in self.items if tag == "a" and attrs.get("href") == "#main-content"]
        self.assertEqual(len(skip), 1)
        self.assertIn("skip-link", skip[0].get("class", ""))

    def test_vault_lock_accessible_from_every_view_and_viewport(self):
        _, lock = self.element("header-lock-button")
        self.assertEqual(lock.get("type"), "button")
        self.assertIn("hidden", lock)
        self.assertIn("$('header-lock-button').hidden=!session", HTML)
        self.assertIn("$('header-lock-button').addEventListener('click',lockVault)", HTML)
        self.assertNotIn(".badges{display:none", HTML)

    def test_quiet_safety_resource_is_always_accessible(self):
        tag, resources = self.element("safety-resources")
        self.assertEqual(tag, "aside")
        self.assertIn("Safety", resources.get("aria-label", ""))
        self.assertIn('href="tel:988"', HTML)
        self.assertIn("U.S. only", HTML)
        self.assertNotIn("#safety-resources{display:none", HTML)

    def test_navigation_exposes_current_section(self):
        buttons = [attrs for tag, attrs in self.items if tag == "button" and "data-tab" in attrs]
        self.assertEqual(len(buttons), 5)
        self.assertEqual(sum(attrs.get("aria-current") == "page" for attrs in buttons), 1)
        for button in buttons:
            self.assertEqual(button.get("aria-controls"), "view-" + button["data-tab"])
        self.assertIn("button.setAttribute('aria-current'", HTML)

    def test_unsaved_conversation_never_requires_vault_session(self):
        # Conversation must remain available even when the user does not create a vault.
        self.assertIn("privateAccess:save", HTML)
        self.assertIn("if(save&&!session)", HTML)

    def test_related_sources_are_not_mislabeled_as_answer_proof(self):
        # The API currently searches against the user prompt, not the model answer.
        # Its links must be labeled as related reading rather than supportive citations.
        self.assertIn("Related reading (not claim-verified)", HTML)

    def test_lock_failure_has_persistent_header_warning(self):
        tag, banner = self.element("security-status")
        self.assertEqual(tag, "p")
        self.assertEqual(banner.get("role"), "status")
        self.assertIn("hidden", banner)
        self.assertIn("Could not confirm vault locked", HTML)
        self.assertIn("lockUncertain?'lock unconfirmed'", HTML)

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable for isolated inline-JS lock test")
    def test_failed_lock_retains_retry_and_clears_sensitive_dom(self):
        # Run only the lock function with a simulated local HTTP failure.
        # This is not a rendered browser or a real server-lock verification.
        js = r"""
          const fs = require('fs');
          const vm = require('vm');
          const source = fs.readFileSync('static/index.html', 'utf8');
          const start = source.indexOf('  async function lockVault(){');
          const end = source.indexOf("  $('lock-button').addEventListener", start);
          if(start < 0 || end < 0) throw Error('lock function absent');
          const elements = {};
          const get = (id) => elements[id] ||= {value:id==='passphrase'?'synthetic partly typed passphrase':'synthetic private text',items:[],append(){this.items.push(...arguments)}};
          let fail = true;
          let attempts = 0;
          const context = {
            session:'synthetic-session', lockUncertain:false, lockInFlight:false,
            $:get, api:async()=>{attempts++; if(fail) throw Error('simulated network timeout'); return {};},
            clearVisibleChat:()=>{get('conversation').items=[];},
            feedback:()=>{},clear:el=>{el.items=[];},node:(tag,cls,text)=>({tag,cls,text}),
            updateBadges:()=>{},loadStatus:async()=>{},
            showSecurityStatus:(message,error)=>{context.message=message;context.error=error;},
          };
          vm.createContext(context);
          vm.runInContext(source.slice(start,end), context);
          (async()=>{
            await vm.runInContext('lockVault()',context);
            if(context.session!=='synthetic-session'||!context.lockUncertain||context.lockInFlight) throw Error('failed lock cannot be retried');
            if(!context.error||!context.message.includes('Could not confirm vault locked'))throw Error('missing visible warning');
            if(get('passphrase').value!=='')throw Error('passphrase still in DOM');
            if(get('journal-text').value!=='')throw Error('journal still in DOM');
            fail=false;
            await vm.runInContext('lockVault()',context);
            if(context.session!==null||context.lockUncertain||context.lockInFlight)throw Error('successful lock did not clear session');
            if(attempts!==2)throw Error('retry did not reach server');
            console.log(JSON.stringify({lockFailure:'warned/retryable/private DOM cleared',retry:'confirmed'}));
          })().catch(error=>{console.error(error);process.exitCode=1;});
        """
        result = subprocess.run(
            ["node", "-e", js], cwd=Path(__file__).resolve().parents[1],
            capture_output=True, text=True, check=False, timeout=8,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["retry"], "confirmed")


if __name__ == "__main__":
    unittest.main()
