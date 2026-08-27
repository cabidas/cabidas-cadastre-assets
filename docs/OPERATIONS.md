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
5. Create the immutable GitHub release `cadastre-<dataset-version>` and attach
   exactly the archive named in `asset-manifest.json`. Publishing the release
   triggers `.github/workflows/publish-image.yml`, which downloads and verifies
   the asset before building. For an authorized local fallback, use
   `scripts/publish_image.sh ghcr.io/cabidas/cabidas-cadastre-assets`.
   Both paths target the Coolify server's `linux/amd64` architecture and emit
   OCI provenance plus an SBOM attestation.
6. Resolve and record the resulting immutable image digest.
7. Configure Coolify with the digest, not `latest`.

Publishing credentials belong in the operator's credential store or CI secret
manager. They must never be committed, printed, or entered as Docker build args.

## Coolify candidate

Create a separate **Docker Compose service** from `compose.example.yaml` and set
`CADASTRE_ASSETS_IMAGE` to the complete immutable
`ghcr.io/...@sha256:<digest>` reference. Do not use a Coolify Docker Image
application for this workload on Coolify `4.3.12`: its image fields can produce
a duplicate digest reference, and its custom-option parser does not preserve
the complete runtime policy. Re-evaluate this restriction only after a later
Coolify release is tested end to end.

Keep the container private during validation. The Compose service exposes port
`8080` only to the private Coolify network; it must not publish a host port.
Define the PID ceiling as `deploy.resources.limits.pids: 128`. Do not add a
second, top-level `pids_limit` while deploy resource limits are present because
the installed Compose version rejects distinct values.

Before creating or changing a production resource, confirm that the Coolify
control plane is on a currently supported, security-patched release and that a
verified database/configuration rollback bundle exists. Record the control-plane
version, immutable image digest, backup location, and post-change health checks
in `docs/DEPLOYMENT_EVIDENCE.md`.

Before attaching public DNS, apply:

- read-only root filesystem;
- `/tmp` tmpfs with a 16 MiB limit;
- all Linux capabilities dropped;
- `no-new-privileges`;
- one CPU and 256 MiB memory as initial ceilings;
- a 128 PID ceiling and 32 MiB memory reservation;
- restart policy `unless-stopped`;
- health endpoint `/healthz`;
- JSON logs rotated at 10 MiB with three files retained.

First validate through Coolify's temporary hostname:

```bash
python3 scripts/verify_delivery.py https://<candidate-hostname>
```

Only after this passes should `assets.cabidas.app` be attached and its DNS record
created. Run the same verification against the final URL before updating any
frontend or backend manifest.

After the public contract passes, activate the backend catalog before changing any frontend default.
Verify that `/api/v1/cadastre/catalog` reports `tiles_available` with the exact URL, size, digest,
source layer, zooms, and commune coverage. The frontend `auto` mode can then select PMTiles without a
frontend redeploy. Complete browser acceptance by confirming `206` archive range requests, visible
parcel boundaries, API-backed point selection, and no compatibility `/bbox` request during the
normal tile path.

After temporary-hostname validation, remove that hostname, redeploy the same
service revision, and confirm the temporary URL no longer routes. Record the
service UUID, image digest, runtime inspection, contract result, and route
removal in `docs/DEPLOYMENT_EVIDENCE.md`.

If a failed trial resource has no domain, container, mount, or volume, it is
safe to leave stopped until an administrator can delete it through Coolify's
password-confirmed UI. Never share or automate an account password merely to
remove an inert control-plane row.

## Rollback

Because URLs and images are immutable, rollback is a configuration change:
point the Coolify resource to the previously verified image digest and redeploy.
Do not delete an archive that any released frontend or manifest may still use.
For a delivery-only incident, first return the backend tile manifest to `staged` and deploy it; the
catalog-driven frontend will fall back to `/bbox` without a frontend deployment. Retain the public
archive and DNS route as immutable release evidence while the incident is investigated.

## Adding a commune or rebuilding data

Do not create one service per commune. Rebuild the consolidated PMTiles archive
with a new dataset version, verify its source coverage and SHA-256, then publish
one new immutable image and URL. This preserves a simple browser contract while
allowing the archive to contain many communes.

If the archive eventually exceeds the operational comfort of a single OCI image,
keep the URL contract and move only the origin storage to an S3-compatible object
store such as self-hosted MinIO. Caddy can remain the policy and cache boundary.
