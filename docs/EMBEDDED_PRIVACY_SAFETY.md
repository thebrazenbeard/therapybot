# Repository-resident TherapyBot: privacy, consent, and safety boundary

**Status:** Design and hostile-review requirements, **not** implementation verification, clinical qualification, or release approval.
**Date:** 2026-11-04.
**Scope:** A conversational engine or actual model distributed as part of TherapyBot's repository, including browser-executable JavaScript/WASM, bundled model data, or a packaged local runtime.
**Review method:** `MODEL_SEMANTIC_CANDIDATE` (manual Lou-Pole-style reasoning); **not** a deterministic FreeRowCochkar result or independent clinical review.

## The protected outcome

The user's correction is about **where a working model lives and how it reaches the HTML interface**: the repository should be able to contain the runnable conversational capability rather than merely document an external GGUF service that must be separately configured. The word *model* does not by itself settle whether the implementation consists of bundled neural weights, deterministic rules, retrieval, a semantic graph, WebAssembly, or a composition of these.

The invariant is stronger than the packaging label:

> A person should be able to obtain the honestly advertised local functionality without paid infrastructure, undisclosed network inference, or compulsory installation of an unrelated model server; sensitive information should remain under that person's explicit control; and the product must not imply clinical reliability it has not demonstrated.

Repository-resident **code** is not automatically repository-resident **inference**. A webpage that downloads weights from another origin on first use or calls a separate model server may be useful as an optional adapter, but cannot truthfully claim to be fully self-contained or necessarily offline. Encoding weights in JavaScript does not change their licensing, redistribution rights, memory footprint, or potential to reveal training data.

## Consent is purpose- and distribution-specific

**Data authorization boundary:** When an owner explicitly permits their personal material to be used for private development or training, that consent is purpose-specific. It **does not** authorize public GitHub publication, distribution inside repository assets or website bundles, sharing through PRs/issues, or inclusion in publicly downloadable weights or adapters. It does not grant rights over independently identifiable third parties mentioned in those records or third-party copyrighted source material. Keep individual consent records private.

Do not silently convert this permission into ongoing collection of new conversations, general model-provider uploads, unrelated ecosystem training, redistributable datasets, or publication. If a proposed use goes beyond authorized development/training, obtain a separate decision before proceeding.

| Data class | Examples | Permitted custody and handling | Public repository or Pages |
| --- | --- | --- | --- |
| **Private source** | Original trauma record, chat exports, personal notes, names and contextual identities | Only within an authorized private local workspace or encrypted personal store; least-privilege access; no automatic logging | **Never** |
| **Private derived material** | Extracted facts, embeddings, personalization indexes, tuned adapters or checkpoints that could memorize the source | Private and consent-scoped; treat as sensitive until demonstrated otherwise; separate storage from published artifacts | **Never by default** |
| **Quarantined candidates** | De-identified synthetic examples and aggregate abstractions derived from sensitive sources | Human/independent review for identity leakage, unique combinations, third-party privacy and provenance; keep an auditable promotion decision | **Not until approved** |
| **Distributable generic material** | Original generic conversation flows, licensed reference metadata, reviewed nonpersonal examples, audited public model artifacts | Repository only after explicit license/provenance, privacy, security, and release checks | **Conditional** |

Names removed from a distinctive life narrative can still leave a recognizable combination of dates, relationships, events and language. A vector embedding, paraphrase, LoRA, quantized or encoded model file is not proof of anonymization. Model extraction or memorization may reproduce fragments even when raw input files are absent from the build.

The user's preference for keeping large model artifacts on VN1/VN2 and code/manifests/checksums in GitHub remains a separate *storage-policy* constraint unless expressly changed. A publicly distributed generic small browser model might eventually justify an exception, but never by silently embedding private learned data.

## Trust boundaries for the architecture

1. **GitHub and public Pages:** Public repository files and deployed website assets are indefinitely copyable. Git history, CI logs, release artifacts, browser caches, and external mirrors may retain material after deletion. The current Pages build intentionally ships the informational `pages/` preview only; it must not expose the existing local `static/index.html` vault/API client as a drop-in public page. A Pages origin is not the existing loopback server. No public interactive release is presently authorized.
2. **Browser-executable engine:** A developer-only browser model may run locally, but it is still executable code supplied by a website or local file. No external inference, analytics, font/CDN libraries or prompt-sending API calls may be hidden behind a "local" label. Conversation text should live in memory by default, not `localStorage`, IndexedDB, a service worker cache, a URL/query string or telemetry. Use `textContent` for untrusted text, explicit same-origin/Content-Security-Policy restrictions, bounded input, and a network-observable offline test.
3. **Local application and vault:** The existing loopback application has token, origin, and encrypted-vault boundaries. Do not bypass them by importing its relative `/api/` paths into GitHub Pages. Opt-in encrypted records need explicit unlock, deletion/backup semantics, and a real readback/restore test; browser-only storage requires a fresh threat model, not an assumed equivalence to the Python vault.
4. **Optional local inference:** KoboldCPP/llama.cpp/GGUF adapters may remain optional. A separately installed model's logging, weights provenance, safety behavior and network access are independent from TherapyBot's controls. A port-response test qualifies protocol connectivity only.
5. **Research and training material:** Bibliographic metadata and short authored summaries are not permissions to copy article bodies or train on third-party content. Distinguish `SOURCE`, `TRAINING_RIGHT`, `RETRIEVAL_RELEVANCE`, and `CLAIM_SUPPORT` in reports and the UI. Personal trauma data must not be folded into general training/evaluation fixtures under a euphemistic "synthetic" label.

