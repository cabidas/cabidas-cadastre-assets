#!/usr/bin/env python3
"""Verify every immutable archive before publication or against the live origin."""
from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify(root: Path = ROOT, base_url: str | None = None) -> dict:
    manifest = json.loads((root / "asset-manifest-active.json").read_text())
    checked = []
    for asset in manifest["assets"]:
        if base_url:
            url = base_url.rstrip("/") + asset["public_path"]
            with urllib.request.urlopen(urllib.request.Request(url, headers={
                "Range": "bytes=0-127", "Origin": "https://cabidas.app"
            }), timeout=30) as response:
                assert response.status == 206, "Range not supported"
                assert response.read()[:8] == b"PMTiles\x03"
                assert response.headers["Content-Range"] == f"bytes 0-127/{asset['size_bytes']}"
                assert response.headers["Access-Control-Allow-Origin"] == "https://cabidas.app"
                assert response.headers["Cache-Control"] == "public, max-age=31536000, immutable"
            with urllib.request.urlopen(url, timeout=90) as response:
                body = response.read()
        else:
            body = (root / asset["path"]).read_bytes()
        assert len(body) == asset["size_bytes"], f"Size mismatch: {asset['path']}"
        assert hashlib.sha256(body).hexdigest() == asset["sha256"], f"Hash mismatch: {asset['path']}"
        checked.append(asset["public_path"])
    return {"ok": True, "dataset_version": manifest["dataset_version"], "verified_assets": checked}


if __name__ == "__main__":
    print(json.dumps(verify(base_url=sys.argv[1] if len(sys.argv) > 1 else None)))
