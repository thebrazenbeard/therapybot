"""Stage allowlisted TherapyBot browser files and optional pinned Wllama 3.8.1 assets."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

LAB = Path(__file__).resolve().parent
REPO = LAB.parents[1]
LAB_FILES = ("index.html", "lab.css", "lab.js", "rules_fallback.js", "neural.js")
RUNTIME_FILES = ("catalog.js", "engine.js", "conversation_adapter.js")
WLLAMA_ASSETS = {
    "@wllama/wllama/esm/index.js": ("runtime/wllama/esm/index.js", "e5506753e41a59c11f61f2c52422045be9fc76e32a7e47f037aaad5df4ec723e"),
    "@wllama/wllama/LICENCE": ("runtime/wllama/LICENCE", "5866e3bd7e3cbd3f7c8bea6efd8a1e7fa7cc8de68c30f428aff7c6584a0fb720"),
    "@wllama/wllama/esm/wasm/wllama.wasm": ("runtime/wllama/esm/wasm/wllama.wasm", "551f13439366eff11e057b1b91fe46a7fdac29d56d67372d4c5f19a549dfe70c"),
    "@wllama/wllama-compat/wasm/wllama.js": ("runtime/wllama-compat/wasm/wllama.js", "2649eeb408988841c372e54805adfa25aed5d02f850c09add78c2f3ac0f3fce1"),
    "@wllama/wllama-compat/wasm/wllama.wasm": ("runtime/wllama-compat/wasm/wllama.wasm", "2db3f67d0bcc19cdf8f14f129e46cab691bff898954808f8a2dc4c586eb5bb68"),
}


def pinned_assets(modules: Path) -> list[tuple[Path, Path]]:
    for package in ("wllama", "wllama-compat"):
        manifest = modules / "@wllama" / package / "package.json"
        if json.loads(manifest.read_text(encoding="utf-8"))["version"] != "3.8.1":
            raise ValueError("Only exact Wllama 3.8.1 is allowed")
    checked = []
    for source, (dest, digest) in WLLAMA_ASSETS.items():
        file = modules.joinpath(*source.split("/"))
        actual = hashlib.sha256(file.read_bytes()).hexdigest()
        if actual != digest:
            raise ValueError("Pinned Wllama asset hash mismatch: " + source)
        checked.append((file, Path(dest)))
    return checked


def build(out: Path, modules: Path | None = None) -> Path:
    target = out.resolve()
    if target.exists() and (not target.is_dir() or any(target.iterdir())):
        raise ValueError("Target must be an empty directory; refusing overwrite")
    if target == LAB or target == REPO or REPO in target.parents:
        raise ValueError("Build output must be outside repository")
    assets = pinned_assets(modules.resolve()) if modules else []
    target.mkdir(parents=True, exist_ok=True)
    (target / "runtime").mkdir()
    for name in LAB_FILES:
        shutil.copyfile(LAB / name, target / name)
    for name in RUNTIME_FILES:
        shutil.copyfile(REPO / "embedded" / name, target / "runtime" / name)
    for source, relative in assets:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="Empty output directory outside repository")
    parser.add_argument("--wllama-node-modules", type=Path, help="Optional verified local npm modules path; no network install")
    args = parser.parse_args()
    print("Staged experimental browser lab at", build(args.out, args.wllama_node_modules))
