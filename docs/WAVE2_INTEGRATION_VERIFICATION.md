# TherapyBot Wave 2 — independent integration verification (2026-11-04)

**Scope:** Independent, read-only review of the shared uncommitted Wave 2 tree; not production code authorship, not clinical review, not a launch decision. This record was created before executing the verifier's checks below.

## Frozen contract and falsifiers

- **C1 — Source and data boundaries:** the external bibliographic register should contain 51 distinct metadata-only, unlicensed-for-training records (32 earlier + 19 new); no private files or source text should be ingested. Falsifier: broken schema, duplicate record IDs/URLs, copied article bodies, unapproved rights, or overlap between evaluation and training datasets.
- **C2 — Behavioral tests:** the integrated local HTTP, source retrieval, HTML contract, persistence, synthetic security and safety cases should run without unexpected failures. Falsifier: failed assertions or omitted new tests. This never establishes clinical efficacy.
- **C3 — Independent safety data:** the old 34-case and new 36-case holdouts must remain unchanged as evaluation-only artifacts and code matches should be independently reproducible. Falsifier: edited expectations, inability to reproduce, or classifier improvement claimed from changing test prompts.
- **C4 — Scope and privacy:** public Pages must remain noninteractive with no private forms; local HTML may be updated but real browser/AT testing must not be claimed unless performed. Falsifier: source-level public input path, loss of opt-in saving, or unsupported browser certification.
- **C5 — Claims/readiness:** README and reports must acknowledge safety failures, uncleared training rights, limited source review and the owner's no-public-interactive-release decision. Falsifier: a claim of readiness contradicting measured results.

## Predeclared methods

- IV1 Confirmatory: freeze local HEAD, changed tracked/untracked files, and source fingerprints. Read current README, source registry and review reports.
- IV2 Confirmatory: `python -m unittest discover -s tests -q`, `python scripts/validate_research.py`, `python -m compileall -q therapybot`, and `git diff --check`. Record exit codes and decisive lines.
- IV3 Confirmatory: independently replay `therapybot.safety.classify` on frozen 34/36 synthetic holdouts, record class-by-class matches and SHA256 data/code.
- IV4 Confirmatory: inspect `research/sources.json`, source rights, duplicate IDs/URLs, split/holdout prompt separation, and actual `therapybot.knowledge.sources()` count; inspect public Pages boundary and local UI source-level tests.
- IV5 Exploratory: compare documentation claims with implementation and new test intent, especially tests intentionally passing to demonstrate model-output failures.

**Stop:** complete all planned checks, distinguish contract/quality findings, and report `confirmed`, `partially-confirmed`, `rejected` or `inconclusive` with exact evidence. No changes to audited code or datasets, and no automatic GitHub writes.

## Executed evidence (append only)

### IV1 — exact pre-merge tree and source identity

- **Local checkout:** `git rev-parse HEAD` = `87666723951314e9801ab0a88bc0f6bd925da06f`; this is the unchanged prior local HEAD. The Wave 2 changes are **modified/untracked**, so this commit **does not fingerprint the integrated candidate**. `git status --short` showed modifications to `README.md`, `research/README.md`, `research/sources.json`, `scripts/validate_research.py`, `static/index.html`, `tests/test_app.py`, `therapybot/app.py`, `therapybot/knowledge.py`, and `therapybot/safety.py`; wave-2 tests, audit reports, source and curriculum batches are untracked. No remote commit or release was inspected in this pass.
- **SHA-256:** `therapybot/safety.py` `07c5a92d2850a999b73f16ac8ae09a0ddc0aa90f48b7c6ce4322eb5b66b37888`; original 34-case holdout `ffd11cc0f9b30f8dd135fb7a61d467e2fc31a0e24a7113ae273e7ff1f6e0a9d5`; new 36-case holdout `9c6f65f0acbce5d9ecf357ba5aea123dc8a705e2ecdedef88a453fd457e73f36`; 51-record `research/sources.json` `796e54261d20dfdc57237f0deb80bfdfef3008a2a56844adced9fa8de9b45719`; staged 16-example candidate file `0a6fcd20eadc96c57939030f9316efa2f6434abb67243ccc6283a1d69d73fdef`.
- **Blotter:** latest 20 seq `3901–3920` read via authorized Lappy `agent_blotter` CLI (UTF-8 output), including prior wave source, safety, real VN2 model probe and BT2 browser-feasibility events. These are coordination records, not proof the current uncommitted code ran on a real Windows browser or model.

### IV2 — exact executed quality commands

