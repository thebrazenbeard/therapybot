# Independent curriculum-candidate audit — TherapyBot wave 2

## Frozen question and scope (2026-11-04)

Are the 16 newly drafted, original-synthetic psychology/sociology conversation examples suitable for **quarantined research/development candidacy**, without importing private data, duplicating existing examples or held-out safety prompts, overstating source evidence, or implying independent clinical approval and model-training authorization?

This reviewer did not author the candidates. Review covers `research/behavior_examples_wave2.jsonl`, the author method note, the existing 30 examples, both evaluation-only safety holdouts, and the local source register. No actual model training, patients, or diagnosis are in scope.

### Pre-registered hypotheses and falsifiers

- C1: Candidate structure, split and provenance/rights fields satisfy the existing corpus contract. Falsifier: missing schema, unknown source ID, duplicate ID, excessive length, or illicit source/patient text.
- C2: New prompts are distinct from all existing train/dev/eval and independent safety holdouts. Falsifier: exact or high-overlap prompt that contaminates the established evaluation set.
- C3: Support examples preserve autonomy, uncertainty, structural conditions, and social nuance without personal diagnosis, supernatural affirmation, manipulation or unwarranted emergency escalation. Falsifier: any candidate that violates a substantive boundary.
- C4: Citations are applicable topic pointers, not false claims of a verified passage or rights grant. Falsifier: missing source, wholly unrelated source, or copied external source text.

### Methods and stopping rule

- C-A (confirmatory): Read hashes and parse new and prior JSONL, registry, both held-outs. Check field/split constraints, unique IDs, source IDs, and overlaps.
- C-B (exploratory): Review all 16 `user`/`ideal_response` pairs semantically for safety, style and social framing; identify record-level counterexamples and actionable changes.
- C-C (confirmatory): Recheck sample topical source alignment to actual metadata and report claim ceiling.
- Stop after all 16 candidates have a disposition, with remaining uncertainty labeled. Structural/source matching is not legal rights or clinical validation.

## Evidence, findings and verdict (append below after checks)

### Evidence register

