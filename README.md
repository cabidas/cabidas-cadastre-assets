# Cabidas Cadastre Assets

Dedicated, read-only delivery service for immutable Cabidas PMTiles archives.
The service keeps large geospatial binaries out of application repositories and
serves them with byte-range support, explicit browser CORS, immutable caching,
and a stable public URL.

## Architecture

- Caddy serves one explicitly allow-listed, content-addressed PMTiles archive.
- The container runs as a dedicated unprivileged UID/GID (`10001:10001`) on port `8080`.
- The root filesystem can be mounted read-only; only a small `/tmp` tmpfs is needed.
- Caddy's build image and the minimal Alpine runtime are pinned by version and
  multi-platform digest; the runtime exposes only port `8080`.
- `asset-manifest.json` is the source of truth for filename, size, SHA-256,
  media type, cache policy, and browser origins.
- The PMTiles binary is intentionally ignored by Git and is packaged only into
  the deployable OCI image.

The initial public endpoint is intended to be:

```text
https://assets.cabidas.app/cadastre/cadastre-15b77a85753ceb06.pmtiles
```

## Local verification

Place the immutable archive at the path declared in `asset-manifest.json`, then:

```bash
make verify-asset
make test-container
```

The end-to-end check validates health, full-file SHA-256, PMTiles v3 magic,
`HEAD`, byte ranges, content length/type, ETag, Last-Modified, immutable caching,
allowed-origin CORS, preflight behavior, and rejection of an untrusted origin.

See [docs/OPERATIONS.md](docs/OPERATIONS.md) for release, deployment, rollback,
and onboarding procedures.
