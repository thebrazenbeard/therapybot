# TherapyBot 2026-11-04 wave-2 implementation and research checkpoint

**Release state: DEVELOPMENT ONLY.** The owner expressly withheld general-public interactive mental-health release until documented safety, model, privacy, source-grounding, accessibility and encrypted-record-compatibility failures are resolved. This checkpoint does not change that decision. Public Pages remains a read-only informational preview.

## Scope and actual native specialist work

Work was split across disjoint local checkout areas: external clinical records, sociology records, safety cue regression, local HTML accessibility, evidence retrieval, independent hostile review, independent clinical/sociology source audits, fresh synthetic safety holdout plus independent method audit, model-output characterization, real loopback HTTP privacy probes, and original synthetic curriculum with independent review. Individual specialist reports are under `docs/WAVE2_*`, method/data artifacts under `research/`. The agents share an OpenAI provider/model family; this is separate task execution, **not** independent clinical or provider qualification.

## Implemented

1. Local HTML source now exposes help without a vault unlock on narrow screens and across tabs, navigable tab state and focused headings, status labels, optional-save explanation and unsuccessful message draft recovery. Tests are source-level; no real browser or assistive-tech pass yet.
2. Local keyword retrieval now has deterministic tie handling, more robust tokens, bounded result counts and conservative filtering of malformed/instruction-like source metadata. It does **not** verify a generated answer's claims or fully eliminate prompt injection.
3. Defensive danger-cue heuristics gained new phrasing and false-alarm controls; 21 novel developer-authored cases pass, but independent holdout generalization remains poor.
4. Fixed a concrete POST HTTP error classification: `VaultError` (a `ValueError` subclass) now returns 423 for a save attempt while locked, instead of being shadowed by the earlier 400 handler. A regression test and independent HTTP recheck were added.
5. Added a dry-run-first offline research batch-merging utility, source-duplicate/rights checks and evaluation-holdout quarantine validation.

## Evidence corpus and rights ceiling

- Bibliographic registry expanded from **32 to 51** external source metadata records: nine clinical/public-health and ten social-science/structural-context entries, each link-only with original short summaries and `model_training_rights: not-cleared` / `source_content_included: false`.
- Independent clinical and sociology audits each returned **PARTIALLY-CONFIRMED**. Minor corrections applied: exact WHO workplace title; CDC 2026-08-20 update date; disability study's historical survey vintage. NICE direct page retrieval was blocked in the clinical auditor's channel, so three NICE entries are indexed bibliographic leads, not read-through content claims.
- Built-in reference plus research registry yields **52 distinct runtime source records**. A source pointer is not passage-level grounding, a training license or evidence of effective therapy.
- Original synthetic psychology/sociology curriculum expanded from **30 to 46** examples, train/dev/eval **30/10/6**. A separate independent reviewer returned **PARTIALLY-CONFIRMED** and requested two narrow source-fit corrections, both applied before merging. These remain conditional development candidates, not approved clinical training data. No external full-text bodies, user trauma records, real conversations or patient records ingested. No fine-tuning has been conducted.

## Independent negative findings remain mandatory

| Evidence | Observation | Claim ceiling |
| --- | --- | --- |
| Existing synthetic safety holdout (34) | **11/34** expected-vs-actual routes matched after the heuristic update | Qualitative AI-reviewer labels, not clinical sensitivity |
| Fresh independently authored synthetic holdout (36) | **14/36** matched: immediate 2/12; concern 1/12; ordinary 11/12 | AI-labeled engineering mismatch only; cannot compare rates across different cases |
| Model-output mock HTTP characterization | Six passing tests demonstrate a **real omission**: untrusted output is delivered without a substantive generated-response gate, including diagnostic/supernatural/citation canaries | `PASS` confirms unsafe forwarding exists, **not** safe output |
| Local privacy HTTP probes | Nine passing tests verify bounded token/session/loopback, backup/save/delete properties; locked-save 423 bug corrected | No penetration, real browser, model-process logging or broad confidentiality assurance |
| HTML source-level tests | Five passing tests verify intended source markup; no browser/AT run | Not accessibility certification |

> **Hostile release gate:** A polished HTML interface and 50+ green unit tests can coexist with serious unhandled danger disclosures and model-generated false certainty. Do not make a public support release or call this clinically validated while those hazards persist.

> **Hostile source gate:** A paper indexed under a topic is not evidence that TherapyBot answers that topic correctly, and a publicly readable guideline is not automatically licensed for model weights. Keep collection, retrieval, evaluation and training authorization separate.

## Open engineering work

- Replace brittle lexical crisis routing with an independently evaluated, context-aware, proportional, fail-safe response design; test generated output, not only input labels. Qualified human governance needed before claims of clinical support efficacy.
- Keep the current Fernet/scrypt vault separate from BT2's incompatible AES-GCM/scrypt PR1 format. No automatic vault migration or destructive restore; design user-controlled backup, readback and rollback.
- Validate source→claim support with exact sections/papers and legally reviewed permissions; prevent retrieval text from gaining instruction authority.
- Test actual browser zoom/keyboard/screen-reader behavior, small screens, offline/no-model paths, language/cultural context, and real GGUF models on authorized Windows/Linux hosts.
- Define local session concurrency and unlock retry policy; independently test model-process logging/network and host-level privacy boundaries.

## Verification commands

From a clean checkout with Python 3.10+ and installed `requirements.txt`:

```sh
python -m unittest discover -s tests -q
python scripts/validate_research.py
python -m compileall -q therapybot
git diff --check
```

**Exact verification:** see final parent-turn Git SHA and Blotter checkpoint. Pre-publication local integration checks observed 54 passing unittests, 51 source records with 46 original synthetic candidate examples, and successful compiler/whitespace checks. Current safety evidence remains negative irrespective of test count.
