"""Stage the public-lab UI with explicitly allowlisted local browser runtime JS."""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path

LAB = Path(__file__).resolve().parent
REPO = LAB.parents[1]
LAB_FILES = ("index.html", "lab.css", "lab.js")
RUNTIME_FILES = ("catalog.js", "engine.js", "conversation_adapter.js")


def build(out: Path) -> Path:
    target = out.resolve()
    if target.exists() and any(target.iterdir()):
        raise ValueError("Target must be an empty directory; refusing overwrite")
    if target == LAB or target == REPO or REPO in target.parents:
        raise ValueError("Build output must be outside repository")
    target.mkdir(parents=True, exist_ok=True)
    (target / "runtime").mkdir()
    for name in LAB_FILES:
        shutil.copyfile(LAB / name, target / name)
    for name in RUNTIME_FILES:
        shutil.copyfile(REPO / "embedded" / name, target / "runtime" / name)
    return target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New empty directory outside repository")
    args = parser.parse_args()
    print("Staged rules-only lab at", build(args.out))
