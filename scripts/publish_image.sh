#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "usage: $0 REGISTRY_IMAGE" >&2
  echo "example: $0 ghcr.io/cabidas/cadastre-assets" >&2
  exit 2
fi

registry_image=$1
dataset_version=$(python3 -c 'import json; print(json.load(open("asset-manifest.json"))["dataset_version"])')
revision=$(git rev-parse --verify HEAD)
image_ref="${registry_image}:${dataset_version}"

python3 scripts/verify_local_asset.py
mkdir -p .build

docker buildx build \
  --platform linux/amd64 \
  --build-arg "BUILD_REVISION=${revision}" \
  --provenance=mode=max \
  --sbom=true \
  --tag "${image_ref}" \
  --metadata-file .build/image-metadata.json \
  --push \
  .

echo "published ${image_ref}"
echo "Resolve and record its immutable digest before deployment:"
echo "  docker buildx imagetools inspect ${image_ref}"
