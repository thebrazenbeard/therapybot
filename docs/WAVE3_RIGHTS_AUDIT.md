# Independent publisher-rights audit — TherapyBot Wave 3

**Date:** 2026-11-04
**Scope:** `docs/WAVE3_SOURCE_RIGHTS_GATES.md` and the registered/staged *bibliographic* source pointers.
**Reviewer:** separate native licensing/data-stewardship review worker.
**Evidence ceiling:** publisher website/source inspection and structural source-data checks; **not a lawyer's opinion, rights-holder grant, or permission for model training**.

## Verdict: PARTIALLY CONFIRMED — one material omission

The root rights-gate memo correctly separates bibliographic indexing, text redistribution, retrieval, adaptation, model fine-tuning, and weight distribution. It correctly keeps source bodies out of GitHub and third-party model-training rights uncleared. **However, the OpenStax row understates a current publisher-specific AI restriction**; amend it before treating the textbook as an eligible AI retrieval or training source.

### 1. OpenStax *Psychology 2e*: explicit generative-AI permission restriction

- The **current online preface** states that its content is offered under CC BY-NC-SA 4.0 for ordinary noncommercial adaptation and redistribution, with page-by-page attribution and share-alike obligations. In the same publisher page's `Citation/Attribution` section, OpenStax explicitly requires **prior written permission for inclusion in LLM training or ingestion into generative-AI offerings**. That restriction is stated independently of its general CC license discussion. [Current official preface](https://openstax.org/books/psychology-2e/pages/preface), lines around the "Citation/Attribution" heading.
- A **separately hosted older official PDF** of *Psychology 2e* has a 2020 copyright page calling the textbook CC BY **4.0** (without NC-SA) and an older preface consistent with that. Its terms visibly conflict with the newer web edition's 2026 wording. [Older official PDF](https://assets.openstax.org/oscms-prodcms/media/documents/Psychology2e_WEB.pdf), copyright page and preface.
- I **cannot determine whether or how the later website AI condition legally affects an independently fixed earlier CC BY 4.0 edition**. Do not select favorable language from one artifact and apply it silently to the other; bind rights records to the exact document hash/version, and seek written publisher clarification for generative-AI ingestion.
- **Required correction to the memo:** describe *Psychology 2e* as **link-and-bibliography only for TherapyBot's AI use until OpenStax written permission or version-specific legal confirmation**. "Free textbook" and "noncommercial" do not establish a right to put its text into the model context or weights. Ordinary human-directed link-out remains different from copying its text into a chatbot's reference store.

### 2. NIMH: text reuse supported with strict scope