## Hostile counterexamples (semantic candidates)

> **Distribution laundering:** A developer promises the model "lives inside the repository," then commits an encoded adapter fine-tuned on recognizable trauma text. The literal packaging claim is met while the privacy invariant fails. **Hardening:** Generic published engine and private personalized artifacts must be separated by build inputs and inspectable artifact manifests, followed by leakage tests.

> **Dependency laundering:** A lightweight repository web page secretly downloads a several-gigabyte model or calls a remote inference endpoint. The source resides in the repository, but the claimed stand-alone offline experience does not. **Hardening:** Name the actual residency of code, weights, and execution separately; test from a disconnected machine and measure first-run resource requirements.

> **Safety laundering:** A deterministic semantic engine works without weights and is called "model-independent," then supplies confident but unsupported advice when encountering a novel crisis statement. The absence of generative hallucinations does not establish appropriate response handling. **Hardening:** Evaluate the full dialogue outcome, including false reassurance, false escalation, unsupported diagnosis, cultural misreading, and bad source attribution.

> **Origin laundering:** A working local chat HTML file is copied into `pages/`. Its relative `/api/chat` and vault paths now target the public Pages origin; entering sensitive text is no longer meaningfully equivalent to the local server's data path. **Hardening:** Preserve the read-only Pages publication boundary until separate, verified browser-only implementation and explicit release authorization exist.

> **Consent laundering:** Development permission for a person's own trauma history is interpreted as permission to make a de-identified benchmark public. A rare event sequence or stylistic quote makes the person or others recognizable. **Hardening:** Quarantine derived data, check for overlap and unusual combinations, obtain an explicit publication decision, and publish no private examples in tests or review comments.

These are **model-generated review hypotheses**. They describe plausible failure paths from source and architecture, not observed disclosures, deterministic graph reachability, proven exploitation, or clinical findings.

## Minimum gates before private-data training

- Record exact data source, owner consent, allowed purpose, retention location, intended outputs, and recipients **without copying personal content into an issue or log**.
- Make the collection and processing opt-in and reversible where practicable; do not automatically ingest unrelated directories, cloud backups, family files, or further chats.
- Separate train/development/evaluation material and avoid test contamination; keep direct quotes and recognizable paraphrases out of general test fixtures.
- Require source-rights and third-party-person checks. A data subject can authorize use of their own material, not another person's copyright or confidentiality.
- Inspect all candidate artifacts for exact-string matches, near-duplicates, distinctive combinations of facts, and adversarial elicitation of training memories. Record limitations: finite negative tests do **not** prove non-memorization.
- Qualify the storage and build chain: git staging/diff, CI artifact contents, generated bundle, browser cache and logs, backup paths, and adapter/model-export destinations. No credentials, private source, or derived identifiable data in distributable artifacts.
- Keep personalization strictly optional; normal functioning must not demand sensitive disclosures or a stored personal history.

## Independent gates before any interactive public release

The owner explicitly holds **general-public interactive release** until safety/privacy/accessibility defects are resolved. Private synthetic development and a noninteractive public preview remain distinct categories. A repository-resident engine does not waive that hold.

| Gate | Required evidence |
| --- | --- |
| Actual self-contained runtime | Fresh install/disconnected developer-only end-to-end conversation, model execution on claimed host/browser, memory/storage profile, and inspected network requests; no hidden remote fallback |
| Input-risk and response behavior | Fresh independent and blinded adversarial prompts across direct/indirect risk, negation, roleplay-to-personal transition, ordinary distress, cultural context, and multiple languages; document false reassurance and false escalation |
| Generated **and** deterministic answer safety | Tests of unsupported diagnosis, unsafe reassurance, manipulative dependency, extraordinary causal certainty, hallucinated or misrepresented citations; safe failure if uncertain |
| Provenance and licensing | Asset-by-asset licenses, rights to distribute bundled weights and snippets, hash-bound exact assets, claim-level citation review |
| Privacy and security | Host/browser network tracing, origin/CSP, user-data retention, code-injection resistance, export/restore, backup/cache/deletion limits, plus private-data leakage and model-extraction probes |
| Accessible usability | Actual keyboard/screen-reader/mobile/narrow-width testing, visible opt-in persistence, clear capability/failure labels, no requirement to install a server merely to view the interface |
| Governance | Independent reviewers (identity/provider/runtime and artifact SHA preserved), unresolved findings recorded, explicit owner release authorization after evidence—not inferred from test counts or an agent vote |

**Current known blocker:** On 2026-11-04, an independent developer-authored strict canary replay on the local `therapybot` tree returned **3/8 expected routes (exit 1)**. Existing fake-model experiments demonstrate unscreened unsafe completion propagation. These are characterization results, **not** clinical sensitivity estimates. The public release hold remains non-negotiable while these faults persist.

**Additional embedded-prototype finding:** Independent read-only review of the first browser engine revision matched only **9/23** separately authored synthetic danger-route expectations. Several immediate threats, ingestions, third-person emergencies, and partner assaults were missed, while historical or fictional statements sometimes escalated. A narrow follow-up repair of additional partner-assault wording does **not** convert this heuristic into a clinically qualified classifier; fresh held-out evaluation and substantially stronger safety design are still required.

## Implementation recommendation

Keep the repository's **generic, inspectable, executable conversational capability** separate from the **optional sensitive personalization layer**. Permit browser-native deterministic or compact-weight engines when they demonstrably run as advertised, support a non-persistent chat session, and have explicit limitations. Maintain local GGUF as an optional alternative, not the only definition of "model." Never use semantic relabeling to bypass licensing, disclosure, clinical review, or release consent.
