#!/usr/bin/env python3
"""Verify the explicit lightweight publication inventory, without network or builds."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath


def verify(root: Path) -> dict:
    manifest_path = root / "docs/publication-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seen = set()
    total = 0
    for entry in manifest["files"]:
        name = entry["path"]
        parts = PurePosixPath(name).parts
        if not parts or name.startswith("/") or ".." in parts or "\\" in name or name in seen:
            raise ValueError("Unsafe or duplicate inventory path: " + name)
        seen.add(name)
        path = root.joinpath(*parts)
        if path.is_symlink() or any(p.is_symlink() for p in path.parents if p != root.parent):
            raise ValueError("Symlink in publication path: " + name)
        data = path.read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Published file differs from inventory: " + name)
        total += len(data)
    if manifest.get("schema") != "cpucond-lightweight-publication-v1":
        raise ValueError("Unsupported publication manifest")
    return {"status": "verified", "files": len(seen), "bytes": total,
            "source_head": manifest["source_head"], "base_head": manifest["base_head"],
            "scope": "published file bytes; no GPU execution or formal equivalence proof"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(verify(args.root.resolve()), indent=2))


if __name__ == "__main__":
    main()
