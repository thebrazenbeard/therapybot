"""Validate a source-only, no-CDN browser GGUF bundle manifest.

Structural validation is not a license audit, clinical safety assessment,
browser compatibility check, or proof that vendored JavaScript never fetches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlsplit


MAX_MANIFEST_BYTES = 65536
MAX_ASSETS = 64
MAX_MODEL_PART_BYTES = 512 * 1024 * 1024  # conservative packaging policy
MAX_ASSET_BYTES = 512 * 1024 * 1024
MAX_BUNDLE_BYTES = 4 * 1024 * 1024 * 1024
SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
REVIEWED_WLLAMA_VERSION = "3.8.1"
NAME_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,127}\Z")
ASSET_ROLES = {"runtime-js", "runtime-wasm", "compat-wasm", "compat-worker", "model-part"}
MANDATORY_ROLES = {"runtime-js", "runtime-wasm", "compat-wasm", "compat-worker"}


class ManifestError(ValueError):
    """A manifest or byte-for-byte file claim failed validation."""


def _object(value, fields, required, name):
    if type(value) is not dict:
        raise ManifestError(f"{name}: expected object")
    unknown = set(value) - fields
    missing = required - set(value)
    if unknown or missing:
        raise ManifestError(f"{name}: unknown={sorted(unknown)}, missing={sorted(missing)}")


def _token(value, name, expr):
    if type(value) is not str or not expr.fullmatch(value):
        raise ManifestError(f"{name}: invalid bounded token")


def _sha(value, name):
    _token(value, name, SHA256_RE)


def _path(raw):
    if type(raw) is not str or not (1 <= len(raw) <= 256):
        raise ManifestError("asset.path: invalid string")
    # The manifest cannot authorize remote URLs, rooted paths, path traversal,
    # URL fragments, encoded separators, or Windows-drive prefixes.
    if any(x in raw for x in ("\\", ":", "?", "#", "%", "//")) or raw.startswith("/"):
        raise ManifestError("asset.path: only unencoded relative POSIX paths allowed")
    parts = PurePosixPath(raw).parts
    if not parts or any(p in {".", ".."} or p.startswith(".") for p in raw.split("/")):
        raise ManifestError("asset.path: traversal/hidden/dot component")
    if any(not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", p) for p in parts):
        raise ManifestError("asset.path: invalid component")
    if parts[0] not in {"assets", "vendor"}:
        raise ManifestError("asset.path: must stay under assets/ or vendor/")
    return raw


def _source_url(raw, name, revision=None):
    if type(raw) is not str or len(raw) > 512:
        raise ManifestError(f"{name}: invalid URL")
    try:
        u = urlsplit(raw)
        port = u.port
    except ValueError as exc:
        raise ManifestError(f"{name}: invalid URL") from exc
    # Documentation pointer ONLY. No runtime component reads this URL.
    if (u.scheme != "https" or u.hostname not in {"huggingface.co", "github.com"}
            or u.username or u.password or u.fragment or u.query or port not in {None, 443}):
        raise ManifestError(f"{name}: HTTPS primary-source pointer required")
    if revision is not None:
        parts = u.path.split("/")
        if not any(parts[i] in {"blob", "tree", "resolve"} and parts[i + 1] == revision
                   for i in range(len(parts) - 1)):
            raise ManifestError(f"{name}: source URL must bind exact declared commit")


def validate_manifest(doc, *, require_cleared=False):
    """Check precise schema and conservative no-network/no-autoload policy."""
    _object(doc, {"schema_version", "model", "runtime", "policy", "assets"},
            {"schema_version", "model", "runtime", "policy", "assets"}, "root")
    if type(doc["schema_version"]) is not int or doc["schema_version"] != 1:
        raise ManifestError("schema_version must be exactly integer 1")
    model = doc["model"]
    _object(model, {"id", "source_revision", "source_url", "license_spdx", "license_evidence_url", "rights_clearance"},
            {"id", "source_revision", "source_url", "license_spdx", "license_evidence_url", "rights_clearance"}, "model")
    _token(model["id"], "model.id", NAME_RE)
    _token(model["source_revision"], "model.source_revision", SHA1_RE)
    _source_url(model["source_url"], "model.source_url", model["source_revision"])
    _source_url(model["license_evidence_url"], "model.license_evidence_url")
    if model["license_spdx"] != "Apache-2.0":
        raise ManifestError("model.license_spdx: only verified Apache-2.0 candidates in this experiment")
    if type(model["rights_clearance"]) is not str or model["rights_clearance"] not in {"pending", "reviewed"}:
        raise ManifestError("model.rights_clearance must be pending/reviewed")
    if require_cleared and model["rights_clearance"] != "reviewed":
        raise ManifestError("model rights review not asserted; refuse readiness")

    runtime = doc["runtime"]
    _object(runtime, {"package", "version", "mode"}, {"package", "version", "mode"}, "runtime")
    if runtime["package"] != "@wllama/wllama":
        raise ManifestError("runtime.package: only explicitly reviewed Wllama")
    if runtime["version"] != REVIEWED_WLLAMA_VERSION:
        raise ManifestError(f"runtime.version must be exactly {REVIEWED_WLLAMA_VERSION}")
    if runtime["mode"] != "self-hosted":
        raise ManifestError("runtime.mode must be self-hosted")

    policy = doc["policy"]
    _object(policy, {"offline_after_install", "automatic_download", "external_runtime_fetch", "explicit_download_consent", "conversation_storage_default", "contains_private_data"},
            {"offline_after_install", "automatic_download", "external_runtime_fetch", "explicit_download_consent", "conversation_storage_default", "contains_private_data"}, "policy")
    for k, required in {"offline_after_install": True, "automatic_download": False,
                        "external_runtime_fetch": False, "explicit_download_consent": True,
                        "contains_private_data": False}.items():
        if type(policy[k]) is not bool or policy[k] is not required:
            raise ManifestError(f"policy.{k}: violates no-network/consent boundary")
    if policy["conversation_storage_default"] != "none":
        raise ManifestError("conversation storage must default to none")

    assets = doc["assets"]
    if type(assets) is not list or not 5 <= len(assets) <= MAX_ASSETS:
        raise ManifestError("assets: at least four runtime assets and one GGUF part required")
    roles, paths, total = [], set(), 0
    for i, a in enumerate(assets):
        _object(a, {"role", "path", "sha256", "size_bytes"},
                {"role", "path", "sha256", "size_bytes"}, f"asset[{i}]")
        role = a["role"]
        if type(role) is not str or role not in ASSET_ROLES:
            raise ManifestError(f"asset[{i}].role: unsupported")
        p = _path(a["path"])
        if p in paths:
            raise ManifestError("asset.path: duplicate")
        paths.add(p)
        _sha(a["sha256"], f"asset[{i}].sha256")
        size = a["size_bytes"]
        if type(size) is not int or not 0 < size <= MAX_ASSET_BYTES:
            raise ManifestError(f"asset[{i}].size_bytes: invalid/oversized")
        total += size
        if total > MAX_BUNDLE_BYTES:
            raise ManifestError("bundle exceeds conservative size limit")
        if role in {"runtime-js", "compat-worker"} and not p.endswith(".js"):
            raise ManifestError(f"asset[{i}]: expected .js")
        if role in {"runtime-wasm", "compat-wasm"} and not p.endswith(".wasm"):
            raise ManifestError(f"asset[{i}]: expected .wasm")
        if role == "model-part" and not p.endswith(".gguf"):
            raise ManifestError(f"asset[{i}]: expected .gguf")
        roles.append(role)
    for required in MANDATORY_ROLES:
        if roles.count(required) != 1:
            raise ManifestError(f"exactly one {required} required")
    if not 1 <= roles.count("model-part") <= 16:
        raise ManifestError("model parts must be bounded 1..16")
    return {"assets": len(assets), "total_bytes": total, "model_parts": roles.count("model-part"),
            "rights_self_assertion_required": bool(require_cleared)}


def verify_local_assets(doc, root):
    """Read every bundled file and compare exact length and SHA-256.

    Never fetch URLs, execute JS/WASM, parse GGUF, or follow symlinks.
    """
    validate_manifest(doc, require_cleared=True)
    root = Path(root).resolve(strict=True)
    for a in doc["assets"]:
        path = root.joinpath(*PurePosixPath(a["path"]).parts)
        # Check every lexical component: a directory symlink resolving *within*
        # root is still a symlink and must not satisfy the custody claim.
        if any(ancestor.is_symlink() for ancestor in (path, *path.parents) if ancestor != root and root in ancestor.parents):
            raise ManifestError(f"asset path includes symlink: {a['path']}")
        if not path.is_file() or not path.resolve().is_relative_to(root):
            raise ManifestError(f"asset missing/symlink/outside root: {a['path']}")
        h = hashlib.sha256()
        size = 0
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                size += len(block)
                if size > a["size_bytes"]:
                    raise ManifestError(f"asset exceeds declared bytes: {a['path']}")
                h.update(block)
        if size != a["size_bytes"] or h.hexdigest() != a["sha256"]:
            raise ManifestError(f"asset mismatch: {a['path']}")
    return True


def _unique_pairs(pairs):
    out = {}
    for k, v in pairs:
        if k in out:
            raise ManifestError(f"duplicate JSON key: {k}")
        out[k] = v
    return out


def load_manifest(path):
    path = Path(path)
    if path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ManifestError("manifest exceeds byte limit")
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_unique_pairs)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("manifest")
    ap.add_argument("--verify-files", metavar="BUNDLE_ROOT", help="verify local asset digests, requires asserted rights review")
    args = ap.parse_args()
    try:
        doc = load_manifest(args.manifest)
        result = validate_manifest(doc, require_cleared=bool(args.verify_files))
        if args.verify_files:
            verify_local_assets(doc, args.verify_files)
    except (ManifestError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        ap.exit(2, f"REFUSE: {exc}\n")
    print(json.dumps({"status": "STRUCTURE_VALID" if not args.verify_files else "LOCAL_BYTES_VERIFIED",
                      **result}, sort_keys=True))


if __name__ == "__main__":
    main()
