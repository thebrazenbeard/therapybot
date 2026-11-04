# TherapyBot wave 3 — independent sociology research audit

## Frozen audit plan (2026-11-04, before source retrieval)

**Question:** Are the ten proposed social-science source pointers sufficiently accurate, rights-conservative and non-overstated to merge **as bibliographic metadata only**?

- **H1 (structural, confirmatory):** all ten records match existing source schema, retain third-party training rights as `not-cleared`, include no copied source bodies and avoid duplicate IDs/URLs within the batch and 51-source baseline. **Falsifier:** one violating record.
- **H2 (bibliographic, confirmatory):** a purposeful sample of at least five records has correct article/report title, publication year, DOI/publisher URL and evidence-type classification. **Falsifier:** one material mismatch, which must be named; the unsampled five remain unverified at this level.
- **H3 (inference control, confirmatory):** descriptions distinguish observational associations, randomized experiments, systematic review heterogeneity and low evidence certainty; no study is presented as causal proof of an individual case or chatbot clinical outcome. **Falsifier:** material overclaim in any of the ten metadata descriptions.

**Methods:** read the current staged batch, method note and 51-source register; check all ten mechanically; retrieve primary journal/DOI/publisher pages for at least five diverse studies; scrutinize summaries, limitations and dates; report exact evidence ceilings. No source full-text ingestion or user data. **Stopping rule:** all ten structural checks and at least five externally inspected records, with each finding assigned a disposition. Additional lookups are exploratory.

**Evidence log:** append results below without changing this frozen plan.

## Evidence log — post-retrieval

**E1 — all ten records: structural / duplicate checks.** Exact shell command (repository root):

```sh
jq -se '(.[0]+.[1]) as $r | ($r|length) == (([$r[].id]|unique)|length) and ($r|length) == (([$r[].url|ascii_downcase]|unique)|length) and (.[1] | length == 10 and all(.[]; (.model_training_rights=="not-cleared" and .source_content_included==false and (.topics|type)=="array" and (.summary|type)=="string" and (.limitations|type)=="string")))' research/sources.json research/social_sources_wave3.json
```

Exit code `0`; decisive output `true`. The 10 new IDs and HTTPS DOI URLs do not duplicate each other or the previous 51 records. The source batch SHA-256 at audit was `cfcf8ffc2a22b999a54234047ad65ba3f27ad20f0807a7bf02ce76e9c283317c`; method note SHA-256 was `306b8a5d4c3072d72015fa05cff1583f6dff9e3571bbf00c77ca2bf2d6524b84`. This verifies only syntax and explicit rights declarations, not actual licensing.

