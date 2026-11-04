# TherapyBot embedded conversation lab — developer-only

This folder is a standalone local HTML/JavaScript experiment. It demonstrates
repository-resident conversational *behavior*, not a trained neural LLM,
psychotherapy, diagnosis, crisis assessment, or clinical qualification.

## Open it

1. Clone/download the TherapyBot repository or this development branch.
2. Open `embedded/index.html` directly in a browser. Keep the six assets in
   `manifest.json` together.
3. Try a synthetic, ordinary reflection question. Nothing needs to be installed;
   the browser runs the included JavaScript locally. An internet connection is
   needed only if you deliberately open an external reference link.
4. Optionally create your own Inner Council members using **Manage members**, then select **Convene** or type `Council:`, `Solo <name>:`, `Integrate:`, or `Containment:`. No members are assigned by default; replies remain limited scripted reflections, not multi-agent reasoning.
5. Use **Clear chat** to discard the conversation while keeping the unsaved Council roster in this tab; **Forget all** (with confirmation), refresh, or close the tab to discard both.

There is **no** neural GGUF inference or automatic model download in this slice.
The plan for optional genuine in-browser GGUF via Wllama is in
`../docs/REPOSITORY_RESIDENT_MODEL.md`.

The scripted rules are English-only. Some obvious non-English messages now
receive an explicit limitation notice and cannot enter Inner Council mode;
this is a partial heuristic, **not** a language detector, translation service,
or reliable safety screen. Unsupported messages can still escape detection,
and quoted foreign phrases in English can trigger over-cautious abstention.
Known danger cues take precedence, but the overall risk router remains
unvalidated. Do not infer that a message is safe from a normal route.

## Development checks

```sh
python -m unittest tests.test_embedded_model -v
python -m unittest discover -s tests -q
node --check embedded/engine.js
node --check embedded/council.js
node --check embedded/ui.js
node --check tests/browser_smoke.cjs
```

For a real local Edge browser smoke test, use `node tests/browser_smoke.cjs`
with an existing Puppeteer installation. `PUPPETEER_CORE_PATH` may point to an
installed `puppeteer-core` directory, and `EDGE_EXECUTABLE` to Edge. The test
creates only an ephemeral loopback HTTP listener and an isolated browser profile;
it uses synthetic dialogue and saves screenshots in a task-owned temporary
artifact directory.

The existence or passing of the Edge smoke test does not constitute
cross-browser or assistive-technology qualification.
The risk-routing heuristics are incomplete and must not be used as a safety
classification or a public interactive mental-health service. The published
GitHub Pages preview remains read-only and excludes this folder.

Private trauma records, conversation exports, local personalization, and any
model adapted to identifiable personal material must **never** be bundled in
this distributable folder. Consent for private development is not permission
for public redistribution.
