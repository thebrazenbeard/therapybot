# TherapyBot generated-output review boundary — developer-only slice

**Source basis:** draft PR #24 HEAD `03d197e84021fd1f640561053acee9fabcb914e2`; this note describes an isolated unmerged descendant, not public deployment.

## What changed

The Python `/api/chat` handler treats a generated model completion as **untrusted**. It now calls a separately supplied server-owned reviewer before a candidate may enter HTTP response JSON or opt-in vault storage. The candidate never authorizes itself by saying it is safe.

The built-in reviewer is **absent**. If none is supplied, the app immediately returns a fixed `review_hold` response without making a costly model call. If a supplied reviewer says `block`, returns an unknown/malformed verdict, raises an exception, or the candidate exceeds 12,000 characters, the app quarantines the candidate and returns the same neutral fallback. A concern cue can add the pre-existing static concern prefix, but cannot append an unreviewed generated reply.

`/api/chat` returns `output_review=quarantined` and `saved=false` when held. `/api/status` explicitly reports `ready_scope=observed_local_model_output_only_not_safety`, `output_review_qualified=false`, and `clinical_qualified=false`; `ready` is a narrow backend-response observation, **not** a mental-health release gate.

## Development-only reviewer seam

Trusted server-side Python code may inject a callable `output_reviewer` into `create_server(...)`, returning the exact string `allow` or `block`. Only an explicit `allow` permits model text; no reviewer is installed by the CLI, website, or browser. The tests use an artificial reviewer and synthetic model strings to exercise this plumbing. That is **not** an independently validated safety classifier or a general-public feature.

A deliberately malicious or faulty injected reviewer could allow harmful text. Same-process callbacks are not an authenticated isolation boundary. A synchronous reviewer can hang; this slice does not provide process isolation or enforce a reviewer execution deadline.

## Exact behavioral evidence

- TDD RED 1 (old code): `test_unreviewed_neural_candidate_is_quarantined_by_default` failed exit 1, expected `review_hold`, observed `model`. GREEN after output-boundary insertion: 1/1 exit 0.
- TDD RED 2 (initial new code): 15,000-character candidate with artificially injected `allow` reviewer was displayed, expected `review_hold`. GREEN after 12,000-character cap: 1/1 exit 0.
- Hostile RED 3: with no reviewer the server still invoked the model once, expected zero calls. GREEN after default generation short-circuit: 14 focused tests exit 0.
- Honesty RED 4: no-reviewer fallback claimed it had generated a draft when generation was short-circuited. GREEN after replacing the copy with a truthful no-reviewer statement.
- After revising two legacy test setups to deliberately inject a synthetic reviewer for their old test purposes, Windows Python 3.14 `python -m unittest discover -s tests -q` returned **169 tests, OK (skipped=2), exit 0, 38.004 seconds**. ResourceWarnings from test HTTPError cleanup remained; they are not production output leaks.
- No real GGUF generation, private transcript data, live browser user session, independent clinical evaluation, or public deployment was executed by this patch.

## Remaining release blockers

> FAIL: No independently tested generated-output reviewer is available. The safe default is therefore an honest non-neural response, **not** a functioning broadly useful neural companion. A trusted server-side callback is only an integration seam.

> FAIL: The current inbound cue router has documented unseen-case misses; a missed input plus an unreliable reviewer could permit harmful text if the integrator explicitly uses the `allow` seam. Clinical safety remains **unknown**, not passed.

> FAIL: The single process-global vault/session and loopback Host/Origin model do not support arbitrary public multi-user access. Existing private data and URL restrictions are deliberately unchanged.

> UNKNOWN: Long-running injected reviewers are not interrupted by this synchronous API. A future reviewer should run in a bounded isolated process with explicit deadline and independent adversarial verification.

**Disposition:** keep branch draft/unmerged, no public interactive release or claims of clinical qualification until a reviewer and the full end-to-end path are independently qualified.
