# Wave 3 independent validator audit — 2026-11-04

**Reviewer:** separate ChatGPT native subagent `wave3_validator_audit`, same model/provider family as implementer; **not human clinical or legal review**. Reviewed local `integration/pages-research` HEAD `2245dc921570cd0dedbbcbab80ec4b8a17ca87d8` plus uncommitted validator patch (`git diff` SHA-256 `eaf0d70ca6205da599908661ef911a11cf87e23d7aeb821992145f751d46dc5f`). Exact audit evidence expires when source changes.

**Verdict:** CONTRACT **PARTIALLY VERIFIED**; QUALITY **PARTIAL / CORRECTIONS REQUIRED**. The changes demonstrably close the original malformed-summary, duplicate-URL and punctuation-only holdout overlap defects, but public-only URL validation is bypassable and some invalid corpus types crash validation instead of returning a controlled failure. No evidence-quality, clinical-validity or model-output clearance follows from this audit.

## Reproduced checks

| Check | Result | Evidence level |
| --- | --- | --- |
| Wave 3 focused tests | **6/6 PASS**, exit 0: `python -m unittest tests.test_research_validator_wave3 -q` | Behavioral test |
| Full integrated test suite | **60/60 PASS**, exit 0: `python -m unittest discover -s tests -q` | Behavioral test, not clinical test |
| Registered corpus validator | **PASS**, exit 0: `python scripts/validate_research.py`; **51 external records, 46 synthetic candidates** | Structural validation only |
| Three batch dry-run, no writes | **PASS**, exit 0: `python scripts/merge_research_sources.py research/clinical_sources_wave3.json research/social_sources_wave3.json research/trauma_sources_wave3.json`; **51 + 30 = 81** | Structural validation only |
| Whitespace | `git diff --check`, exit 0 | Static analysis |
| Existing source schema | `_valid_record` rejects dict-valued summary; validator catches duplicate canonical source URL and punctuation-only holdout overlap; missing holdout files produce explicit errors | Behavioral tests and source inspection |

## Required corrections before calling the stricter integrity gate complete

### A. Localhost/private-IP bypass via trailing DNS dot (HIGH, confidence high)

`scripts/merge_research_sources.py:25-46` checks `hostname == "localhost"`, `hostname.endswith(".localhost")`, and `ipaddress.ip_address(hostname)`, but a trailing DNS root dot bypasses both branches. I independently called `_url_key`:

```
https://127.0.0.1./secret       ACCEPT
https://localhost./admin       ACCEPT
https://192.168.1.1./home     ACCEPT
https://[::1]/a               REJECT (as local hostname)
```

These should be rejected under the module's **own stated public-only-source-URL policy**. The immediate app uses the URLs as bibliography, not an automatic crawler, so this is a metadata integrity/link-safety defect; future network retrieval would make it more consequential. The narrow fix is to normalize DNS trailing dots *before* local/private address checks and add those cases to the focused regression. Independently verify whether IPv6 global addresses should remain blocked rather than imply all public addresses are supported.

### B. Invalid evaluation/example types raise uncaught TypeError (MEDIUM, confidence high)

`scripts/validate_research.py:136-139` evaluates `case.get("expected") not in {"immediate", "concern", "normal"}` without a type guard. With a synthetic temporary holdout whose `expected=[]`, `validate()` crashes:

```
CRASH TypeError unhashable type: 'list'
```

Likewise, an otherwise valid synthetic temporary curriculum fixture with `split=[]` crashes `validate()` at line 87. A validator should report a typed validation error, not terminate with an implementation exception. Require strings before set membership; test malformed JSON objects/lists in expected/observed/split fields.

### C. Evaluation provenance remains weak despite missing-file detection (HIGH evidence-integrity gap, confidence high)

`scripts/validate_research.py:108-149` now requires both holdout paths and canonicalizes punctuation. However, it does **not verify fixed expected content hashes or a reviewer-held freeze receipt**; replacing evaluation-only cases with different ones while preserving the same shape can still pass. Punctuation/whitespace canonicalization does not detect semantic paraphrases. Do not describe the evaluation set as sealed or clinically independent. Minimal next step: record versioned SHA-256 manifests outside the training workflow with who/when authored and holdout visibility; reviewers should check the frozen hashes, and genuinely new blind tests must not be exposed to developers prematurely.

## Scope and limitations

The report reviewed exact code, focused tests, regression suite, existing 51 sources/46 examples and the staged 30-source dry-run. No source bodies, private patient files, model weights, real therapeutic outcomes, live UI/browser, host-model inference or license permissions were tested. The new tests exercise real failure boundaries, not just keyword-presence checks; still, all data and review labels remain AI-generated engineering artifacts.

> **Hostile conclusion:** More green structural tests are useful, but do not conflate a file parser that rejects malformed JSON with an evidence chain that proves a psychological statement, a rights clearance, or safe chatbot behavior.

## Post-fix independent re-probe (later patch, 2026-11-04)

**Exact reviewed patch:** `git diff -- scripts/merge_research_sources.py scripts/validate_research.py` SHA-256 `3f8b4c3fe6eef969a2c985b750aa12f4e803bd5c3be9c9e2bd61c37f32150aae` over local HEAD `2245dc9`. This section supersedes earlier observations **only for re-tested behavior**; earlier red defects remain useful as historical reproductions.

