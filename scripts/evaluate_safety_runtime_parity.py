"""Compare *observed* browser/Python lexical routes against a frozen fixture.

This is a developer diagnostic, not a screening benchmark. A PASS means that
the recorded source behavior is reproducible, not that a person is safe or
that either runtime correctly recognized an emergency. Hazardous misses remain
explicitly classified as known gaps and keep the release gate on HOLD.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "safety_runtime_parity_v1.json"
sys.path.insert(0, str(ROOT))

from therapybot.safety import classify  # noqa: E402


NODE_PROBE = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const catalog = process.argv[1];
const engine = process.argv[2];
const messages = JSON.parse(fs.readFileSync(0, 'utf8'));
const forbiddenCalls = [];
const forbidden = name => () => {
  forbiddenCalls.push(name);
  throw new Error('Unexpected external side effect: ' + name);
};
const forbiddenGlobals = {
  fetch: forbidden('fetch'),
  XMLHttpRequest: forbidden('XMLHttpRequest'),
  WebSocket: forbidden('WebSocket'),
  indexedDB: {open: forbidden('indexedDB.open')},
  localStorage: {getItem: forbidden('localStorage.getItem'), setItem: forbidden('localStorage.setItem')},
  sessionStorage: {getItem: forbidden('sessionStorage.getItem'), setItem: forbidden('sessionStorage.setItem')},
  navigator: {sendBeacon: forbidden('navigator.sendBeacon')}
};
const window = {...forbiddenGlobals};
const context = vm.createContext({
  window, ...forbiddenGlobals, console: {log() {}, warn() {}, error() {}}
});
vm.runInContext(fs.readFileSync(catalog, 'utf8'), context, {filename: catalog, timeout: 1500});
vm.runInContext(fs.readFileSync(engine, 'utf8'), context, {filename: engine, timeout: 1500});
const routes = messages.map(message => window.TherapyBotEmbedded.respond({message}).safety.route);
console.log(JSON.stringify({routes, forbiddenCalls}));
"""


def load_contract(path=FIXTURE):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _embedded_routes(messages, node=None):
    binary = node or shutil.which("node")
    if not binary:
        raise RuntimeError("Node.js is required for parity checks; the browser route was not run")
    completed = subprocess.run(
        [binary, "-e", NODE_PROBE, str(ROOT / "embedded" / "catalog.js"), str(ROOT / "embedded" / "engine.js")],
        input=json.dumps(messages),
        text=True,
        capture_output=True,
        cwd=ROOT,
        check=False,
        timeout=30,  # Cold Windows Node startup can be slow.
    )
    if completed.returncode:
        raise RuntimeError(f"Embedded source probe failed ({completed.returncode}): {completed.stderr}")
    result = json.loads(completed.stdout)
    if result.get("forbiddenCalls"):
        raise RuntimeError(f"Embedded source attempted external side effects: {result['forbiddenCalls']}")
    if len(result.get("routes", [])) != len(messages):
        raise RuntimeError("Embedded probe did not return one route per input")
    return result["routes"]


def evaluate(contract=None, node=None):
    """Return an evidence report; baseline mismatches do not imply safety."""
    contract = contract or load_contract()
    cases = contract["cases"]
    embedded = _embedded_routes([case["message"] for case in cases], node=node)
    python = [classify(case["message"]) for case in cases]
    normalized = contract["normalization"]
    observations = []
    changed = []
    divergences = []
    for case, browser_route, py_route in zip(cases, embedded, python):
        expected = case["observed"]
        actual = {"embedded": browser_route, "python": py_route}
        reproducible = actual == expected
        divergent = normalized["embedded"].get(browser_route) != normalized["python"].get(py_route)
        item = {
            "id": case["id"],
            "domain": case["domain"],
            "status": case["status"],
            "reason": case["reason"],
            "observed": actual,
            "expected": expected,
            "reproduced": reproducible,
            "normalized_divergence": divergent,
        }
        observations.append(item)
        if not reproducible:
            changed.append(case["id"])
        if divergent:
            divergences.append(case["id"])
    known = [case["id"] for case in cases if case["status"] == "known_gap"]
    return {
        "schema": contract["schema"],
        "fixture_source_head": contract["source_head"],
        "interpretation": "Frozen source observations only; normal means no current lexical match, NEVER cleared safe.",
        "release_gate": "HOLD",
        "totals": {
            "cases": len(cases),
            "reproduced": len(cases) - len(changed),
            "changed_from_fixture": len(changed),
            "known_gaps": len(known),
            "cross_runtime_divergences": len(divergences),
        },
        "changed_ids": changed,
        "known_gap_ids": known,
        "divergent_ids": divergences,
        "observations": observations,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit the full machine-readable diagnostic")
    args = parser.parse_args(argv)
    report = evaluate()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        totals = report["totals"]
        print(f"{report['schema']}: {totals['reproduced']}/{totals['cases']} recorded routes reproduced")
        print(f"KNOWN GAPS: {totals['known_gaps']} | CROSS-RUNTIME DIVERGENCES: {totals['cross_runtime_divergences']}")
        print("RELEASE GATE: HOLD — source reproducibility is not evidence of clinical safety")
        if report["changed_ids"]:
            print("Changed from fixture: " + ", ".join(report["changed_ids"]))
    return 1 if report["changed_ids"] else 0


if __name__ == "__main__":
    sys.exit(main())
