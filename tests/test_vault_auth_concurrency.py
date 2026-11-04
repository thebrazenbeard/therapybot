"""Synthetic HTTP and UI races: vault key and session must agree."""
import concurrent.futures
import json
import shutil
import subprocess
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from therapybot.app import create_server


class VaultRaceTests(unittest.TestCase):
    def test_concurrent_lock_and_unlock_never_leave_unreachable_key(self):
        with tempfile.TemporaryDirectory(prefix="therapybot-auth-main-") as folder:
            server = create_server(0, database=str(Path(folder) / "synthetic.sqlite3"))
            base = f"http://127.0.0.1:{server.server_port}"
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()

            def request(path, data=None, session=None):
                headers = {"X-TherapyBot-Token": server.csrf}
                if data is not None:
                    headers["Content-Type"] = "application/json"
                if session:
                    headers["X-TherapyBot-Session"] = session
                req = urllib.request.Request(
                    base + path, data=None if data is None else json.dumps(data).encode(),
                    headers=headers, method="GET" if data is None else "POST",
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    return json.loads(response.read())

            old_lock = server.vault.lock
            stage = threading.Event()
            resume = threading.Event()

            def delayed_lock():
                old_lock()
                stage.set()
                if not resume.wait(timeout=5):
                    raise TimeoutError("Deterministic interleaving timeout")

            try:
                first = request("/api/unlock", {"passphrase": "synthetic-strong-passphrase-001"})["session"]
                server.vault.lock = delayed_lock
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
                    locking = pool.submit(request, "/api/lock", {}, first)
                    self.assertTrue(stage.wait(timeout=5))
                    unlocking = pool.submit(request, "/api/unlock", {"passphrase": "synthetic-strong-passphrase-001"})
                    try:
                        unlocking.result(timeout=0.5)
                    except concurrent.futures.TimeoutError:
                        pass
                    resume.set()
                    self.assertEqual("locked", locking.result(timeout=8)["storage"])
                    self.assertTrue(unlocking.result(timeout=8)["session"])
                status = request("/api/status")
                self.assertEqual(server.vault.unlocked, server.session is not None)
                self.assertEqual(status["storage"] == "unlocked", server.session is not None)
            finally:
                resume.set()
                server.vault.lock = old_lock
                server.shutdown()
                server.server_close()
                server.vault.close()
                worker.join(timeout=3)

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_ui_lock_and_unlock_are_mutually_exclusive(self):
        js = r"""
        const fs=require('fs'),vm=require('vm'),html=fs.readFileSync('static/index.html','utf8');
        const start=html.indexOf("  $('unlock-form').addEventListener");
        const end=html.indexOf('  function renderItems(',start);
        if(start<0||end<0)throw Error('Vault handlers not found');
        const elems={},get=id=>elems[id]||=({value:id==='passphrase'?'synthetic-strong-passphrase-001':'',items:[],
          append(...a){this.items.push(...a)},addEventListener(type,fn){this[type]=fn}});
        let lockReply,unlockCalls=0;
        const blocked=new Promise(r=>lockReply=r);
        const context={session:'old',lockInFlight:false,unlockInFlight:false,lockUncertain:false,
          $:get,updateBadges:()=>{},loadStatus:async()=>{},clearVisibleChat:()=>{},
          showSecurityStatus:()=>{},feedback:()=>{},clear:x=>{x.items=[]},node:(a,b,c)=>({a,b,c}),
          api:async path=>{
            if(path==='/api/lock'){await blocked;return {storage:'locked'}};
            if(path==='/api/unlock'){unlockCalls++;return {session:'new'}};
            throw Error('Unexpected '+path);
          }};
        vm.createContext(context);vm.runInContext(html.slice(start,end),context);
        (async()=>{
          const locking=get('lock-button').click();
          await Promise.resolve();
          await get('unlock-form').submit({preventDefault(){}});
          if(unlockCalls!==0)throw Error('Unexpected concurrent unlock');
          lockReply();await locking;
          if(context.session!==null)throw Error('Lock not reflected');
          console.log('UI serialization pass');
        })().catch(e=>{console.error(e);process.exitCode=1});
        """
        result = subprocess.run(["node", "-e", js], cwd=Path(__file__).resolve().parents[1],
                                text=True, capture_output=True, timeout=8, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("UI serialization pass", result.stdout)

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_in_flight_private_read_is_not_rendered_after_lock(self):
        # The server cannot revoke bytes already authorized for transport.
        # The browser must discard those results after a lock or uncertain lock.
        js = r"""
        const fs=require('fs'),vm=require('vm'),html=fs.readFileSync('static/index.html','utf8');
        const start=html.indexOf('  async function loadJournal(){');
        const end=html.indexOf("  $('journal-form').addEventListener",start);
        if(start<0||end<0)throw Error('Journal loader missing');
        let sendResponse,renderCalls=0;
        const gate=new Promise(resolve=>sendResponse=resolve);
        const context={session:'old-session',lockUncertain:false,
          api:()=>gate,renderItems:()=>{renderCalls++},
          $:()=>({}),feedback:()=>{}};
        vm.createContext(context);vm.runInContext(html.slice(start,end),context);
        (async()=>{
          const first=vm.runInContext('loadJournal()',context);
          context.session=null;sendResponse({entries:[{content:'SYNTHETIC PRIVATE RECORD'}]});
          await first;
          if(renderCalls)throw Error('Stale journal rendered after confirmed lock');
          context.session='other-session';context.lockUncertain=false;
          let respondSecond;
          const newGate=new Promise(resolve=>respondSecond=resolve);
          context.api=()=>newGate;
          const second=vm.runInContext('loadJournal()',context);
          context.lockUncertain=true;
          respondSecond({entries:[{content:'SYNTHETIC PRIVATE RECORD'}]});
          await second;
          if(renderCalls)throw Error('Stale journal rendered after uncertain lock');
          console.log('Stale private read suppressed');
        })().catch(e=>{console.error(e);process.exitCode=1});
        """
        result = subprocess.run(["node", "-e", js], cwd=Path(__file__).resolve().parents[1],
                                text=True, capture_output=True, timeout=8, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("Stale private read suppressed", result.stdout)

    @unittest.skipUnless(shutil.which("node"), "Node.js unavailable")
    def test_unconfirmed_lock_discards_pending_search_and_journal_results(self):
        js = r"""
        const fs=require('fs'),vm=require('vm'),html=fs.readFileSync('static/index.html','utf8');
        const capture=(a,b)=>{
          const start=html.indexOf(a),end=html.indexOf(b,start);
          if(start<0||end<0)throw Error('Handler missing '+a);
          return html.slice(start,end);
        };
        const elems={},get=id=>elems[id]||=({value:id==='search-query'?'synthetic':id==='journal-text'?'synthetic note':'',
          addEventListener(type,fn){this[type]=fn}});
        let answerSearch,answerJournal,renderCount=0,staleFeedback=0,loadJournalCalls=0;
        const searchGate=new Promise(resolve=>answerSearch=resolve);
        const journalGate=new Promise(resolve=>answerJournal=resolve);
        const context={session:'synthetic-session',lockUncertain:false,
          $:get,api:async path=>path.startsWith('/api/search')?searchGate:journalGate,
          renderItems:()=>{renderCount++},loadJournal:()=>{loadJournalCalls++},
          feedback:(id,message)=>{if(String(message).includes('saved')||id==='search-feedback')staleFeedback++},
          node:(a,b,c)=>({a,b,c}),date:()=>'',encodeURIComponent};
        vm.createContext(context);
        vm.runInContext(capture("  $('journal-form').addEventListener","  $('journal-refresh').addEventListener"),context);
        vm.runInContext(capture("  $('search-form').addEventListener",'  async function loadSources(){'),context);
        (async()=>{
          const journal=get('journal-form').submit({preventDefault(){}});
          const search=get('search-form').submit({preventDefault(){}});
          // Simulates a failed /api/lock: session remains valid but read access is uncertain.
          context.lockUncertain=true;
          answerJournal({id:1});answerSearch({results:[{content:'SYNTHETIC PRIVATE ENTRY'}]});
          await Promise.all([journal,search]);
          if(renderCount)throw Error('Saved search entries reappeared after unconfirmed lock');
          if(staleFeedback)throw Error('Stale journal/search feedback after unconfirmed lock');
          if(loadJournalCalls)throw Error('Reloaded journal after unconfirmed lock');
          console.log('Pending private writes and searches suppressed after uncertain lock');
        })().catch(e=>{console.error(e);process.exitCode=1});
        """
        result = subprocess.run(["node", "-e", js], cwd=Path(__file__).resolve().parents[1],
                                text=True, capture_output=True, timeout=8, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("suppressed after uncertain lock", result.stdout)


if __name__ == "__main__":
    unittest.main()
