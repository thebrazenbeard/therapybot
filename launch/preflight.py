"""Local stdlib-only dependency check. No network, model load or database I/O."""

import importlib.metadata
import re
import sys


_STABLE_VERSION = re.compile(r"^(\d+)\.\d+(?:\.\d+)?(?:\.post\d+)?$")


def check_runtime():
    if sys.version_info < (3, 10):
        print("TherapyBot needs Python 3.10 or newer", file=sys.stderr)
        return 2
    try:
        version = importlib.metadata.version("cryptography")
    except importlib.metadata.PackageNotFoundError:
        print("Missing local cryptography package; explicitly run launcher setup", file=sys.stderr)
        return 2
    match = _STABLE_VERSION.fullmatch(version)
    if match is None or not 43 <= int(match.group(1)) < 51:
        print(
            f"cryptography {version} does not satisfy local requirement >=43,<51; run launcher setup",
            file=sys.stderr,
        )
        return 2
    print(f"Local Python {sys.version_info.major}.{sys.version_info.minor}; cryptography {version}: ready")
    return 0


if __name__ == "__main__":
    raise SystemExit(check_runtime())
