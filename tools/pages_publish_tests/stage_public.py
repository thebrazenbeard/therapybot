"""Stage ONLY explicitly reviewed public informational pages for GitHub Pages.

This is a publication boundary, not a clinical or content-safety verifier.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil

PUBLIC_FILES = ('index.html', 'interface-preview.html', 'interface-preview.css')


def stage_public(source: Path, destination: Path) -> tuple[str, ...]:
    """Copy a fixed allowlist; reject symlinks/missing files and unsafe outputs."""
    source = Path(source)
    destination = Path(destination)
    if source.is_symlink() or not source.is_dir():
        raise ValueError('public source must be an ordinary directory')
    real_source = source.resolve(strict=True)
    real_destination = destination.resolve(strict=False)
    if real_destination == real_source or real_source in real_destination.parents:
        raise ValueError('staging destination cannot be inside public source')
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(f'public artifact already exists: {destination}')
    validated = []
    for filename in PUBLIC_FILES:
        candidate = source / filename
        if (candidate.is_symlink() or not candidate.is_file()
                or candidate.resolve(strict=True).parent != real_source):
            raise ValueError(f'public allowlisted file missing or unsafe: {filename}')
        validated.append(candidate)
    destination.mkdir(parents=True, exist_ok=False)
    for filename, candidate in zip(PUBLIC_FILES, validated):
        shutil.copyfile(candidate, destination / filename, follow_symlinks=False)
    return PUBLIC_FILES


def main() -> None:
    parser = argparse.ArgumentParser(description='Stage reviewed public pages only')
    parser.add_argument('--source', default='pages')
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    staged = stage_public(Path(args.source), Path(args.destination))
    print('staged-public-pages=' + ','.join(staged))


if __name__ == '__main__':
    main()
