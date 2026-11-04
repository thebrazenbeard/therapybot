# Sociology evidence, Wave 3 (metadata only)

Research date: 2026-11-04. Author role: sociology research specialist, Team01. Status: **staged for independent source audit**, not clinically approved, not cleared for model training, and not merged into `research/sources.json` by this worker.

## Question and bounded method

Can TherapyBot connect psychological explanations to *housing, employment, discrimination, and community circumstances* without claiming that any population association diagnoses or predicts an individual?

1. Examined `research/sources.json` (51 entries at task start) for existing identifiers and URL/DOI links.
2. Searched for peer-reviewed reviews, cohort studies, and official publication records in four thematic searches. Preferred first-party publisher pages, PubMed citations/abstracts, and NIH PubMed Central records as evidence of source identity and study method.
3. Selected ten **new source pointers**, all with descriptive limitations, publication and retrieval dates, evidence types, original brief summaries, and explicit `model_training_rights: not-cleared`. This phase does not import publication bodies or produce supervised model weights.
4. Ran `python scripts/merge_research_sources.py research/social_sources_wave3.json` without `--apply`, plus local JSON/duplicate checks. Independent audit is still required before main registry integration.

## Source verification ledger

| Batch ID | Peer-reviewed source | Trace for source identity and method | Key methodological caution |
| --- | --- | --- | --- |
| `talmatzky-renter-housing-mental-health-review-2026` | Talmatzky et al., *PLOS ONE*, 2026 | [DOI](https://doi.org/10.1371/journal.pone.0294222), [PubMed 41544000](https://pubmed.ncbi.nlm.nih.gov/41544000/) | Review certainty low–very low; OECD adult renter samples; primarily non-controlled designs |
| `keen-childhood-housing-prospective-2023` | Keen et al., *JAMA Pediatrics*, 2023 | [DOI](https://doi.org/10.1001/jamapediatrics.2023.1733), [PubMed 37338896](https://pubmed.ncbi.nlm.nih.gov/37338896/) | Regional prospective cohort; adjusted associations, not causal attribution |
| `lundstrom-us-precarious-work-meps-2024` | Lundstrom et al., *Preventive Medicine*, 2024 | [DOI](https://doi.org/10.1016/j.ypmed.2024.108090), [PubMed 39098343](https://pubmed.ncbi.nlm.nih.gov/39098343/), [CDC STACKS](https://stacks.cdc.gov/view/cdc/208320) | Self-rated mental health; employed-only U.S. survey; residual confounding |
| `pulford-persistent-precarious-work-review-2022` | Pulford et al., *Journal of Epidemiology & Community Health*, 2022 | [DOI](https://doi.org/10.1136/jech-2022-219292), [PubMed 36137738](https://pubmed.ncbi.nlm.nih.gov/36137738/) | Very low GRADE certainty; reviewer explicitly cautions against causal claims |
| `emmer-experimental-discrimination-meta-2024` | Emmer et al., *Psychological Bulletin*, 2024 | [DOI](https://doi.org/10.1037/bul0000419), [PubMed 38330346](https://pubmed.ncbi.nlm.nih.gov/38330346/) | Experimental immediate effects, limited ecological validity and nonrepresentative samples |
| `wang-young-discrimination-intensive-meta-2026` | Wang et al., *Journal of the American Academy of Child & Adolescent Psychiatry*, 2026 | [DOI](https://doi.org/10.1016/j.jaac.2025.06.007), [PubMed 40541925](https://pubmed.ncbi.nlm.nih.gov/40541925/) | Mixed time-lag results; young people only; observational intensive longitudinal methods |
| `coimbra-racial-discrimination-suicidality-meta-2022` | Coimbra et al., *SSM - Population Health*, 2022 | [DOI](https://doi.org/10.1016/j.ssmph.2022.101283), [PubMed 36387016](https://pubmed.ncbi.nlm.nih.gov/36387016/) | Population associations; **not a person-level suicide prediction or triage rule** |
| `spanos-social-prescribing-referral-review-2025` | Spanos et al., *International Journal of Integrated Care*, 2025 | [DOI](https://doi.org/10.5334/ijic.9127), [PubMed 40862008](https://pubmed.ncbi.nlm.nih.gov/40862008/) | Highly heterogeneous studies; effectiveness of referral pathways remains uncertain |
| `staras-social-identity-prescribing-review-2024` | Staras et al., *Journal of Community & Applied Social Psychology*, 2024 | [DOI](https://doi.org/10.1002/casp.2878), [publisher page](https://onlinelibrary.wiley.com/doi/10.1002/casp.2878) | Mostly uncontrolled UK evaluations; social-identity lens is not an established clinical treatment |
| `reinhardt-social-prescribing-loneliness-review-2021` | Reinhardt et al., *Perspectives in Public Health*, 2021 | [DOI](https://doi.org/10.1177/1757913920967040), [publisher page](https://journals.sagepub.com/doi/10.1177/1757913920967040), [PubMed 34159848](https://pubmed.ncbi.nlm.nih.gov/34159848/) | Only nine studies, heterogeneous measures, insufficient meta-analytic comparability |

## Boundaries, rights and consequences

- These are **index metadata and original paraphrases**, not redistributable training corpora. Every source remains `model_training_rights: not-cleared` and `source_content_included: false`, even if an abstract or full article is publicly readable.
- Avoid inferring clinical condition, socioeconomic class, ethnicity, identity, or dangerousness from a user's disclosure. Ask for context where appropriate; do not treat structural harms as mere cognitive distortions.
- Social prescribing may motivate nonclinical, consent-based local resource discovery, **not** automatic referrals or chatbot-human-connection equivalence. Local availability, affordability, suitability, and safety must be checked before suggestions are actionable.
- This wave supplies social-science provenance for knowledge retrieval and original curriculum design. It supplies **no evidence** that TherapyBot has been clinically tested or that model responses are grounded by these sources.

## Retrieval or verification gaps

- Publisher journal page for Pulford et al. returned HTTP 403 in one web retrieval; PubMed and PubMed Central metadata/abstract were available. Some PubMed openings transiently returned minimal or bot-check pages; search-indexed official abstracts and publisher DOI pages were cross-checked where possible.
- Source license permissions and permitted full-text redistribution/training uses were not researched to legal certainty, and must remain closed until separately documented.
- Independent source identity and claim audits are deliberately left to a different reviewer.
