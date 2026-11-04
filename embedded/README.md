# TherapyBot embedded conversation lab — developer-only

This folder is a standalone local HTML/JavaScript experiment. It demonstrates
repository-resident conversational *behavior*, not a trained neural LLM,
psychotherapy, diagnosis, crisis assessment, or clinical qualification.

## Open it

1. Clone/download the TherapyBot repository or this development branch.
2. Open `embedded/index.html` directly in a browser. Keep the five assets in
   `manifest.json` together.
3. Try a synthetic, ordinary reflection question. Nothing needs to be installed;
   the browser runs the included JavaScript locally. An internet connection is
   needed only if you deliberately open an external reference link.
4. Use **Clear chat** or close/refresh the tab to discard the in-memory exchange.

There is **no** neural GGUF inference or automatic model download in this slice.
The plan for optional genuine in-browser GGUF via Wllama is in
`../docs/REPOSITORY_RESIDENT_MODEL.md`.

## Development checks

```sh
python -m unittest tests.test_embedded_model -v
python -m unittest discover -s tests -q
node --check embedded/engine.js
node --check embedded/ui.js
```

This code has not been tested across real browsers or assistive technology.
The risk-routing heuristics are incomplete and must not be used as a safety
classification or a public interactive mental-health service. The published
GitHub Pages preview remains read-only and excludes this folder.

Private trauma records, conversation exports, local personalization, and any
model adapted to identifiable personal material must **never** be bundled in
this distributable folder. Consent for private development is not permission
for public redistribution.
