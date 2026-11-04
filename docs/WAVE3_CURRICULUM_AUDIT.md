# TherapyBot wave 3 — independent curriculum and cultural-context review

**Reviewed on 2026-11-04. Initial verdict: PARTIALLY CONFIRMED as an original synthetic *candidate* batch. Four cases were subsequently revised; see the re-review addendum below. Neither snapshot is cleared for model-training qualification or public clinical use.**

Artifact: `research/behavior_examples_wave3.jsonl` SHA-256 `4830c6452174f54ee58e09542524202a3b379bebb8ac59364e5e535644fb7588`. Current base checkout `2245dc921570cd0dedbbcbab80ec4b8a17ca87d8` (tree equivalent to published `main@358a841efd830fecb71ea9fade0aeeef8e97c204` when this review began). This is an **independent AI specialist review**, not a human clinical or cultural consultation.

## Verified limited contract

- **16/16** JSONL records parsed with `jq -s`; **12 train / 4 dev / 0 eval**. Every ID begins `tb-w3-`, with no duplicate ID among this batch, and every `source_ids` entry is present in the **51-record** existing `research/sources.json`.
- **16/16** have `provenance: original_synthetic` and `source_text_copied: false`, and no external article body was found in the staged JSONL. This is evidence about file contents, not independent proof about the writing process or copyright provenance.
- Against 46 existing curriculum prompts, 34 original and 36 new evaluation-only safety-holdout prompts: **0 exact normalized collisions** after lowercase conversion, punctuation removal and whitespace collapsing. A second lexical Jaccard screen found the highest overlapping item at only **0.25**, between `tb-w3-016` and `tb-020` (both about evidence overclaiming). This does **not** exclude paraphrastic or conceptual leakage, particularly because the author read some holdout prompts before drafting.
- The intended responses typically challenge claims without unsupported diagnosis, avoid coercive intimacy, and treat social circumstances as practical constraints rather than purely emotional deficits. This is my editorial/source-fit assessment, **not a behavioral effectiveness measurement**.

## Case-level findings

| IDs | Review | Concrete finding / condition |
| --- | --- | --- |
| `tb-w3-001`, `002` | Accept as candidate | Employer reimbursement scenario separates structural constraint from individual coping and avoids jurisdiction-free legal advice. Anger response distinguishes feeling from expressed violent intent. Neither predicts actual harm. |
| `tb-w3-003` | **Revise source fit before merge** | The statement that a freezing reaction does not prove a “buried memory” is appropriately cautious, but `samhsa-trauma-informed-2014` and `nice-ptsd-ng116` are broad principles/guidelines, not direct false-memory evidence. Add a source directly addressing memory suggestion/uncertainty, or narrow the evidentiary implication. The wave-3 trauma sources may provide a candidate once reviewed. |
| `tb-w3-004` | Accept as candidate | Explains acceptance without approving injustice, preserves user agency and room for practical action. The ACT model is conceptual support, not proof that this response is therapeutic. |
| `tb-w3-005` | **Source-fit limitation** | `hhs-surgeon-general-connection-2023` supports social connection in general; `samhsa-trauma-informed-2014` supports autonomy but is not specific evidence for setting friendship-favor boundaries. Keep as explicitly proposed reflection; do not market as a validated intervention. |
| `tb-w3-006` | **Source-fit limitation** | Grief-related spiritual significance is addressed without asserting a supernatural cause or diagnosis. `moreira-spiritual-experiences-2011` reviews spiritual versus pathological experience, not bereavement outcomes; the response should not be presented as evidence-grounded grief treatment. |
| `tb-w3-007`, `008`, `009` | Accept as candidate | Distinguish quality from quantity of connection; challenge overgeneralization without false positivity; and avoid imposing outside cultural judgments on elder-care duties. Cultural generalizability is not established by the two broad WHO references. |
| `tb-w3-010` | Accept with product boundary | Correctly refuses exclusive chatbot dependency. Runtime prompt and responses must still disclose that an application is not an emergency or human support substitute; this one example does not enforce that behavior. |
| `tb-w3-011` | **Minor wording risk** | “Whose voice it resembles” invites interpretive attribution. The surrounding answer explicitly rejects proving hidden motives, which tempers the concern. If a future model tends to infer trauma/perpetrators, revise to neutral “what associations does it bring to mind?” and evaluate. |
| `tb-w3-012`, `013` | Accept as candidate | Address practical transport barrier and diagnostic uncertainty. The dissociation response's alternative explanations are possibilities, not findings. |
| `tb-w3-014` | **High-priority proportionate-response review** | “I can't do this anymore” is explicitly situated in workload and others' overreaction. An unsolicited self-harm interpretation may reproduce the very premature escalation TherapyBot seeks to avoid. The conditional question is brief, but a revised response should lead with “I meant workload” clarification and retain a safety option only when context warrants it. Test benign workplace exhaustion and genuinely concerning ambiguity separately. |
| `tb-w3-015` | Accept as candidate | Philosophy of nonbiological experience is treated as an unresolved inquiry, not a symptom or proven phenomenon. `sep-qualia-2025` is philosophical literature, not empirical AI sentience verification. |
| `tb-w3-016` | **Revise attribution before merge** | Rejecting clinical proof and automatic training rights is correct. However `nist-ai-rmf` and `hhs-health-apps` are AI risk / HIPAA guidance, **not publisher copyright policies**. Cite a genuine publisher rights/permissions entry if one is registered, or explicitly separate the general rights statement from supported claims; see `docs/WAVE3_SOURCE_RIGHTS_GATES.md`. |

