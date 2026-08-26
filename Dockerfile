FROM caddy:2.11.4-alpine@sha256:5f5c8640aae01df9654968d946d8f1a56c497f1dd5c5cda4cf95ab7c14d58648 AS caddy-binary

FROM alpine:3.22@sha256:14358309a308569c32bdc37e2e0e9694be33a9d99e68afb0f5ff33cc1f695dce

ARG BUILD_REVISION=local
LABEL org.opencontainers.image.title="Cabidas Cadastre Assets" \
      org.opencontainers.image.description="Immutable PMTiles delivery service for Cabidas" \
      org.opencontainers.image.source="https://github.com/cabidas/cabidas-cadastre-assets" \
      org.opencontainers.image.revision="${BUILD_REVISION}" \
      org.opencontainers.image.licenses="Apache-2.0" \
      io.cabidas.cadastre.dataset-version="15b77a85753ceb06" \
      io.cabidas.cadastre.sha256="9b57ca4511470c6509a5ce16d259871f29976bb7c364f132b7188cb10e45311d"

ENV XDG_CONFIG_HOME=/tmp/caddy-config \
    XDG_DATA_HOME=/tmp/caddy-data

COPY --from=caddy-binary /usr/bin/caddy /tmp/caddy-source

RUN cp /tmp/caddy-source /usr/bin/caddy \
    && rm /tmp/caddy-source \
    && chmod 0755 /usr/bin/caddy \
    && addgroup -S -g 10001 caddy-assets \
    && adduser -S -D -H -u 10001 -G caddy-assets caddy-assets \
    && mkdir -p /srv/cadastre \
    && chown -R caddy-assets:caddy-assets /srv

COPY --chown=caddy-assets:caddy-assets Caddyfile /etc/caddy/Caddyfile
COPY --chown=caddy-assets:caddy-assets dist/cadastre/cadastre-15b77a85753ceb06.pmtiles /srv/cadastre/cadastre-15b77a85753ceb06.pmtiles

USER 10001:10001
EXPOSE 8080
STOPSIGNAL SIGQUIT
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/healthz || exit 1

ENTRYPOINT ["/usr/bin/caddy"]
CMD ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
