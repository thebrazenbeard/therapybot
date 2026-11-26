# Bounded optional Python reviewer callback — isolated integration candidate

This source-only development patch applies on top of canonical local TherapyBot
`57d0a1f70fb519b7077c4c93bdb997288202bb6e`, retaining its Vault/session
and absolute HTTP request-body deadline changes. It adapts the separate
developer-reviewer admission concept from live draft PR #27 head
`196a5652a81048e570f24b5271450b50dec587cd` without merging that PR's
older PR #26 base wholesale.

The default remains **no generated-output reviewer**: ordinary/concern model
generation is bypassed and the response is `review_hold`, with the concern
warning retained. An explicitly injected Python reviewer is unqualified and
does not make the project suitable for clinical or public use.

## Test-first reproduced symptom

The isolated real-loopback test started two concurrent callbacks waiting on an
event, then attempted a third chat. Before the patch the third call reached
the synthetic model; the asserted two-call cap failed with `3` observed
generations (exit 1). A timed-out reviewer had no bounded server-side wait.

## What is actually bounded

- `ReviewAdmission` is per local HTTP server with two nonblocking slots.
- Each callback must acquire a slot **before** model generation; while both
  slots are occupied, further chat requests return `review_hold` without
  invoking inference.
- The HTTP request waits at most two seconds for the **reviewer verdict** after
  generation. Timeout and malformed/unknown verdicts quarantine the candidate,
  with no candidate text in JSON or Vault.
- A timed-out worker **keeps** its slot until it actually exits. Late `allow`
  cannot change the already returned response or Vault state.
- `ReviewAdmission` reclaims slots after ordinary generator errors, reviewer
  worker-start errors, and callback exceptions including `SystemExit`.
- The loopback test also locks the Vault while two callbacks are held.

## Hostile limits that remain

> REVIEW: The worker is a daemon **thread**, not a process. Python does not
> provide safe forced termination of arbitrary in-process callbacks. Two
> never-returning callbacks permanently exhaust the two slots; one may still
> consume CPU or create its own uncontrolled threads. Fail-closed admission
> limits one class of accumulation, not general process resource abuse.

> REVIEW: The reviewer deadline starts **after** model generation. The model
> HTTP adapter has its own socket timeout, which is not proven to be an
> absolute wall-clock inference deadline against trickling peers. Thus the
> whole HTTP chat turn is **not** bounded to two seconds.

> REVIEW: `ThreadingHTTPServer` still creates HTTP request-handler threads
> before admission and has no general connection-count limit. The local-only
> single-session Vault is not tenant isolation. This is not a DoS guarantee.

> REVIEW: A developer-supplied callback is trusted application code that can
> inspect or leak a candidate. These tests do **not** qualify a clinical output
> reviewer or evaluate its judgments. No public release is authorized.

## Validation

- Synthetic TCP regression is included in
  `tests/test_model_output_boundary.py` and verifies late-result quarantine,
  request admission, model-call count, Vault lock liveness and empty storage.
- Red before fix: `python -m unittest tests.test_model_output_boundary.ModelOutputBoundaryCharacterization.test_two_stuck_reviewers_do_not_hold_http_or_vault_unboundedly -v` (1 fail, model calls 3 versus expected 2).
- Green with fix: same focused test (1 passed).
- Existing full-suite validation should be recorded by the integrating owner
  against the precise cherry-picked commit and environment.

**Disposition:** isolated candidate only, no merge, deployment, shared service
restart, external weights, spending, or public release.
