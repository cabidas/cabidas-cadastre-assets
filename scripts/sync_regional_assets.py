#!/usr/bin/env python3
"""Synchronize and verify Gran Santiago Regional PMTiles artifacts into cabidas-cadastre-assets."""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
SRC_TILES_DIR = WORKSPACE_ROOT / "output" / "cadastre_s9_tiles"

REGIONAL_ASSETS = [
    {
        "filename": "cadastre-gran_santiago_regional.pmtiles",
        "expected_sha256": "484aa56314ee104036c87747a6e75509a5e0746ee381e6dc0124f6c9bc0b10fc",
        "expected_size": 4526560,
        "public_path": "/cadastre/cadastre-gran_santiago_regional.pmtiles",
        "source_layer": "parcels",
        "min_zoom": 15,
        "max_zoom": 18,
    },
    {
        "filename": "cadastre-gran_santiago_districts_ref.pmtiles",
        "expected_sha256": "8eef92588d44b915a7be554b7dc2c142edcbb406e0ee62b7969fc65dab1c2e68",
        "expected_size": 194732,
        "public_path": "/cadastre/cadastre-gran_santiago_districts_ref.pmtiles",
        "source_layer": "districts",
        "min_zoom": 9,
        "max_zoom": 15,
    },
]


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_pmtiles_magic(path: Path) -> bool:
    with path.open("rb") as stream:
        magic = stream.read(8)
    return magic == b"PMTiles\x03"


def main() -> int:
    dist_dir = ROOT / "dist" / "cadastre"
    provenance_dir = ROOT / "provenance"
    dist_dir.mkdir(parents=True, exist_ok=True)
    provenance_dir.mkdir(parents=True, exist_ok=True)

    print("=================================================================")
    print("REGIONAL PMTILES ASSET PACKAGING & SYNCHRONIZATION")
    print("=================================================================")
    print(f"Source Directory: {SRC_TILES_DIR}")
    print(f"Target Directory: {dist_dir}")

    staged_archives = []

    for item in REGIONAL_ASSETS:
        src = SRC_TILES_DIR / item["filename"]
        if not src.is_file():
            print(f"ERROR: Source asset not found: {src}", file=sys.stderr)
            return 1

        dest = dist_dir / item["filename"]
        print(f"\n1. Staging {item['filename']}...")
        shutil.copy2(src, dest)

        size = dest.stat().st_size
        actual_sha = sha256_of_file(dest)
        magic_ok = verify_pmtiles_magic(dest)

        print(f"   - Size:     {size} bytes (expected: {item['expected_size']})")
        print(f"   - SHA-256:  {actual_sha}")
        print(f"   - Magic v3: {magic_ok}")

        if size != item["expected_size"]:
            print(f"ERROR: Size mismatch for {item['filename']}!", file=sys.stderr)
            return 1
        if actual_sha != item["expected_sha256"]:
            print(f"ERROR: SHA-256 mismatch for {item['filename']}!", file=sys.stderr)
            return 1
        if not magic_ok:
            print(f"ERROR: Invalid PMTiles magic header for {item['filename']}!", file=sys.stderr)
            return 1

        staged_archives.append({
            "path": f"dist/cadastre/{item['filename']}",
            "public_path": item["public_path"],
            "media_type": "application/vnd.pmtiles",
            "size_bytes": size,
            "sha256": actual_sha,
            "source_layer": item["source_layer"],
            "min_zoom": item["min_zoom"],
            "max_zoom": item["max_zoom"],
        })

    # Copy manifest to provenance
    manifest_src = SRC_TILES_DIR / "cadastre_tiles_manifest.v1.json"
    if manifest_src.is_file():
        provenance_dest = provenance_dir / "cadastre_tiles_manifest_regional.json"
        shutil.copy2(manifest_src, provenance_dest)
        print(f"\n2. Copied regional manifest to {provenance_dest}")

    # Generate regional asset manifest
    regional_manifest = {
        "schema": "cabidas.cadastre_asset.v2",
        "dataset_version": "gran_santiago_2026_s2_s6_release",
        "provenance_manifest": "provenance/cadastre_tiles_manifest_regional.json",
        "archives": staged_archives,
        "delivery": {
            "cache_control": "public, max-age=31536000, immutable",
            "allowed_origins": [
                "https://cabidas.app",
                "https://www.cabidas.app",
            ],
        },
        "coolify": {
            "service_name": "cadastre-assets",
            "container_port": 8080,
            "health_path": "/healthz",
            "memory_limit": "256M",
            "cpu_limit": "1.0",
        },
    }

    manifest_output = ROOT / "asset-manifest-regional.json"
    manifest_output.write_text(json.dumps(regional_manifest, indent=2) + "\n", encoding="utf-8")
    print(f"\n3. Generated regional asset manifest at {manifest_output}")

    print("\n✅ All regional PMTiles assets staged, verified and ready for Coolify/Docker packaging.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