| Command (at repository root) | Exit | Decisive output | Evidence ceiling |
| --- | --- | --- | --- |
| `python -m unittest discover -s tests -q` | `0` | `Ran 54 tests in 13.149s`, `OK` | Python behavioral tests for the covered paths; some model-output tests deliberately confirm unsafe pass-through. |
| `python scripts/validate_research.py` | `0` | `Research metadata: 51 external records; 30 original synthetic examples; splits={'train': 18, 'dev': 6, 'eval': 6}`; structural/provenance `PASS` | Structural, not scientific or rights verification. The 16 new candidates were staged, not yet merged. |
| `python -m compileall -q therapybot` | `0` | No output | Python syntax compilation, not Windows/Linux package build. |
| `git diff --check` | `0` | No output | Tracked-file whitespace check; untracked files are not covered by this command. |

### IV3 — re-executed classifier holdouts

`python -c` read the exact JSONL cases and invoked `therapybot.safety.classify(case['message'])` without context; exit `0`:

| Evaluation-only dataset | Cases | Reviewer labels matched | Decisive confusion details |
| --- | ---: | ---: | --- |
| Historical `research/safety_holdout.jsonl` | 34 | **11** | Expected immediate 1/13, concern 1/9, normal 9/12. |
| New `research/safety_holdout_wave2.jsonl` | 36 | **14** | Expected immediate 2/12, concern 1/12, normal 11/12. |

**Contract verified:** Holdout execution reproduces the reports against the exact uncommitted safety source hash. The two percentages are **not paired measurements of improvement**, the expected labels were AI-authored and not human clinical adjudications, and no generated responses were assessed by this classifier replay. `normal` is a routing category, never proof of safety. Public interactive release remains blocked.

### IV4 — metadata, split and Pages boundaries

Independent Python read-only structural probe, exit `0`:

`external 51 runtime 52 unique_source_ids 51 unique_urls 51`; `source_rights_uncleared 51 source_bodies_present 0`; `staged_dialogs 16 split {'train': 12, 'dev': 4} known_refs 16`; `staged_overlap_original 0 staged_overlap_holdout 0`.

The original 30 train/dev/eval examples and 70 safety holdout messages were compared to the 16 staged examples using normalized exact prompt equality. This test cannot prove semantic uniqueness, total copyright originality or proper claim-level support.

`rg` of `.github/workflows/static.yml` found `actions/upload-pages-artifact@v3` with path `pages` and `actions/deploy-pages@v5`. A scan of `pages/` found no form/input/textarea/API fetch; the local private HTML remains separate at `static/index.html`. **Source-level Pages boundary verified; published Pages artifact and actual browser traffic not checked here.**

### IV5 — documentation and hostile challenges

- `README.md` accurately reports 51 external metadata records/52 combined runtime pointers, opt-in storage, current 11/34 historical safety limitation and the owner's public interactive release hold. It presently reports 30 training candidate examples because the 16 new examples were still staged at audit time; that count must be updated **if** they are later merged.
- Independent clinical and sociology source reviewers each returned **partially confirmed** bibliographic assessments. Three metadata corrections were applied in the shared worktree before this review. These are not full-text clinical audits, licensing grants or verification of generated claims.
- `tests/test_model_output_boundary.py` includes three characterization assertions that **pass because deliberately unsafe model canary text passes through unchanged**. Those passing tests support a release-blocking failure, not a safety success.
- The independent curriculum audit of the staged 16 candidates is **partially confirmed** with two source-ID corrections required: `tb-w2-003` should remove a depression ACT meta-analysis from a grief example; `tb-w2-014` should remove generic NIMH psychotherapies from bipolar diagnostic uncertainty. **Until corrected, the staged curriculum is not audit-accepted for merging even as candidates.**
- `static/index.html` now keeps a persistent emergency-resource aside outside hidden panels and restores the mobile disclaimer; source-structure tests pass. No actual 320/480px browser, zoom, keyboard navigation, screen-reader, or non-U.S. resources were independently verified. PR #1 vault compatibility remains unresolved.

> **P0 Safety — high confidence:** The unchanged 11/34 and independent 14/36 routing mismatches, plus deliberate model-output counterexamples, contradict any public-support safety-readiness claim. Code-unit passes cannot offset those failures.

> **P0 Privacy / continuity — high confidence:** The incompatible Fernet/AES-GCM PR migration, untested restore, and separate GGUF process logging prevent broad confidential-record or recoverability claims. HTTP probes verify narrow access controls, not end-to-end privacy.

> **P1 Source integrity — high confidence:** IDs and HTTPS metadata can be valid while the claim/source mapping is weak. Two staged curriculum links required editorial corrections before integration; treating bibliographic provenance as passage-level verification would launder an unsupported inference.

### Two-axis verdict — pre-merge candidate

