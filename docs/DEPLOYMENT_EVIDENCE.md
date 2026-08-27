# Deployment evidence

Last verified: 2026-08-27

## Public release

- Release: `cadastre-15b77a85753ceb06`
- Archive size: `20,502,868` bytes
- Archive SHA-256: `9b57ca4511470c6509a5ce16d259871f29976bb7c364f132b7188cb10e45311d`
- Release asset was downloaded again after publication; its size and full SHA-256
  matched `asset-manifest.json`.

## OCI image

- Image: `ghcr.io/cabidas/cabidas-cadastre-assets`
- Immutable index digest:
  `sha256:04221de36f7fd4cfd5925dc550b9cb17f71cb388c6d8a734134b613fbe946d8b`
- Linux amd64 manifest:
  `sha256:4251c0f0004362e3df302b987a4f130e1fd32ba829139f7207400fb09e58e17c`
- Attestation manifest:
  `sha256:e43007fc7cb91dbfb87ba58e5bdc1c97878090bc92d22bfea7c38caea0c77f89`
- GitHub Actions run `33018233466` verified the release identity and archive,
  built the image, emitted an SBOM and OCI provenance, pushed it to GHCR, and
  created a GitHub build-provenance attestation. All steps passed.
- Anonymous registry resolution passed after package publication. The Cabidas
  organization restriction on creating additional public packages was then
  restored.

## Isolated server candidate

The immutable image was pulled by digest onto the production Coolify host and
started as a loopback-only candidate. It does not have a public domain or route.

Verified runtime controls:

- image reference pinned to the index digest above;
- `linux/amd64` host and image;
- user `10001:10001`;
- read-only root filesystem;
- `/tmp` limited to a 16 MiB `noexec,nosuid` tmpfs;
- all Linux capabilities dropped;
- `no-new-privileges` enabled;
- 256 MiB memory, 32 MiB reservation, one CPU, and 128 PID ceilings;
- bounded JSON logs;
- container port `8080` bound only to host loopback;
- Docker health state `healthy`.

The complete remote delivery contract passed through a temporary SSH tunnel:
health, allow-listed paths, method restrictions, full-file SHA-256, PMTiles v3
magic, content type/length, byte ranges and `416`, ETag and conditional `304`,
Last-Modified, immutable caching, allowed-origin CORS/preflight, and rejection
of an untrusted origin. The temporary tunnel was closed after verification.

## Coolify control-plane gate

The pre-activation audit found that the installed Coolify image predated the
fix for CVE-2026-34047. On 2026-08-26, the control plane was upgraded with the
official version-pinned installer to `4.3.12` at image digest
`sha256:7e9f90a25443cea2e2b33925a58db8763650dde38e3e820cddb0fb692e4b9bed`.

Before the upgrade, a root-only rollback bundle was created on the host at
`/data/coolify/backups/security-upgrade-20260826T223119Z`. It contains a
restorable PostgreSQL custom-format dump, Coolify source/configuration and SSH
key archives, container/image metadata, the installer and upgrade logs, and an
offline compressed copy of the previous Coolify image. The database listing,
archives, image gzip stream, permissions, and checksums were verified before
the upgrade began.

Post-upgrade verification passed:

- the Coolify container is healthy on `4.3.12`, with zero restarts;
- the upgrade log records successful completion and status-file cleanup;
- PostgreSQL accepted connections and authenticated Redis returned `PONG`;
- all 17 pre-existing containers remained running;
- the Cabidas frontend, analysis route, and both backend health routes returned
  HTTP `200` from outside the server;
- the loopback-only cadastre candidate remained healthy and returned a correct
  `206` PMTiles byte-range response;
- no fatal, panic, exception, migration-failure, or error entries appeared in
  the recent Coolify logs.

Rollback was not required. The security gate is complete.

## Coolify-managed production service

On 2026-08-27, the candidate was replaced by a native Coolify Docker Compose
service in the Cabidas production environment and activated at the public domain:

- service UUID: `hdrwhn8qwrmz1sgj87em8pne`;
- service name: `cabidas-cadastre-assets`;
- container: `cadastre-assets-hdrwhn8qwrmz1sgj87em8pne`;
- immutable image: the GHCR index digest recorded above;
- public domain: `https://assets.cabidas.app`.

