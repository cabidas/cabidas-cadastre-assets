SHELL := /bin/sh
IMAGE ?= cabidas-cadastre-assets:15b77a85753ceb06
CONTAINER ?= cabidas-cadastre-assets-test
PORT ?= 18080

.PHONY: verify-asset validate-config build test-container stop-container verify-url

verify-asset:
	python3 scripts/verify_local_asset.py

validate-config:
	docker run --rm -v "$(CURDIR)/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2.11.4-alpine@sha256:5f5c8640aae01df9654968d946d8f1a56c497f1dd5c5cda4cf95ab7c14d58648 caddy validate --config /etc/caddy/Caddyfile

build: verify-asset validate-config
	docker build --build-arg BUILD_REVISION="$$(git rev-parse --verify HEAD 2>/dev/null || printf local)" -t "$(IMAGE)" .

test-container: build
	-docker rm -f "$(CONTAINER)"
	docker run -d --name "$(CONTAINER)" --read-only --tmpfs /tmp:rw,noexec,nosuid,size=16m --cap-drop ALL --security-opt no-new-privileges -p "127.0.0.1:$(PORT):8080" "$(IMAGE)"
	python3 scripts/verify_delivery.py "http://127.0.0.1:$(PORT)"
	docker rm -f "$(CONTAINER)"

stop-container:
	-docker rm -f "$(CONTAINER)"

verify-url:
	test -n "$(URL)"
	python3 scripts/verify_delivery.py "$(URL)"
