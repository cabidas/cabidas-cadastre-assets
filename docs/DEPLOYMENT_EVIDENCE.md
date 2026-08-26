# Deployment evidence

Last verified: 2026-08-26

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

## Managed activation gate

The candidate is still intentionally loopback-only and is not registered as a
Coolify-managed resource. The next gate is to create that managed resource from
the immutable image digest, reproduce the reviewed runtime controls, and pass
the complete delivery contract through a temporary Coolify hostname.
Production DNS and the backend PMTiles catalog remain unchanged until that
managed candidate passes and activation is approved separately.
