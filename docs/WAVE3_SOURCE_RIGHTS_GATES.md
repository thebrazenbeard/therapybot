# External clinical and social-science material: reuse gates (2026-11-04)

**Purpose:** prioritize lawful, traceable *knowledge* for TherapyBot without treating a readable document as automatically authorized model-training data. This is an engineering rights triage, **not legal advice or a license clearance**.

## Checked publisher positions

| Publisher / collection | Primary publisher policy | What the policy says | TherapyBot decision |
| --- | --- | --- | --- |
| US National Institute of Mental Health (NIMH) | <https://www.nimh.nih.gov/site-info/policies> | Unless otherwise indicated, NIMH website/publication **text** is public domain and can be copied/reused with attribution. Images are not reusable; material must not be misleadingly modified or presented as specific treatment advice or endorsement. | Candidate *text-only* public-domain educational reference. Verify each page's exception/ownership, identify exact version and retain attribution. Do not imply NIMH endorsement or model/clinical approval. |
| OpenStax *Psychology 2e* web edition | <https://openstax.org/books/psychology-2e/pages/preface> | The web edition describes CC BY-NC-SA 4.0 **but also explicitly requires prior written OpenStax permission to use the book for LLM training or otherwise ingest it into generative-AI offerings** (current preface's Citation/Attribution section). Art and trademarks have additional conditions. | **LINK ONLY. Do not download/ingest into TherapyBot RAG, prompts or model training** until OpenStax grants written permission or an appropriately qualified rights review resolves the edition-specific terms. Noncommercial intent does not override the publisher's express AI-use notice. |
| World Health Organization (WHO) | <https://www.who.int/about/policies/publishing/copyright> | WHO publishes multiple categories and years of material; rights and applicable CC BY-NC-SA 3.0 IGO terms depend on the publication. | Keep bibliography-only until the **exact edition's** notice, IGO terms and any third-party components have been checked. Never infer universal rights from the WHO domain. |

**Edition conflict requiring resolution:** An older official OpenStax *Psychology 2e* PDF carries a CC BY 4.0 notice, while the currently served web text describes CC BY-NC-SA 4.0 and an explicit generative-AI ingestion restriction. A title match is **not** a version/license match. Record a precise edition, file hash and publisher clarification before relying on any apparently more permissive notice. The present TherapyBot disposition remains **link only**.

## Practical ingestion gates

1. **Identity and provenance:** log exact document URL, title, author/publisher, edition/revision, section, retrieval date, checksum and a saved record of the publisher's applicable rights notice.
2. **Rights by use:** track separate decisions for public GitHub text redistribution, local-only indexing/retrieval, synthetic-example adaptation, model fine-tuning, model redistribution, and generated-output attribution. A single “open access” checkbox is insufficient. **Check AI-ingestion exclusions separately from the generic Creative Commons label.**
3. **Scope:** permit only explicitly approved text. Exclude images, embedded third-party figures, comments, names, trademark assets and personal/private health records by default.
4. **Clinical context:** index source version and limitations; distinguish professional practice guidelines, undergraduate pedagogy, systematic review, observational correlation and opinion. A publication's clinical credibility does not validate chatbot-delivered interventions.
5. **User agency:** no silent ingestion from a person's files, no training on sessions by default, no cloud transfer, and no model-weight files in GitHub.
6. **Revocation/updates:** record how to remove a superseded or disputed item from indexes and future training sets; historical model unlearning cannot be promised.

## Current disposition

The **82 registered external source pointers** remain `model_training_rights: not-cleared` and `source_content_included: false`; this memo does not change those flags. The **62 current examples** were authored synthetically and are candidates for experiments, not a clinically validated instruction dataset. **No third-party publication body or new model weights were imported.**

> **Hostile check:** Even an explicitly public-domain text can be outdated or misapplied. A permissive reuse notice alone says nothing about clinical safety, source-to-answer entailment, or whether a small GGUF model faithfully follows the source.