Docker inspection confirmed the managed container is running and healthy with
zero restarts. It runs as `10001:10001`, has a read-only root filesystem, a
16 MiB `noexec,nosuid` tmpfs, no Linux capabilities, no-new-privileges, a
128-PID limit, one CPU, 256 MiB memory, a 32 MiB reservation, and bounded JSON
logs. It has no host port binding; all public traffic reaches it through the
Coolify-managed Traefik route.

The complete delivery contract first passed against the private service and then
through the temporary Coolify hostname
`t8erss8cp8pmdzt0roxbv0dt.37.27.82.232.sslip.io`. The downloaded archive was
`20,502,868` bytes and matched SHA-256
`9b57ca4511470c6509a5ce16d259871f29976bb7c364f132b7188cb10e45311d`.
Range requests, CORS, cache validators, cache policy, method restrictions, and
error behavior also passed. The temporary hostname was removed afterward and
an external request returned `404`, confirming route removal before production activation.
The superseded manually started candidate container was removed after its lack
of mounts and volumes was verified.

Two Coolify `4.3.12` behaviors affected deployment:

- the Docker Image resource UI produced an invalid duplicate digest reference
  when given an `image@sha256:<digest>` value;
- its custom-option parser truncated `no-new-privileges:true` and did not
  reproduce the complete reviewed runtime policy.

The native Docker Compose resource is therefore the supported deployment path.
Compose also requires the PID ceiling under
`deploy.resources.limits.pids`; specifying a distinct top-level `pids_limit`
alongside deploy limits is rejected by the installed Compose version.

A failed Docker Image trial remains as application UUID
`erxop5mdeivlq2tywyurkuln`. It is stopped, has no FQDN, container, mount, or
volume, and cannot affect traffic. Coolify requires an interactive account
password to delete the row, so it is retained as an explicitly documented
control-plane cleanup item rather than handling credentials outside the normal
login flow.

## Production activation

Production activation completed on 2026-08-27 after explicit authorization:

- Coolify attached `https://assets.cabidas.app` to service UUID
  `hdrwhn8qwrmz1sgj87em8pne` and recreated the service successfully;
- a scoped pre-change Coolify database backup was written to
  `/data/coolify/backups/cadastre-assets-activation-20260827T1345Z`, and its custom-format dump
  passed `pg_restore -l` validation;
- all four authoritative Name.com servers resolve the `assets` A record to `37.27.82.232`;
- Traefik issued and serves a valid Let's Encrypt certificate for `assets.cabidas.app`;
- public health, `HEAD`, CORS, immutable cache, ETag, byte-range `206`, `Content-Range`, and
  PMTiles v3 header checks passed;
- a complete public download was `20,502,868` bytes and matched SHA-256
  `9b57ca4511470c6509a5ce16d259871f29976bb7c364f132b7188cb10e45311d`;
- backend commit `90e96d48e43a87e93726f3e5c9909637665c3092` activated the checked manifest and deployed
  successfully through Coolify; and
- the live `/api/v1/cadastre/catalog` reports `tiles_available`, the exact immutable asset URL,
  digest, size, zoom contract, and coverage for Las Condes, Lo Barnechea, and San Miguel.

The catalog-driven frontend required three production integration corrections after activation:

- `e002a61` prevents binding before MapLibre source managers exist;
- `a80575f` adds the exact asset origin to CSP `connect-src`; and
- `925c537` retries idempotent handler binding on `styledata` instead of depending on global map
  `idle`, which unrelated raster sources can postpone.

Authenticated browser acceptance passed on 2026-08-27 against deployed frontend bundle `925c537`:

- the live source type was `vector` with the exact immutable `pmtiles://` archive URL;
- browser archive requests returned HTTP `206`, while no viewport `/cadastre/bbox` request occurred;
- at zoom 17, rendered/source feature counts were Las Condes `346/668` (`15108`), Lo Barnechea
  `155/697` (`15161`), and San Miguel `325/1209` (`16106`);
- the expected `click`, `moveend`, and `sourcedata` handlers were present; and
- a real pointer click in Lo Barnechea called `/api/v1/cadastre/parcel` with HTTP `200`, rendered the
  authoritative selection geometry, and opened the parcel popup with address, area, and confirmation
  action.

The compatibility `/bbox` endpoint remains deployed as a controlled fallback. Its eventual removal
requires a separate decision based on monitoring history and rollback policy.