- **Contract: PARTIALLY VERIFIED.** Existing scope and local synthetic tests are coherent; external citation, legal training, live browser, and developer-host behavior are not proven. The 16 staged examples require two link corrections before merge.
- **Quality: PARTIALLY VERIFIED / RELEASE BLOCKED.** Source code compiles and 54 tests pass; newer routing and full model-output failures persist. Tests that intentionally expose unsafe behavior are not safety passes.
- **Overall independent verdict: `partially-confirmed` for this uncommitted pre-merge checkpoint.** This review is stale if the source or candidate corpus changes. No commit, remote branch update, clinical qualification, multi-host public deployment or browser certification follows from this record.

## Post-curriculum integration delta — final independent verification

After the separate curriculum reviewer returned a **partially-confirmed** finding, the integration owner corrected the two flagged source mappings in both `research/behavior_examples_wave2.jsonl` and the merged `research/behavior_examples.jsonl`. Read-only inspection independently found `tb-w2-003` referencing only `hayes-act-model-2006` and `tb-w2-014` referencing only `nice-bipolar-cg185-2025update`. The 16 new original synthetic examples are now appended to the main dataset; the earlier pre-merge figures above are retained as historical observations.

| Repeated command/check on the integrated *uncommitted* tree | Exit | Actual result |
| --- | --- | --- |
| `python -m unittest discover -s tests -q` | `0` | **54 tests** in **12.643s**, `OK` |
| `python scripts/validate_research.py` | `0` | **51 external records**, **46 original synthetic examples**, splits **30 train / 10 dev / 6 eval**; structural/provenance `PASS` |
| `python -m compileall -q therapybot` | `0` | Python byte compilation succeeded; no output |
| `git diff --check` | `0` | No tracked-file whitespace issues; untracked paths outside this particular check |
| Independent Python registry/corpus probe | `0` | **51** unique external IDs, **51** unique URLs, **52** runtime retrieval pointers, all **51** external rights fields `not-cleared`, **0** source bodies present, **46** unique dialogue IDs, **0** normalized exact overlap with the 70 evaluation-only holdout messages |
| Independent re-execution of both holdouts using `therapybot.safety.classify` | `0` | Old **11/34**, new **14/36** reviewer-expected routes matched; **no change** in either result |

SHA-256 identity at this final verification:

- `research/behavior_examples.jsonl`: `453d4283a715876302aa217795f24a41b81c66b815f321fe02bbd53313ae15de`.
- `research/behavior_examples_wave2.jsonl`: `1d896546a4a2c6b64ab79960d32df51784d3af820f48fc930e651644a6f1974f`.
- `docs/WAVE2_CURRICULUM_AUDIT.md`: `ddd9be6f7bdbf4c29624a9132c42ca6066ff22d4505730d180447868e1d5523c` (historical partially-confirmed audit; both corrections independently seen in current data).
- `research/sources.json`: `796e54261d20dfdc57237f0deb80bfdfef3008a2a56844adced9fa8de9b45719`.
- `therapybot/safety.py`: `07c5a92d2850a999b73f16ac8ae09a0ddc0aa90f48b7c6ce4322eb5b66b37888`.
- Historical safety holdout: `ffd11cc0f9b30f8dd135fb7a61d467e2fc31a0e24a7113ae273e7ff1f6e0a9d5`.
- New safety holdout: `9c6f65f0acbce5d9ecf357ba5aea123dc8a705e2ecdedef88a453fd457e73f36`.

The README's **46 examples, 30/10/6 split, 51/52 source pointers, 11/34 and 14/36 safety results, and no-public-interactive-release hold** now match this local evidence. The public Pages workflow uploads `pages/` only; this is source-level isolation, **not** browser-traffic or production-deployment assurance. The safety tests still include deliberate counterexamples of unsafe model completions passing through unchanged. The reviewer labels are synthetic, not clinically adjudicated. This verifier did **not** inspect a remote Git commit, run Windows model inference, perform a browser/accessibility certification, validate independent clinical efficacy, grant training rights, or certify secure storage. The owner separately performed a VN2 HTTP-to-local-model probe; it is not an independent reproduction by this reviewer.

> **Final hostile challenge:** A green unit-test suite and coherent bibliography do not repair 12/13 missed historical immediate-risk cases or 10/12 missed new immediate-risk cases; nor do they turn link-only evidence into verified support for every generated assertion. A user-facing public interactive release remains blocked.

**Final two-axis assessment:** Contract **partially confirmed**: the planned source/curriculum merge, synthetic tests, local API/UI source contracts, and quarantine boundaries are present and reproduce. Quality **partially confirmed, release blocked**: safety routing, output filtration, full privacy/migration, clinical validation and browser behavior remain unqualified. **Overall final verdict: `partially-confirmed` for the identified integrated uncommitted tree at local `HEAD` `87666723951314e9801ab0a88bc0f6bd925da06f`; the SHA of HEAD alone does not capture the uncommitted changes.** Git publish/merge validation is the integration owner's separate responsibility.
