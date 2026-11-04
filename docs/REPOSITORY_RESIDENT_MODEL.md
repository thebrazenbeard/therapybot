# Repository-resident model: a browser-native TherapyBot

**Status:** Developer-only semantic prototype implemented in `embedded/`; browser GGUF inference is a design proposal, not implemented or clinically qualified. **Date:** 2026-11-04.

## The product requirement, not the file-format assumption

The intended experience is that someone opens TherapyBot's repository-delivered web application and can use its intelligence **without separately installing Python, KoboldCPP, llama.cpp, an API server, or a paid/cloud account**. The repository owns the executable engine, its versioned knowledge/logic, and the distribution manifest for any neural model. The person's own browser runs the engine. GitHub does **not** run inference on behalf of visitors.

“Model lives inside the repo” has several technically different meanings; these must not be silently conflated:

| Interpretation | Possible artifact | What actually executes | Limitation |
| --- | --- | --- | --- |
| Strict Git-tree residence | JavaScript semantic engine, dialogue graphs, small model assets, local source register | Browser JavaScript/Worker/WASM | Large weights bloat Git; Git's 100 MB/object hard limit applies. |
| Repository-owned distribution | Browser engine in Git; versioned GGUF/ONNX assets attached to **the same repository's release**; signed/hashed manifest in Git | Browser after an explicit one-time download | Release assets are not literally tracked inside the Git tree; cross-origin delivery and caching must be tested. |
| Packaged offline artifact | Downloadable ZIP/PWA containing engine and licensed model assets | Browser served from a local static origin | Workers, modules, and service-worker features cannot be assumed to work directly from `file://`. |
| Remote model endpoint | Python local HTTP handler and separate KoboldCPP/llama.cpp | Separate native process | This is the present development route, **not** the required browser-native experience. |

The first three are legitimate ways to ship a *repository-resident application model*; the fourth remains an optional compatibility adapter. A deterministic knowledge/decision model and a trained neural model are different implementations. Do not call a rules-only build an LLM or present it as equally fluent.

## Proposed layered design

