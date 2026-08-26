# Security policy

This service contains public, read-only cadastre visualization data and no user
data or credentials. Report vulnerabilities privately to the Cabidas maintainers.

The service deliberately exposes only `/healthz` and one versioned PMTiles path.
Directory listing, uploads, mutation methods, Caddy's admin API, automatic TLS,
and cross-origin access from domains other than Cabidas are disabled.