- The [NIMH website policy](https://www.nimh.nih.gov/site-info/policies) identifies its own website/publication **text** as public-domain unless a page indicates otherwise, requests citation and accuracy, and says **images and logos are not reusable**. It asks that reproduced materials not imply advertising, NIMH endorsement, specific medical treatment recommendations or referrals.
- The policy explicitly distinguishes external linked sites: NIMH **cannot grant permissions for third-party content**. Verify authorship and notices for each selected item.
- **Decision:** limited candidate for accurately attributed, version-identified *text-only* educational reference, subject to page exceptions and keeping medical advice/endorsement out of presentation. It is **not a validation of clinical model use**. Existing all-`not-cleared` training flags can remain conservative until an actual use-specific rights decision is recorded.

### 3. WHO: publication-specific, not domain-wide

- The [WHO copyright policy](https://www.who.int/about/policies/publishing/copyright) describes CC BY-NC-SA 3.0 IGO for relevant WHO-issued publications, plus different licenses for articles produced in other venues. It warns about third-party material inside WHO documents and identifies uses needing permission where a work is *not* under the applicable CC license. WHO logo and implied endorsement are excluded.
- Translations/adaptations require appropriate source acknowledgement, disclaimers and suitable downstream licensing. Edition year and the publication's actual copyright notice govern; older and coauthored material can differ.
- **Decision:** bibliographic pointers and original summaries only, pending per-publication permission/rights review for copying, local AI retrieval, or fine-tuning. The root memo's current WHO row is appropriately conservative.

## Usage-specific status matrix

| Action | Current finding |
| --- | --- |
| Link to third-party official page with independent short summary | **Permitted as repository practice**, subject to accurate metadata and no invented endorsement; does not assert clinical claim-to-section support. |
| Copy NIMH-owned text into a private local educational cache | **Candidate, not implemented**; confirm exact page public-domain/third-party exceptions, version, attribution, clinical context and private-cache boundaries. |
| Copy OpenStax text into prompt context/RAG or fine-tune | **Do not implement without additional rights clearance**; current site explicitly demands written permission for AI ingestion and older PDF has conflicting terms. |
| Copy WHO document text into local AI/RAG or fine-tune | **Not cleared**; inspect exact edition, IGO terms, third-party rights, attribution/adaptation and AI-use interpretation. |
| Redistribute full third-party chapter or model weights trained on it | **Not cleared**; no rights grant or clinical evaluation supplied by this audit. |
| Use original synthetic developmental dialogues with source IDs | **Development candidates**, separate from redistribution of source passages. Synthetic authorship does not prove scientific grounding or clinical safety. |

## Data checks and recommended actions

The existing source register is bibliographic, and the Wave 3 staged files are short metadata entries rather than publication bodies. Their conservative `model_training_rights: not-cleared` and `source_content_included: false` decisions should be preserved. I found no publisher grant in the checked source material authorizing third-party model training.

1. **Fix OpenStax row** before implementing local corpus ingestion: explicitly mention its AI-use permission clause and the older PDF/web license conflict.
2. Keep a rights record per exact artifact (`version_url`, `retrieved_at`, checksum, `rights_notice_url`, human reviewer, intended use, disposition). Do not infer all years/editions of a work share the same policy.
3. If pursuing a rights-cleared library, prioritize NIMH's identifiable, attributed, text-only public-domain educational pages. Do not include logos/images or derive a false clinical authority from them.
4. Require a separate decision before any OpenStax/WHO body ingestion, public redistribution or model fine-tuning. **A link in `sources.json` is not permission to train.**

> **Hostile falsifier:** A permissive 2020 PDF copyright statement and a 2026 web-page AI restriction coexist under the same book title. Treating that title as a single rights-cleared corpus would contaminate the training manifest before a single model step.

## Post-audit source-pointer review

After the primary audit, the root created `research/rights_sources_wave3.json` with one proposed bibliographic pointer (`openstax-psychology2e-ai-policy-2026`) to the **publisher's rights notice**, not to the textbook contents. I independently inspected it and `tb-w3-016` in the staged synthetic curriculum.

- **Confirmed:** title, canonical HTTPS URL, rights-warning summary and descriptive Citation/Attribution section anchor match the current OpenStax site. The pointer does not include copied textbook prose, photographs or embedded content; model-training rights are `not-cleared` and `source_content_included` is `false`.
- **Structural merge probe:** `python scripts/merge_research_sources.py research/rights_sources_wave3.json` returned `51 existing + 1 staged = 52`, `mode=DRY-RUN`; no registry mutation or collision in this check.
- **Curriculum cross-reference:** `tb-w3-016` describes the distinction between a bibliography and clinical/model rights, appropriately cites this policy pointer, and contains no copied publication passage. It will remain a development-only synthetic example until independently reviewed and merged.
- **Metadata correction recommended:** `source_license: publisher-ai-ingestion-permission-required` is a *permission condition*, not a license identifier. Represent the current web notice's **CC BY-NC-SA 4.0** license explicitly and retain its separate AI-use restriction in `rights`/`limitations` or a dedicated use-rights field.
- **Date uncertainty:** `date: 2026` could be mistakenly treated as the date of an explicit publisher revision. The current web footer has 2026 copyright, but I did not find an unambiguous revision date for the restriction; use `undated`/date-precision or label 2026 as page-observed copyright year until revision history is documented.

**Post-source verdict:** bibliographic link appropriate after those two metadata clarifications; still **not an AI ingestion or model-training clearance**. The linked source should not become a first-party clinical research paper simply because it is added to the same registry.

**Final limited recheck:** root applied both corrections to the staged `research/rights_sources_wave3.json`, and I reread the file: `date: undated` with the existing conservative precision label, and `source_license: CC BY-NC-SA 4.0 (current web notice; AI ingestion requires written permission)`. The flags `model_training_rights: not-cleared` and `source_content_included: false` are unchanged. These resolve the two metadata objections above **without** clearing the use-rights or clinical-content gates.
