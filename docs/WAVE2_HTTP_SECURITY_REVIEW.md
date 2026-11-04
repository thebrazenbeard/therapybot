# TherapyBot Wave 2 — Independent HTTP Privacy Boundary Probe

**2026-11-04 — source + isolated local runtime tests, not a security certification**

## Scope and evidence

The probe used `therapybot/app.py`, `therapybot/model.py`, and `therapybot/storage.py` as they stood in the shared TherapyBot worktree during the second development wave. I wrote only `tests/test_http_privacy_wave2.py` and this report; I did not change production code, install services, use real medical/personal records, connect an actual model, or contact a remote host. Each case starts a fresh real `AppServer` bound to `127.0.0.1` on an ephemeral local port with a temporary synthetic SQLite vault. A deterministic `FakeModel` avoids third-party or model-server network calls while exercising normal HTTP chat/save behavior.

Executed:

```text
python -m unittest tests.test_http_privacy_wave2 -v
Ran 9 tests in 5.233s
OK
exit code 0
```

The first run exposed one mismatched HTTP error code: an attempted save without vault unlock returned **400** rather than the intended **423**. This was not a bypass. During review, the parent integration task corrected the exception ordering in `therapybot/app.py` and added an exact regression in `tests/test_app.py`. I subsequently tightened the new test to require **423**; the revised app and both test modules passed **16/16** on a fresh run. The original discovery is preserved below.

## Confirmed implementation behavior

| Boundary | Actual isolated result | Evidence class |
| --- | --- | --- |
| Loopback bind | `AppServer(('0.0.0.0',0),...)` rejected by constructor | Source + runtime unit probe |
| Forged HTTP Host/Origin | Mismatched hosts, foreign and HTTPS origins returned HTTP 403 | Real local HTTP probe |
| Missing or incorrect process token | Chat, unlock, journal, record deletion returned 403 | Real local HTTP probe |
| Private reads | History, journal, search and backup rejected absent/guessed session | Real local HTTP probe |
| Backup | GET backup required **both** token and current vault session; synthetic canary absent from backup bytes | Real local HTTP + synthetic ciphertext inspection |
| Save defaults | Ordinary model-backed chat with `save:false` left vault empty, before and after unlocking; `save:true` required a valid session | Real local HTTP with deterministic fake model |
| Deletion | Required a valid session and literal `X-TherapyBot-Confirm: DELETE`; previously copied backup remained unaffected | Real local HTTP in throwaway vault |
| Body parsing | Invalid JSON, oversize body, overlong message, wrong content-type rejected with 400 | Real local HTTP probe |
| Model host | Remote HTTPS/LAN addresses, query secrets and URL fragments rejected by `ModelClient` constructor | Local source/constructor tests |

The served page included a no-store cache header, frame denial, and nosniff. This verifies header presence, **not** browser exploitation resistance.

## Findings and attack paths requiring follow-up

### P1 — Single server-global vault session; concurrent sessions invalidate each other

`AppServer.session` is one process-wide bearer token. A second correct unlock rotates that token: the first session is denied (`403`), the second works (`200`). This avoids two independent active sessions but can disrupt multiple tabs or clients and creates a last-unlock-wins race. A stolen active bearer token plus access to the process CSRF token would permit the same protected operations as that tab while unlocked. Exact local credential theft was **not** demonstrated by these tests.

**Recommendation:** Decide between explicit single-client ownership with visible lockout semantics or per-client session registry with expiry/lock revocation, then test concurrent unlock/lock/backup flows. Do not claim browser-bound authentication before that test.

### P1 — Locked-save error was mislabeled 400, not 423 (source-level remediated)

At the initial snapshot, `VaultError` derived from `ValueError`; in `do_POST`, the earlier `except (ValueError, json.JSONDecodeError)` caught it before `except VaultError`. The intended 423 handler was unreachable for these failures. A synthetic unauthenticated `save:true` request returned HTTP **400** and saved nothing. This was a misleading status/UX boundary, not an access-control bypass.

**Fix and verification during this wave:** The parent changed the handler order and added an exact expected-423 test. I independently re-ran `tests.test_app` and `tests.test_http_privacy_wave2`: **16 tests passed**, with `save:true` from an ununlocked vault now returning **423**. Integration still needs a Git commit and review; the problem should no longer be represented as active in the modified local tree.

### P1 — No unlock throttling, timeout, or per-client failed-attempt governance

The source checks passphrase-derived keys but contains no failed-unlock counter, backoff, or session expiration mechanism. Per-attempt scrypt work creates cost, but is not a substitute for an explicit local threat policy. No brute-force attack was attempted; resistance remains **unverified**.

**Recommendation:** Define bounded local abuse-resistance measures without encouraging a lockout that traps a legitimate user; test denial-of-service and wrong-passphrase behavior in isolation.

### P1 — Other privacy claims remain outside this probe

No actual GGUF inference process, browser, browser extension, firewall, remote DNS rebinding attacker, disk forensic analysis, vault migration, or cross-machine runtime was tested. `ModelClient` checks the configured URL and suppresses explicit proxy use, but a separately installed local model process can log or relay prompts. Local-only endpoint enforcement cannot establish end-to-end confidentiality. The HTML CSP still permits inline scripts, which weakens mitigation if markup ever becomes injectable.

> **Hostile challenge:** If one browser tab can learn another tab's active vault token through a local compromise, is the product protected by a separate security boundary, or only by an assumed uncompromised same-origin environment?

> **Hostile challenge:** Would the same source assertions survive an actual browser DNS-rebinding attempt and locally configured model that logs or proxies requests? Until tested, no blanket confidentiality guarantee follows.

## Verdict

**PARTIALLY-CONFIRMED for these narrow access-control properties; INCONCLUSIVE for end-to-end confidentiality or public-release readiness.** The nine passing probes are meaningful local HTTP evidence and add coverage beyond the baseline tests. They cannot substitute for independent penetration review, browser/assistive-technology validation, clinical harm evaluation, safe vault migration, or data-deletion assurance.

Public interactive release remains on hold under the owner's direction.