1. **Static browser shell:** accessible HTML/CSS, visible capability status, chat transcript in current-session memory, explicit data-export/delete controls, no mandatory account or remote API.
2. **Repository-shipped semantic baseline:** original authored concept graph, conversation-state transitions, local source lookup, reflection/education pathways, refusal/uncertainty handling. It runs with no model-weight download and makes no claim to unrestricted natural-language understanding.
3. **Optional neural backend in the browser:** a Web Worker loads version-locked WASM/WebGPU runtime plus licensed, checksum-verified model assets. [Wllama](https://github.com/ngxson/wllama) is a concrete candidate for GGUF inference through llama.cpp compiled to WebAssembly; [Transformers.js](https://huggingface.co/docs/transformers.js/index) is an alternative for compatible ONNX models. Neither requires a standalone inference server. Wllama supports model splits, progress callbacks, worker execution, single-thread fallback, and optional WebGPU. Selection is contingent on actual Windows/Linux/mobile browser tests.
4. **Optional native adapter:** preserve existing localhost KoboldCPP/llama.cpp for people who deliberately select it; never make it a prerequisite for baseline browser conversation.
5. **Safety and evidence boundary outside the generative adapter:** the dialogue model, source retrieval, output validation, crisis/help routing, and user consent have distinct tests. Generated text cannot be taken as clinical advice or cited evidence merely because an LLM produced it.

The local semantic baseline and optional neural backend must expose a common, narrow interface: `respond({messages, context, mode}) -> {text, engine_id, source_ids, uncertainty, warnings}` (illustrative contract only). The UI must visibly distinguish **semantic-guided response**, **neural-generated response**, and **unavailable/unsupported**. Never silently change to a network inference API, synthesize nonexistent citations, or imply the system remembers a person beyond consented state.

## Model-distribution manifest (proposed, not a committed schema)

Every offered neural engine should have a reviewed, immutable manifest with:

| Field | Purpose |
| --- | --- |
| `engine_id`, `runtime`, `format`, `revision` | Exact runtime/model identification (`wllama`/GGUF or Transformers.js/ONNX). |
| `source_repository`, `release_tag`, `asset_urls` | Where the **same-repository** release assets are obtained; external sources require separate justification. |
| `sha256` per file, `total_bytes` | Integrity verification and honest download size before consent. |
| `license`, `redistribution_rights`, `model_card_url` | Rights gate before a public bundled download. “Publicly downloadable” is not proof of rehosting rights. |
| `memory_estimate`, `backend_requirements`, `supported_devices` | Device suitability and safe failure/fallback. Each claim needs a real runtime probe. |
| `safety_review`, `evaluation_revision`, `release_status` | Separation of model operability from behavioral safety acceptance. |

Do **not** put raw private conversations, personal trauma records, account tokens, clinical notes, or copied third-party research bodies into the repository, release assets, browser cache prepopulation, logs, or model-training corpus. The default model and knowledge base are generic. Personalization is local, off by default, purpose-specific, inspectable, and user-deletable; it is neither bundled into a release nor silently uploaded to GitHub.

## Real constraints, not imagined prohibitions

- [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) hosts static HTML/CSS/JS. [Official Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits): published site at most **1 GB**, recommended source repository **1 GB**, soft **100 GB/month** bandwidth. Distributing several-hundred-MB weights through the Pages site could exhaust those limits rapidly.
- [GitHub repository limits](https://docs.github.com/en/repositories/creating-and-managing-repositories/repository-limits) enforce a **100 MB single Git object** ceiling. Splitting weights can avoid the per-file cap, but not the site-size, bandwidth, or repository-history costs. [Git LFS cannot be used with Pages](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-git-large-file-storage).
- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) currently allow assets **under 2 GiB apiece** and document no total release-size or download-bandwidth limit. Release asset URLs, redirects, and cross-origin fetch support still require end-to-end browser testing; a GitHub release isn't automatically a cross-origin model CDN contract.
- [Wllama](https://github.com/ngxson/wllama) provides browser GGUF inference and splitting. Its WASM multithreaded mode needs COOP/COEP cross-origin-isolation headers; GitHub Pages does not directly let this project configure them. **Single-thread CPU** is a functional fallback, not a performance promise. A [GitHub Pages browser-GGUF proof of concept](https://github.com/hybridgroup/yzma-wasm-example) explores isolation via a service worker, but that implementation must undergo compatibility, provenance, and security review before adoption.
- [WebGPU](https://developer.mozilla.org/en-US/docs/Web/API/WebGPU_API) requires a secure context and is not uniformly available; device support and sufficient RAM/VRAM cannot be inferred merely from a browser version. WebAssembly fallback may be substantially slower. Mobile testing must include modest hardware, failed downloads, interrupted sessions, and storage eviction.
- A service worker is not a server, nor does its cache guarantee permanent offline access. [MDN's PWA caching guidance](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps/Guides/Caching) documents browser storage eviction. `file://` pages do not provide a reliable secure HTTP origin for modules, workers, service workers, and cross-origin model fetches: a downloadable offline bundle should include an explicitly tested minimal local static-server launcher or a vetted installed-PWA route.
- [GitHub Pages usage guidance](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits) warns against sensitive transactions on Pages. Do not assume a public Pages origin is an appropriate private clinical-record vault merely because inference runs client-side. Privacy testing must cover request telemetry, fetch destinations, browser persistence, origin integrity, browser backup behavior, and malicious dependency/CDN substitution.

## Honest user experience

1. Open the browser application: **baseline support/education runs immediately** from local packaged code and authored reference data, with no external inference request.
2. Choose an optional *enhanced language mode*: show exact model name, license, approximate download/storage requirements, hardware requirements, and an explicit **Download and enable on this device** action.
3. Download versioned, integrity-checked assets; verify CORS and complete-file SHA-256 **before load**; cache locally when consented; make cache purge and model switching straightforward.
4. If downloads, GPU initialization, RAM, or browser features fail, retain the baseline and report the actual limitation. Do not conceal failure by forwarding conversation data to a remote model.
5. Permit temporary, unsaved conversation with no account. Encrypt persisted private records only after a separate demonstrated local security design; a static preview must not claim the Python SQLite/Fernet vault has been reproduced in the browser.

## Separation of build phases and release gate

**Already implemented in the working feature branch:** local Python/HTML chat through a loopback GGUF endpoint, a simple retrieval register, local encrypted-record functionality, a **read-only** public Pages preview, and the separate `embedded/` developer-only HTML/JavaScript semantic dialogue prototype. The embedded engine supports bounded topic, intent, and in-memory context matching; it is a deterministic model, **not** a trained language model. Its source-level and Node tests do not establish actual browser accessibility or clinical safety. No Wllama bridge, bundled neural weights, browser-secure personal vault, or repository release-asset manifest has been implemented or verified.

**First developer-only implementation slice:** add the browser semantic engine and a local-hosted interactive HTML harness without publishing interactive Pages; test deterministic source lookup, state transitions, no-remote-fetch behavior, keyboard/screen-reader basics, and explicit no-storage operation. Keep all tests synthetic.

**Second experimental slice:** add a gated Wllama adapter behind a feature flag with a tiny distributable license-cleared GGUF, same-repo release manifest, download consent, checksum verification, offline/caching tests, CPU fallback, and measured device memory/performance. If a claimed source or model license cannot be verified, do not distribute it.

**Independent gates before any public interactive deployment:** repaired and independently evaluated danger routing (existing holdout failures remain open); model-output harm and claim-level grounding evaluations; genuine browser/mobile accessibility; origin/CORS/CSP and dependency threat-model tests; actual storage deletion/recovery and consent tests; rights review; and an explicit owner release decision. Successful HTTP 200, a passing synthetic unit suite, or a working WebGPU demo is not clinical qualification.

> **Hostile challenge:** Merely packaging a model *inside* a repository could satisfy a literal instruction while betraying the intended outcome if users must download gigabytes, expose sensitive data, or receive confidently wrong psychological guidance. The design must test practical access, privacy, evidence, and safety as end-to-end invariants—not just file residence.
