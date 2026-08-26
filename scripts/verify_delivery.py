#!/usr/bin/env python3
"""End-to-end HTTP contract check for a deployed PMTiles asset service."""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "asset-manifest.json").read_text(encoding="utf-8"))
ARCHIVE = MANIFEST["archive"]
ALLOWED_ORIGIN = MANIFEST["delivery"]["allowed_origins"][0]
DISALLOWED_ORIGIN = "https://untrusted.invalid"


def request(url: str, *, method: str = "GET", headers: dict[str, str] | None = None):
    return urllib.request.urlopen(
        urllib.request.Request(url, method=method, headers=headers or {}), timeout=30
    )


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_http_error(
    url: str,
    expected_status: int,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
) -> urllib.error.HTTPError:
    try:
        with request(url, method=method, headers=headers):
            pass
    except urllib.error.HTTPError as error:
        require(
            error.code == expected_status,
            f"{method} {url} returned {error.code}, expected {expected_status}",
        )
        return error
    raise AssertionError(f"{method} {url} unexpectedly succeeded")


def wait_for_health(url: str, timeout_seconds: float = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            with request(url) as response:
                require(response.status == 200, f"health returned {response.status}")
                require(response.read() == b"ok", "unexpected health response")
                return
        except (AssertionError, urllib.error.URLError) as error:
            last_error = error
            time.sleep(0.25)
    raise AssertionError(f"health did not become ready: {last_error}")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: verify_delivery.py BASE_URL")

    base_url = sys.argv[1].rstrip("/")
    asset_url = base_url + ARCHIVE["public_path"]

    wait_for_health(base_url + "/healthz")

    with request(asset_url, method="HEAD", headers={"Origin": ALLOWED_ORIGIN}) as response:
        headers = response.headers
        require(response.status == 200, f"HEAD returned {response.status}")
        require(headers.get_content_type() == ARCHIVE["media_type"], "wrong media type")
        require(headers.get("Content-Length") == str(ARCHIVE["size_bytes"]), "wrong size")
        require(headers.get("Accept-Ranges", "").lower() == "bytes", "missing byte ranges")
        require(headers.get("ETag") is not None, "missing ETag")
        require(headers.get("Last-Modified") is not None, "missing Last-Modified")
        require(headers.get("Cache-Control") == MANIFEST["delivery"]["cache_control"], "wrong cache policy")
        require(headers.get("Access-Control-Allow-Origin") == ALLOWED_ORIGIN, "wrong CORS origin")
        require("Content-Range" in headers.get("Access-Control-Expose-Headers", ""), "range header is not exposed")
        require(headers.get("Content-Encoding") is None, "archive must not be transfer-compressed")
        etag = headers["ETag"]

    with request(
        asset_url,
        headers={"Origin": ALLOWED_ORIGIN, "Range": "bytes=0-127"},
    ) as response:
        body = response.read()
        require(response.status == 206, f"range returned {response.status}")
        require(len(body) == 128, f"range returned {len(body)} bytes")
        require(body[:8] == b"PMTiles\x03", "invalid PMTiles v3 header")
        require(
            response.headers.get("Content-Range") == f"bytes 0-127/{ARCHIVE['size_bytes']}",
            "wrong Content-Range",
        )

    with request(
        asset_url,
        method="OPTIONS",
        headers={
            "Origin": ALLOWED_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Range",
        },
    ) as response:
        require(response.status == 204, f"preflight returned {response.status}")
        require(response.headers.get("Access-Control-Allow-Origin") == ALLOWED_ORIGIN, "preflight CORS failed")

    with request(asset_url, method="HEAD", headers={"Origin": DISALLOWED_ORIGIN}) as response:
        require(response.headers.get("Access-Control-Allow-Origin") is None, "untrusted origin was allowed")

    not_modified = require_http_error(
        asset_url,
        304,
        method="HEAD",
        headers={"Origin": ALLOWED_ORIGIN, "If-None-Match": etag},
    )
    require(
        not_modified.headers.get("Access-Control-Allow-Origin") == ALLOWED_ORIGIN,
        "304 response lost CORS policy",
    )

    require_http_error(base_url + "/cadastre/", 404)
    require_http_error(base_url + "/cadastre/not-allow-listed.pmtiles", 404)
    require_http_error(asset_url, 405, method="POST")
    require_http_error(
        asset_url,
        416,
        headers={"Origin": ALLOWED_ORIGIN, "Range": "bytes=999999999-"},
    )

    digest = hashlib.sha256()
    with request(asset_url, headers={"Origin": ALLOWED_ORIGIN}) as response:
        require(response.status == 200, f"GET returned {response.status}")
        while chunk := response.read(1024 * 1024):
            digest.update(chunk)
    require(digest.hexdigest() == ARCHIVE["sha256"], "delivered archive SHA-256 mismatch")

    print(
        json.dumps(
            {
                "ok": True,
                "asset_url": asset_url,
                "sha256": digest.hexdigest(),
                "size_bytes": ARCHIVE["size_bytes"],
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, urllib.error.URLError) as error:
        raise SystemExit(f"delivery verification failed: {error}") from error