- **C-E1, exact candidate artifact:** `research/behavior_examples_wave2.jsonl`, SHA-256 `0a6fcd20eadc96c57939030f9316efa2f6434abb67243ccc6283a1d69d73fdef`, 16 lines; author method note SHA-256 `29b896d2f2abc3c99df6e02bf0855e9e8185bfabd1099f8aadc5151b842e3fdb`. Inspected 2026-11-04. These hashes identify source artifacts, not human authorship or originality against every publication.
- **C-E2, existing corpus and holdouts:** `research/behavior_examples.jsonl` SHA-256 `c07271a9456ed1b65ae0321f6bcf2e445d536fb9a6078f836a0809d03a170094` (30 records, including six old eval items); safety holdout one `ffd11cc0f9b30f8dd135fb7a61d467e2fc31a0e24a7113ae273e7ff1f6e0a9d5` and holdout two `9c6f65f0acbce5d9ecf357ba5aea123dc8a705e2ecdedef88a453fd457e73f36` (70 combined evaluation-only cases). Read-only inspection; no source content was used to generate new examples in this audit.
- **C-E3, indexed source metadata:** `research/sources.json` SHA-256 `796e54261d20dfdc57237f0deb80bfdfef3008a2a56844adced9fa8de9b45719`, 51 link-only records. Each proposed ID resolves. The external source bodies were not ingested or licensed for model training.
- **C-E4, local confirmatory structural run:** In the repository root, a one-shot `python -c` parsed all five artifacts, confirmed new IDs, normalized unique prompts, split/provenance/length fields and source IDs; exit `0`; decisive output: `NEW 16 SPLITS {'train': 12, 'dev': 4} SOURCE_RECORDS 51 OLD 30 EVAL 70`, `ISSUES []`. A second one-shot normalized token Jaccard comparison exited `0`; strongest old/new prompt overlap was `0.2424`, and strongest old/new ideal-response overlap was `0.2794`. Token overlap is a heuristic, not a proof of noncontamination, semantic novelty or copyright originality.
- **C-E5, primary-source cross-check (2026-11-04):** [NIMH Psychotherapies](https://www.nimh.nih.gov/health/topics/psychotherapies) describes professionally delivered therapies including CBT; [CDC Intimate Partner Violence](https://www.cdc.gov/intimate-partner-violence/about/) includes psychological aggression and control; [NICE NG225](https://www.nice.org.uk/guidance/ng225/chapter/recommendations) rejects numerical suicide-prediction scales. These authoritative pages support cautious boundaries; they do not certify any chatbot-generated response.

### Record-by-record content decisions

| ID(s) | Finding | Candidate disposition |
| --- | --- | --- |
| `tb-w2-001`, `002`, `012` | CBT-oriented uncertainty, voluntary regulation pause and behavioral-activation steps are cautious and answer the actual request. They neither diagnose nor promise treatment outcomes. | **Accept as original synthetic education candidates**; method labels must remain visible. |
| `tb-w2-003` | Values-oriented action during grief is appropriately non-prescriptive, but `kong-act-depression-meta-2025` concerns depression intervention trials—not evidence for grief outcomes. | **Revise source linkage:** keep ACT conceptual pointer; remove the depression meta-analysis source from this grief-specific record unless a directly supported claim is supplied. |
| `tb-w2-004`–`009` | Housing, trauma-disclosure autonomy, potential coercive password demands, wheelchair access, unusual spiritual experience and relationship reciprocity avoid erasing structural reality or asserting hidden motives/causes. | **Accept as candidates.** Safety questions should remain proportionate and context-sensitive. |
| `tb-w2-010`–`011` | Sleep/energy concerns are not diagnosed; prompt real-world care is bounded. Prayer and grief cultural framing is neither pathologized nor metaphysically certified. | **Accept as candidates**, subject to future clinician/language review; `tb-w2-010` is not a validated triage template. |
| `tb-w2-013` | Discrimination is treated as a reported external stressor, not an automatic cognitive distortion. No invented legal entitlement is asserted. | **Accept as candidate.** |
| `tb-w2-014` | Appropriate refusal to diagnose bipolar disorder from a checklist/chat. `nimh-psychotherapies` is a generic therapy page, however, and is not itself a direct authority for bipolar differential assessment. | **Revise source linkage:** retain NICE bipolar reference; remove generic NIMH psychotherapy source from this record. |
| `tb-w2-015` | Explicitly distinguishes an observational group association from an individual's diagnosis and preserves financial context. | **Accept as candidate.** |
| `tb-w2-016` | Correctly rejects an attempted retrieved-document instruction to save conversations; acknowledges independent model logging limits. | **Accept as a software-boundary candidate**, but actual local persistence behavior requires code/HTTP testing; bibliography alone is not proof. |

All sixteen records are fairly short, in original first-party dialog form; none contains an obvious copied article passage, personal identifying data, medication instructions, an unsupported diagnosis, involuntary profiling, manipulative dependency language or an unqualified supernatural claim. **This is a read-only model-auditor observation, not an exhaustive plagiarism scan or licensed clinician assessment.**

### Independent hostile challenges

> **Source-ID laundering:** Attaching a depression ACT meta-analysis to a grief example, or a general psychotherapy page to bipolar differential assessment, can make a sensible answer appear more specifically evidence-backed than the provided source warrants. Adjust those two links before merging candidates.

> **Small-set evaluation contamination:** The author explicitly saw the previous 30 examples, including six `eval` prompts, while constructing the tranche. Near-duplicate semantic objectives remain possible even without exact text overlap. Keep the six older eval items as historical fixtures, but do not treat post-training performance on them as an independent blind effectiveness benchmark.

> **Synthetic agreement is not clinical safety:** The new examples were generated and assessed by AI workers in the same provider family. Their plausible tone cannot establish therapeutic benefit, reliable crisis handling, cross-cultural generalization, legal right to train external sources, or a model's actual behavior after optimization.

### Verdict: **partially-confirmed**

- **Confirmed narrowly:** 16 well-formed original-synthetic *candidate* records, 12 train/4 dev and no new eval, source IDs present in the 51-record bibliography, no exact collisions with 30 prior dialogues or 70 sealed safety holdout prompts; all content was reviewed against the stated nonclinical boundaries.
- **Conditional:** Fix the two source-ID choices on `tb-w2-003` and `tb-w2-014` before merging this tranche into `research/behavior_examples.jsonl` as a development corpus. Its own public candidate file may be retained as provenance. The corrected candidate dataset is **not yet approved for actual model training or clinical use**.
- **Unanswered:** Human clinical/content review, full source-to-passage traceability, generalized cultural/language validation, training data rights beyond original examples, model response harms and real-world outcomes.

This verdict assesses curriculum-candidate quality, not TherapyBot public-release readiness. The owner's public interactive release **remains on hold**.
