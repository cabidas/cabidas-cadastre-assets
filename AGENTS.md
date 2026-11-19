# Cabidas agent instructions

## Official CI authority

Owner decision reaffirmed **2026-11-19**: the official CI is **local Buildbot +
act + Docker on the owner's Mac**. Before CI, release or deployment work, read the
[canonical CI policy](https://github.com/cabidas/cabidas-policy/blob/main/docs/CI_LOCAL.md)
and its [operations guide](https://github.com/cabidas/cabidas-policy/blob/main/tools/local-ci/README.md).
Use an available local policy checkout when present; this repository does not
require a sibling checkout.

Accept only the complete local build and receipt for the exact SHA, reported as
`local-ci/arm64/cabidas-cadastre-assets`. Hosted GitHub Actions runs or billing failures are
not the current acceptance gate or a pending deployment blocker. Do not rerun,
repair, re-enable or request payment for Actions unless the owner explicitly
changes this decision. The versioned `.github/workflows/` definitions remain
inputs to local `act`. Keep required repository checks and separate native AMD64
production acceptance.