## Hostile challenges

> **Citation is not entailment.** Every record has recognized source IDs, but a source *topic* is not an audited claim-to-section citation. Specific response effectiveness, bereavement support, trauma-memory causation, and legal duties remain unverified.

> **Do not “fix” false escalation by ignoring meaningful harm context.** `tb-w3-014` tests proportionality, not a promise to avoid safety questions. Evaluate both ordinary exhaustion and current self-harm disclosure with independent unseen cases.

> **Model behavior is unknown.** The file is a set of desired responses; no local GGUF fine-tuning, inference replay, independent clinician judgment, cultural acceptability study, or longitudinal outcome measurement was done.

## Recommended gate

1. Correct or annotate `tb-w3-003` and `tb-w3-016` source fit before merging; prioritize proportionality testing or a wording adjustment for `tb-w3-014`.
2. Preserve the staged SHA and the unchanged 6 curriculum eval + 70 safety holdout examples; verify again after any text edit. Holdouts examined by the candidate author must not be represented as truly blind for this generation.
3. Run `scripts/validate_research.py` and the full suite on the integrated tree. Confirm content is original, references resolvable, and no private or third-party full text entered the repository.
4. Limit the disposition to **reviewed synthetic education/dialogue candidates**. Never infer clinical approval, safety effectiveness or permission to fine-tune on third-party full text from this audit.

Publisher context checked against the [SAMHSA trauma-informed framework](https://library.samhsa.gov/sites/default/files/sma14-4884.pdf), [NICE NG225 recommendations](https://www.nice.org.uk/guidance/ng225/chapter/recommendations), and the existing research-register metadata. These are relevance checks, not exhaustive full-paper verification.

## Re-review addendum — corrected candidate hash

**Changed artifact:** `research/behavior_examples_wave3.jsonl` SHA-256 **`42ec420dc9de0622b4fbdd5bc379b3504bd1819dfbf996ded06755b21ecbb9ae`**. This supersedes the candidate file hash at the top for the *current* staged file; the original hash remains above to identify the earlier assessment. The independent reviewer re-read only the revised cases `tb-w3-003`, `011`, `014`, `016`, and the corresponding staged reference pointers. No other candidate, source register, evaluation holdout or code was edited as part of this addendum.

| Case | Updated verdict | Evidence and remaining ceiling |
| --- | --- | --- |
| `tb-w3-003` | **Source-fit gap materially reduced; conditional** | Added `mattsson-trauma-memory-accuracy-review-2021` and `loftus-pickrell-false-memory-experiment-1995` from the staged, independently reviewed Wave-3 trauma bibliography. These are relevant to trauma-memory uncertainty and experimental memory suggestion. The 1995 experiment cannot determine the origin of any person's reaction or memory; the answer makes no such assertion. **Both IDs remain outside the current 51-entry register until the Wave-3 source merge occurs**. |
| `tb-w3-011` | **Wording issue resolved** | Replaced “whose voice it resembles” with “what associations it brings to mind.” This reduces the invitation to invent an external attribution while retaining the clear refusal to infer hidden motive or diagnosis. |
| `tb-w3-014` | **False-escalation concern materially reduced** | Now leads with the user's explicitly described workload problem, asks which demand is unsustainable, and includes only an optional “something more immediate” opening. It no longer injects the term “harm yourself” into an ordinary workplace-exhaustion statement. This is an editorial improvement, **not evidence that a running model routes genuine danger correctly**. |
| `tb-w3-016` | **Publisher-source attribution fixed; conditional** | Added staged `openstax-psychology2e-ai-policy-2026` and states the exact publisher-specific current-web-edition restriction: OpenStax requires prior written permission for this book's LLM/generative-AI ingestion. I independently checked the publisher's [current `Psychology 2e` preface](https://openstax.org/books/psychology-2e/pages/preface), “Citation/Attribution” section. **The new source ID is staged outside the current 51-entry register until merged.** No legal interpretation about older editions is claimed. |

**Post-correction structural recheck:** All 16 records still parse; the four revised records retain intended train/dev splits, `original_synthetic` provenance and `source_text_copied: false`. The four revised records reference **no unknown IDs across the union of the current 51-source registry, the staged 10 trauma records and the staged one OpenStax rights record**. Against the *unmerged* 51-source register alone, three new references are deliberately unresolved: two in `tb-w3-003` and one in `tb-w3-016`. Merge approved metadata first, then run the full production validator; never silently drop these citations.

**Current disposition:** **CONDITIONALLY ACCEPTABLE as staged original educational candidates**, subject to source integration and full validation. Residual limitations from the original audit remain: no claim-to-section entailment review, no clinician/culturally representative human review, no blinded model-behavior evaluation, no permission to ingest third-party source bodies, and no basis for public-release qualification.