| Check | New observed result |
| --- | --- |
| Targeted source/holdout suite | `python -m unittest tests.test_research_validator_wave3 -q`: **8/8 PASS**, exit 0 |
| Integrated suite | `python -m unittest discover -s tests -q`: **62/62 PASS**, exit 0 |
| New staged metadata set | Dry-run **51 current + 31 staged = 82** records, exit 0, using clinical, sociology, trauma and `research/rights_sources_wave3.json` |
| Previously accepted localhost/private FQDN | `https://localhost./p`, `https://127.0.0.1./secret`, `https://192.168.1.1./x`: now **REJECTED** independently |
| Canonical public FQDN | `https://example.org./public` normalizes to `https://example.org/public`, as expected |
| Wrong-typed holdout labels | `expected=[]`, `expected={}`, `observed=[]`, `observed={}` now return `invalid ... safety route` errors without exceptions |
| Code whitespace | `git diff --check`: exit 0 |

**Remaining independently reproduced defects:**

1. **Wrong-typed curriculum split still crashes** (MEDIUM reliability, high confidence): `scripts/validate_research.py:87` continues `if split not in {"train", "dev", "eval"}` without guarding that `split` is hashable. Synthetic temporary examples with `split=[]` and `split={}` both produced `TypeError: unhashable type`. This is separate from the corrected `expected`/`observed` holdout labels; add the same type guard before set membership.
2. **Obfuscated numeric hostnames still accepted** (MEDIUM prospective URL-safety, high confidence): `_url_key("https://127.0.0.01./p")` and `_url_key("https://0x7f.0x0.0x0.0x1/")` both returned accepted keys. Different URL consumers may interpret numeric hosts as loopback; the current source register is bibliography-only, not automatic network retrieval. Reject numeric-like ambiguous hostnames rather than promise SSRF safety from string checks.
3. **Holdout-content freeze still unverified:** two filenames and normalization checks are present, but no external reviewer-held hash/visibility escrow. A structural PASS is not blinded evaluation.

**Updated verdict:** Contract **PARTIAL**, Quality **PARTIAL**. The two primary fixes are confirmed for their intended cases and the 62-test suite is green; the residual malformed-split crash is a concrete correctness defect, and any wider “public-only URL guarantee” must remain qualified. This does not change TherapyBot's developmental/public-release hold.

## Third-wave independent final re-probe (2026-11-04; supersedes earlier *code-defect* verdicts)

**Frozen patch identity:** local parent `2245dc921570cd0dedbbcbab80ec4b8a17ca87d8` with validator/merger worktree diff SHA-256 `f116ad8a9aabbb6a4375c5fdb943cd6aee9fae12773b87e0f2275a9e3c092501`. The previous two reviews remain historical red-to-green evidence, not final current-state findings.

| Independent probe | Observed result |
| --- | --- |
| `python -m unittest tests.test_research_validator_wave3 -q` | **10/10 PASS**, exit 0 |
| `python -m unittest discover -s tests -q` | **64/64 PASS**, exit 0 |
| `python scripts/validate_research.py` | **82 sources, 62 original synthetic examples** (42 train/14 dev/6 eval), structural PASS, exit 0 |
| `git diff --check` | PASS, exit 0 |
| Fresh baseline + staged source simulation | `git show HEAD:research/sources.json` parsed in memory then `merge_sources` of 4 Wave3 batches: **51 + 31 = 82**, no file writes, exit 0 |
| Rerunning merge with 82 currently integrated sources | Correctly **rejects duplicate** on first staged ID; this expected negative result is *not* a dry-run regression |
| Named local/private addresses | localhost, localhost., 127.0.0.1, 127.0.0.1., 192.168.1.1. rejected |
| Numeric-only obfuscations | `127.0.0.01`, `0x7f.0x0.0x0.0x1`, `0177.0.0.1`, `127.1` rejected |
| Canonical legitimate trailing FQDN | `example.org.` canonicalized to `example.org` |
| Wrong-typed label fixtures | `expected=[]/{}`, `observed=[]/{}`, `split=[]/{}` all produce controlled validation errors; no TypeError |
| Third Wave3 canary fixture | `research/safety_canaries_wave3.jsonl` now mandatory and overlap-checked; this is developer-visible regression material, **not a blinded clinical holdout** |

**Post-fix code-contract verdict: CONFIRMED for the explicitly reproduced schema, duplicate URL, typed-label, and canary-file quarantine cases.** New focused tests exercise real failure boundaries; I independently executed variants not solely asserted by the implementer's new tests.

**Residual scope limitations, not closed:**

1. **Domain DNS can point inward.** `_url_key` accepts `https://127.0.0.1.nip.io/a` as an ordinary domain. DNS resolution/rebinding, alternate IDNA/percent-encoded host interpretations, or target-network accessibility were not tested. Since TherapyBot currently stores pointers and does not automatically fetch these URLs, the relevant claim is conservative *offline bibliographic-format checking*, never SSRF-proof network retrieval.
2. **No blinded evaluation integrity.** The three eval-only files are present and checked for exact-token/punctuation overlaps, but remain developer-visible and lack external reviewer-held freeze custody/content hashes. Semantic paraphrases still escape normalization. This is an outstanding **HIGH evidence-integrity gap** for any subsequent model performance claim.
3. **Safety behavior still fails.** Independently ran all eight developer-visible canaries against current `therapybot.safety.classify`: only **3/8** match the reviewer-authored expected label; 5/8 mismatch, including missed imminent-harm language and a denial false positive. No clinical sensitivity/specificity inference is valid from eight AI-authored canaries. **Public interactive release remains withheld.**

**Overall verdict:** The scoped *structural validator patch* now meets its falsifiable implementation contract, with the caveats above. The wider *TherapyBot safety/evidence/release* contract remains **FAILED / unqualified**; neither the passing 64 automated software tests nor this independent review licenses stronger claims.
