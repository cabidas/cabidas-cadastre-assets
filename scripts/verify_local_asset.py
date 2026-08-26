#!/usr/bin/env python3
"""Verify the immutable archive against the checked-in delivery manifest."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "asset-manifest.json"


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    archive = manifest["archive"]
    path = ROOT / archive["path"]

    if not path.is_file():
        raise SystemExit(f"missing archive: {path}")

    size = path.stat().st_size
    if size != archive["size_bytes"]:
        raise SystemExit(
            f"size mismatch: expected {archive['size_bytes']}, received {size}"
        )

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        magic = stream.read(8)
        if magic != b"PMTiles\x03":
            raise SystemExit(f"invalid PMTiles v3 header: {magic!r}")
        stream.seek(0)
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)

    actual_sha = digest.hexdigest()
    if actual_sha != archive["sha256"]:
        raise SystemExit(
            f"SHA-256 mismatch: expected {archive['sha256']}, received {actual_sha}"
        )

    print(
        json.dumps(
            {
                "ok": True,
                "path": str(path),
                "size_bytes": size,
                "sha256": actual_sha,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
