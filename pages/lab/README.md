# TherapyBot private browser conversation lab — source-only, release HOLD

This is an **unreleased experiment**, not a therapist, crisis service, or qualified safety classifier. Rules-based conversation is the default. Only after the visitor explicitly checks a 105 MB consent box and clicks the model-load button does it attempt an experimental local neural model. No account, API key, or visitor installation is required for a hypothetical published static page. **Do not merge into the published Pages tree** until separate release approval; the current Pages workflow could publish the lab if merged.

## Reproducible isolated build

From the repository root, stage the rules-only/default UI into a new empty directory outside Git:

    py -3 pages/lab/build_preview.py --out D:\temp\therapybot-lab-preview

To include the exact self-hosted Wllama 3.8.1 dependencies, supply a local npm installation (no network access or npm install is performed by the builder):

    py -3 pages/lab/build_preview.py --out D:\temp\therapybot-neural-preview --wllama-node-modules D:\path\tools\neural_poc\node_modules

Then serve the staged directory with an isolated loopback-only HTTP server. A browser opening the page downloads its static assets from that server; **it does not download model weights on page load**. If the 4 pinned neural runtime assets are missing, a model-load click fails before a 105 MB transfer.

The builder copies only four UI files, three approved browser runtime JavaScript files, and, when requested, four exact SHA-256-checked Wllama assets. It never includes GGUF weights, Python backend code, data/vault files, credentials, or private trauma history. The build directory must be empty; the script refuses overwriting existing contents.

## Model provenance and privacy boundaries

- **SmolLM2-135M-Instruct Q4_K_M:** pinned quantization revision `a6b7826ed969c3926a98359e39912af137b464cb` from QuantFactory. Exact file size **105,454,144 bytes** and SHA-256 `8030f04528538d47bda434f6f0bdf3952c40a58123e4d5e755332f23731a8684`. Underlying [HuggingFaceTB/SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct) is Apache-2.0; review quantizer provenance at [QuantFactory](https://huggingface.co/QuantFactory/SmolLM2-135M-Instruct-GGUF).
- **Engine:** `@wllama/wllama@3.8.1` and `@wllama/wllama-compat@3.8.1`, MIT-licensed, from [ngxson/wllama](https://github.com/ngxson/wllama). The four staged ESM/WASM/worker files are pinned to exact local hashes in `build_preview.py`. Explicit compat asset paths prevent fallback to a runtime CDN.
- **Opt-in transfer:** direct `fetch` with `cache:'no-store'`, exact byte count, exact SHA-256 before `loadModel([verified File])` with single-thread CPU settings. Do **not** substitute Wllama `loadModelFromUrl`: its default model manager can use persistent browser storage.
- **Actual network:** page assets are fetched locally; a consented model download contacts Hugging Face and its CDN and discloses normal network metadata such as an IP address to those services. The model is held in browser memory. The application does not call CacheStorage/IndexedDB/localStorage to retain model weights or conversations, but the browser may cache its static JavaScript/WASM.
- **CSP:** this page has a *meta* Content Security Policy for local scripts, WASM/worker, local requests and pinned Hugging Face/CDN network hosts. It is not a verified production HTTP security-header policy or proof of CORS success on a future Pages origin.

## Tests and release gate

    py -3 -m unittest discover -s pages/lab -p 'test_*.py' -v
    node pages/lab/test_browser_turn.cjs
    node pages/lab/test_edge_cdp.cjs <edge-debug-port> <loopback-url>
    node pages/lab/test_firefox_bidi.cjs <firefox-bidi-port> <loopback-url>

Browser tests require independently started **isolated** Edge/Firefox debugging profiles. They use synthetic prompts, avoid model downloads, exercise keyboard submission, stop/pause, clear/focus, immediate-help routing, and record actual page network requests. The optional neural-click test intentionally makes a **105 MB external transfer** and must not run on resource-starved hardware or concurrently with other model tests. For offline/error tests, block the pinned external hosts and verify fail-closed behavior first.

**Hard limitations:** The deterministic urgent-help path is neither clinically validated nor comprehensive. It can miss dangerous indirect cases or misread hypothetical language; independent earlier holdouts found severe context failures. A 135M neural model proves only token generation, not conversational competence or therapy safety. Stop/pause discards eventual stale results; it may not immediately abort already-running WASM generation. Explicit source, browser tests, blinded reviews, and separate release authorization are required. **No public deployment, merge or clinical claim is authorized by this branch.**
