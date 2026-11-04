# TherapyBot Team01 wave 3 — evidence, curriculum and safety-honesty checkpoint

**Date:** 2026-11-04. **Release state:** development-only; owner has withheld general-public interactive mental-health deployment. No treatment efficacy, emergency-service capability, clinical validation, privacy certification, source-to-claim entailment or model-training rights are asserted here.

**Authority and coordination:** Team01 psychology/sociology research and `main`/README ownership; BT2's runtime, HTML, vault and model experiments continue in separate unmerged draft PRs. Root oriented to current GitHub `main@358a841efd830fecb71ea9fade0aeeef8e97c204` and latest available Blotter entries before this work; do not silently replace the branch with BT2's incompatible historical code.

## Genuine native subagent execution and independent review

First wave: clinical sources, social research, trauma/cultural research, synthetic curriculum, independent hostile provenance review, independent safety-language review. Successor implementation: source validator/merger hardening. Independent review wave: clinical+trauma, sociology, curriculum/cultural response quality, copyright/source stewardship, and validator adversarial replay. Targeted independent correction/re-review rounds followed material findings. Agent review is **not** independent human clinical expert or different-provider model assurance. Reports and exact evidence ceilings are under `docs/WAVE3_*AUDIT.md` and original author method notes under `research/*wave3*method.md`.

## Delivered research and provenance

- Source registry expanded from **51 to 82** external bibliographic/publisher-permission pointers: +10 clinical, +10 social-science, +10 trauma/cultural-context, +1 OpenStax AI-use rights policy. Local `knowledge.sources()` returns **83** distinct combined pointer records (built-in + research). All are original short summaries, not full works; `model_training_rights: not-cleared`, `source_content_included: false` for every external record.
- Independent source reviewers inspected original publisher/DOI/PubMed descriptions and returned **partial confirmation for bibliographic indexing only**, with explicit NICE 403, limited method/full-text access, heterogeneity, GRADE and license caveats. ISTSS source metadata was corrected to note the 2019 recommendation amendment, reuse restrictions and edition-date uncertainty.
- Publisher rights source and independent audit caught a consequential distinction: OpenStax *Psychology 2e* current web preface expressly requires written permission for language-model/generative-AI ingestion, despite the surrounding CC license. The present decision is **link only; no RAG, prompt ingestion or model training on that textbook**. NIMH text-only public-domain terms and WHO edition-specific permissions are documented without claiming universal clearance. No private trauma records or real conversations were accessed.
- Original synthetic response candidates expanded **46 → 62**, split **42 train / 14 dev / 6 eval**. The new 16 have independent source-fit/cultural review and four targeted revisions: trauma-memory evidence links; neutral journal wording; proportionate workplace-exhaustion framing; publisher-specific AI rights reference. Source records were merged first so every new candidate source ID resolves. No weights were trained or pushed.

## Engineering and the safety release hold

- Research metadata validator/merger reject wrong source field types, **syntactically recognizable** private/loopback and numeric-obfuscated URL hosts, canonical URL duplicates, missing evaluation fixtures, wrong-typed labels/splits, and punctuation-only prompt overlap. New independently challenged regression tests were run red-before/green-after. The checks are structural; **DNS indirection/rebinding (e.g. loopback-mapping third-party domains), semantic paraphrase leakage, publisher authenticity and URL-following SSRF safety are not established**. Reference URLs remain link-only metadata; there is no automatic remote content fetch in this step.
- Eight *transparent* development-only `research/safety_canaries_wave3.jsonl` cases and a runnable diagnostic `python -m scripts.evaluate_safety_canaries --strict` preserve the hostile review's observable counterexamples. **3/8** matched the reviewer-assigned engineering expectations on the current heuristic, including misses of an explicit imminent self-harm disclosure and over-escalation of a denial. This score is not clinical sensitivity or another sealed holdout.
- Historical independent synthetic danger-routing holdouts remain **11/34** and **14/36** matched, on different cases. Six previous fake-model HTTP tests deliberately confirmed that unsafe generated responses can pass through; passing software tests are not output-safety qualification.
- BT2 draft PR #5 (local HTML/vault/runtime hardening) and #7 (source metadata/provenance preservation) are separate; they require independent integration review. Team01 did not merge them, alter public Pages, deploy a public chat UI, run model training, or migrate private vaults.

## Reproduction and evidence ladder

From this repository with Python dependencies installed:

```sh
python -m unittest discover -s tests -q
python scripts/validate_research.py
python -m scripts.evaluate_safety_canaries --strict
python -m compileall -q therapybot
git diff --check
```

The third command is **expected to exit nonzero** until the known safety mismatches are addressed. Its failing result is release-blocking engineering evidence, not a CI regression to hide. The full unittest pass and research validator result should be recorded against the **exact final GitHub commit** on publication. A source pointer, passing test, local GGUF demonstration and independent nonclinical review are distinct evidence levels and do not establish efficacy.

**Publication SHA:** see the verified GitHub `main` and final Blotter record for this checkpoint. The root must verify the remote readback and report any remote race, rather than asserting publication in advance.
