# Operations runbook

## Release invariant

An archive URL is immutable. Never replace bytes at an existing public path or
reuse a dataset version. Any changed archive receives a new content-derived
version, manifest entry, image tag, and URL.

## Build and publish

1. Generate the PMTiles archive through the controlled cadastre pipeline.
2. Copy it to the manifest's local `archive.path` (the `dist/` tree is ignored).
3. Run `make verify-asset` and `make test-container`.
4. Authenticate Docker to the chosen OCI registry through the operator's normal
   credential flow.
5. Publish with `scripts/publish_image.sh ghcr.io/cabidas/cadastre-assets`.
   The build targets the Coolify server's `linux/amd64` architecture and emits
   OCI provenance plus an SBOM attestation.
6. Resolve and record the resulting immutable image digest.
7. Configure Coolify with the digest, not `latest`.

Publishing credentials belong in the operator's credential store or CI secret
manager. They must never be committed, printed, or entered as Docker build args.

## Coolify candidate

Create a separate Docker-image resource and expose container port `8080`.
`compose.example.yaml` is the reviewed runtime-policy reference; if the Coolify
UI is used directly, its settings must remain equivalent.
Before attaching public DNS, apply:

- read-only root filesystem;
- `/tmp` tmpfs with a 16 MiB limit;
- all Linux capabilities dropped;
- `no-new-privileges`;
- one CPU and 256 MiB memory as initial ceilings;
- restart policy `unless-stopped`;
- health endpoint `/healthz`;
- JSON logs with rotation at the platform level.

First validate through Coolify's temporary hostname:

```bash
python3 scripts/verify_delivery.py https://<candidate-hostname>
```

Only after this passes should `assets.cabidas.app` be attached and its DNS record
created. Run the same verification against the final URL before updating any
frontend or backend manifest.

## Rollback

Because URLs and images are immutable, rollback is a configuration change:
point the Coolify resource to the previously verified image digest and redeploy.
Do not delete an archive that any released frontend or manifest may still use.

## Adding a commune or rebuilding data

Do not create one service per commune. Rebuild the consolidated PMTiles archive
with a new dataset version, verify its source coverage and SHA-256, then publish
one new immutable image and URL. This preserves a simple browser contract while
allowing the archive to contain many communes.

If the archive eventually exceeds the operational comfort of a single OCI image,
keep the URL contract and move only the origin storage to an S3-compatible object
store such as self-hosted MinIO. Caddy can remain the policy and cache boundary.
