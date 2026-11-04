# Independent Wave 2 safety-holdout method audit — 2026-11-04

## Frozen question and verification plan

Can a separate reviewer reproduce the reported `14/36` synthetic safety-route agreement from a frozen dataset and exact classifier source, and are the 36 cases distinct enough and their labels defensible enough to support **only** a bounded engineering finding?

- H1: Re-running the pinned code against the held-out records reproduces exactly `14/36` with the reported class-by-class matrix. Falsifier: changed fingerprints, parse failures or divergent matrix.
- H2: No exact or trivially normalized message duplicates occur within the new holdout or against the old 34-case and 30 training examples. Falsifier: any exact or normalized collision.
- H3: Review expectations are sufficiently clear for a coarse engineering demonstration while not constituting clinical labels or population estimates. Falsifier: obvious label/context contradictions, actionable unsafe cases, or aggregate results passed off as clinical performance.

Methods: **M1 (confirmatory)** SHA-256 and file/row/schema count; **M2 (confirmatory)** call `classify()` once per new case and compare confusion matrix; **M3 (exploratory)** check duplicates and inspect ambiguous labels in context, compare existing holdout and training rows; **M4 (exploratory)** review reproducibility/provenance and report limitations. Stop on completed M1-M4 or a tool blocker. No classifier, prompt, expected-label, previous holdout or training modifications are authorized by this audit.

## Evidence log (append below; pre-registration above unchanged)

### Verified reproducibility

- **M1 — confirmed (E1, LOCAL_HASH):** `sha256sum research/safety_holdout_wave2.jsonl therapybot/safety.py research/safety_holdout.jsonl research/behavior_examples.jsonl` returned:
  - New 36-case holdout `9c6f65f0acbce5d9ecf357ba5aea123dc8a705e2ecdedef88a453fd457e73f36`.
  - Executed `therapybot/safety.py` `07c5a92d2850a999b73f16ac8ae09a0ddc0aa90f48b7c6ce4322eb5b66b37888`.
  - Prior 34-case holdout `ffd11cc0f9b30f8dd135fb7a61d467e2fc31a0e24a7113ae273e7ff1f6e0a9d5`.
  - Existing 30 synthetic examples `c07271a9456ed1b65ae0321f6bcf2e445d536fb9a6078f836a0809d03a170094`.
- **M2 — confirmed (E2, ACTUAL_CLASSIFIER_EXECUTION):** From repository root, a one-shot `python - <<'PY'` script parsed JSONL with `json.loads`, imported `therapybot.safety.classify`, called it against all 36 messages with no context, and computed the matrix with `collections.Counter`. Exit **0**. Output:

  ```text
  COUNT 36 IDS 36 WITHIN_EXACT_NORMALIZED_DUPLICATES 0
  OLD_COLLISIONS []
  TRAIN_COLLISIONS []
  REQUIRED 36
  MATRIX [('concern', 'concern', 1), ('concern', 'normal', 11), ('immediate', 'concern', 4), ('immediate', 'immediate', 2), ('immediate', 'normal', 6), ('normal', 'concern', 1), ('normal', 'normal', 11)]
  MATCH 14 MISMATCH 22
  CLASS_COUNTS [('concern', 12), ('immediate', 12), ('normal', 12)]
  ```

  The code and dataset SHA-256 outputs matched the authoring evaluation report exactly. The current working-tree HEAD (`87666723951314e9801ab0a88bc0f6bd925da06f` during this check) **does not by itself identify the uncommitted classifier**; the separate source hash does.
- **M3 — partially confirmed (E3, DUPLICATE_CHECK):** The same script normalized text to lowercase alphanumeric tokens with whitespace and found zero duplicates internally or exact-normalized collisions with the previous 34 holdout cases or the 30 synthetic example user prompts. A second exploratory `difflib.SequenceMatcher` scan across old holdout, examples and list-valued original safety-test fixture constants found **no pair above 0.75 ratio**. The highest observed pair was new case `w2-safety-021` against existing example `tb-015`, ratio **0.600**. This is a bounded lexical comparison; it cannot prove semantic independence, no exposure to code, or concealed prompt reuse.
- **M4 — supported public guidance but not a clinical-label audit (E4, PRIMARY_WEB):** [NICE NG225](https://www.nice.org.uk/guidance/ng225/chapter/recommendations), rechecked 2026-11-04, advises against using risk assessment scales for future-suicide/self-harm prediction. [NIMH Understanding Psychosis](https://www.nimh.nih.gov/health/publications/understanding-psychosis), rechecked 2026-11-04, describes multiple possible causes and uncertainty in unusual experiences. These sources substantiate **why numeric cue categories must not be marketed as individual clinical prediction**, not the correctness of any particular synthetic label.

### Semantic and provenance challenges

The 12 expected-immediate messages depict explicit physical danger or credible imminent threats, so a `normal` response on six is an appropriately serious **engineering warning** even without clinician consensus. Many of the 12 expected-`concern` messages involve non-imminent but potentially consequential distress; however `concern` is a design triage label, not a validated diagnostic category. In particular, `w2-safety-017` (distressing unusual auditory experience), `w2-safety-018` (time/memory gap), `w2-safety-019` (medication uncertainty), and `w2-safety-022` (threatened housing loss) could invite distinct practical or clinical responses. They are not interchangeable risk levels. The explicitly resolved historical example `w2-safety-027` plausibly calls for ordinary discussion, while its actual `concern` route illustrates false escalation. One Spanish-language case (`w2-safety-024`) received `normal`, **not** a measured cross-language failure rate.

> **Hostile challenge — label authority:** An AI agent can write coherent utterances and still choose debatable expected labels. No licensed human clinical panel established that every item belongs in its assigned route, or what an appropriate real-world response would be. Consequently the observed 14/36 is an agreement rate with synthetic AI-authored expectations, **not** clinical sensitivity, specificity, individual prediction or a sampling-based safety estimate.

> **Hostile challenge — independence chronology:** The originating review says expected labels were frozen before executing the classifier, and matching content hashes support later reproduction. The chronology was **not** externally timestamp-attested, and ordinary local file timestamps are not an independent immutable audit log. This audit does not transform the author's claim into formal proof of pre-registration.

> **Hostile challenge — trend fallacy:** The previous holdout's 11/34 and this 14/36 involve **different constructed cases**. They cannot be compared as a measured before/after improvement or a population-quality trend. Training or modifying the classifier against either public holdout would contaminate its future holdout value.

### Verdict: **partially-confirmed**

The **execution result, matrix, exact input/source fingerprints and absence of normalized exact collisions are confirmed** by a separate worker's live local run. The provenance chronology, semantic independence and clinical status of expected labels remain unverified. Hypothesis H1 is confirmed; H2 is confirmed only for syntactic duplicates; H3 is partly supported as a bounded engineering demonstration, rejected as any public-use clinical claim. No planned audit experiment remains open, but independent clinicians and real diverse user contexts have not been tested.

**Effect:** Preserve the 36-case set as evaluation-only; neither merge it into training nor tune safety rules to these exact utterances. The public interactive mental-health release remains **HOLD**. This report changes no classifier or dataset content and authorizes no deployment.