**E2 — housing.** Original publisher [PLOS ONE article](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0294222) and [PubMed PMID 41544000](https://pubmed.ncbi.nlm.nih.gov/41544000/) match Talmatzky et al., 2026, DOI `10.1371/journal.pone.0294222`, renter housing systematic review. The reported low-to-very-low GRADE certainty and predominance of uncontrolled studies are supported at abstract level. [PubMed PMID 37338896](https://pubmed.ncbi.nlm.nih.gov/37338896/) independently confirms Keen et al., JAMA Pediatrics, August 2023, Great Smoky Mountains prospective cohort, with adjusted **associations**, not individual causal attribution.

**E3 — employment.** [CDC STACKS primary government deposit](https://stacks.cdc.gov/view/cdc/160723) and [PubMed PMID 39098343](https://pubmed.ncbi.nlm.nih.gov/39098343/) agree with Lundstrom et al., *Preventive Medicine* volume 186, September 2024, DOI `10.1016/j.ypmed.2024.108090`, MEPS nationally representative employed-worker analysis. Authors and measured self-rated outcome align with the staged synopsis. [PubMed PMID 36137738](https://pubmed.ncbi.nlm.nih.gov/36137738/) independently confirms Pulford et al., 2022, review and meta-analysis of 50 studies, **very low GRADE certainty** and explicitly uncertain causality. The journal's DOI landing page returned HTTP 403 in this channel; this is an access limitation, not a negative scientific result.

**E4 — discrimination.** [PubMed PMID 38330346](https://pubmed.ncbi.nlm.nih.gov/38330346/) matches Emmer, Dorn and Mata, *Psychological Bulletin*, March 2024, DOI `10.1037/bul0000419`, 73 experimental studies; immediate lab effects and poor population representativeness are accurately limited. [PubMed PMID 40541925](https://pubmed.ncbi.nlm.nih.gov/40541925/) matches Wang et al., *JAACAP* **May 2026 issue** (online June 2025), DOI `10.1016/j.jaac.2025.06.007`, intensive-longitudinal youth review. [PubMed PMID 36387016](https://pubmed.ncbi.nlm.nih.gov/36387016/) matches Coimbra et al., online **November 3, 2022** (December issue), DOI `10.1016/j.ssmph.2022.101283`, a review of population associations with suicidal ideation/attempts. The staged record appropriately forbids using these associations for individual risk scores.

**E5 — social prescribing.** [PubMed PMID 40862008](https://pubmed.ncbi.nlm.nih.gov/40862008/) matches Spanos et al., *International Journal of Integrated Care*, August 19, 2025, DOI `10.5334/ijic.9127`; the study evaluated 30 empirical studies with heterogeneous pathways and inconclusive effect claims. [Wiley publisher record](https://onlinelibrary.wiley.com/doi/10.1002/casp.2878) matches Staras et al., first published August 26, 2024, UK-only social-identity prescribing review, mostly mixed methods/qualitative evaluations; causality is not proven. [PubMed PMID 34159848](https://pubmed.ncbi.nlm.nih.gov/34159848/) matches Reinhardt et al., June 23, 2021 electronic publication, review of nine eligible studies on loneliness outcomes. The staged summary correctly distinguishes reported benefits from reliable causal effect estimates.

**Retrieval record:** All sources above were looked up on 2026-11-04 through primary publisher, DOI, government deposit or original PubMed records. Web retrieval references also include `turn94search3`, `turn96view2`, `turn100search0`, `turn100search1`, `turn100search2`, `turn103search0`, `turn103search1`, `turn103search2`, `turn109view0`, and `turn109view1`. URLs are supplied because tool reference IDs are not durable outside this session.

## Findings and decision

1. **H1 — confirmed structurally (E1):** ten distinct new, HTTPS bibliographic pointers, no copied source bodies, each explicitly says model-training rights **not cleared**. No actual rights grant was independently established.
2. **H2 — confirmed at bibliographic/abstract level (E2–E5):** all ten proposed titles, article identities, DOI and publication-year labels are supported by original source records; several use defensible online versus issue-date distinctions. I found **no material title/year/DOI correction** requiring exclusion. This does not establish line-by-line support from full papers.
3. **H3 — confirmed at the short-summary level (E2–E5):** the ten original summaries and limitations retain uncertainty about causation, representativeness, effect estimates and individual prediction. The strongest direct experimental claim (Emmer) remains bounded to short-term laboratory manipulations.

> **Hostile residual finding (HIGH, certainty):** Topical association is **not source-to-answer entailment**. A future chatbot could cite one of these studies to excuse a false clinical inference or tell a worker that a survey proves an individual diagnosis. Neither bibliographic metadata nor a peer-reviewed study licenses such a leap.

> **Hostile residual finding (HIGH, rights):** Publicly accessible abstracts, PMCID records and a first-party DOI do **not automatically clear full-text redistribution or language-model training**. Preserve `model_training_rights: not-cleared` until separate source-specific clearance; do not fetch/commit full article bodies.

> **Hostile residual finding (MEDIUM, method):** High heterogeneity, low GRADE certainty, selection bias and observational design require careful wording whenever TherapyBot discusses housing, work, discrimination and community-based supports. Do not silently treat social prescribing as an established clinical treatment or let demographic identity drive suicide-risk judgments.

**Independent reviewer verdict: PARTIALLY CONFIRMED.** The batch is **acceptable to merge as bibliography pointers with original short paraphrases only**, with attribution, source status and limitations preserved. It is **not** confirmed as a training corpus, evidence-grounded generated answers, clinical efficacy or license-cleared redistribution. The author did not participate in this independent review; this is an AI technical/source review, not professional human peer review. No source batch or runtime file was edited during audit.
