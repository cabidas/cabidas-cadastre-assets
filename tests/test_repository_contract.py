from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RepositoryContractTest(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = json.loads(
            (ROOT / "asset-manifest.json").read_text(encoding="utf-8")
        )

    def test_manifest_is_immutable_and_versioned(self) -> None:
        archive = self.manifest["archive"]
        version = self.manifest["dataset_version"]
        self.assertEqual(self.manifest["schema"], "cabidas.cadastre_asset.v1")
        self.assertIn(version, archive["path"])
        self.assertIn(version, archive["public_path"])
        self.assertEqual(len(archive["sha256"]), 64)
        self.assertGreater(archive["size_bytes"], 0)

    def test_backend_provenance_matches_delivery_manifest(self) -> None:
        provenance = json.loads(
            (ROOT / self.manifest["provenance_manifest"]).read_text(encoding="utf-8")
        )
        archive = self.manifest["archive"]
        self.assertEqual(provenance["dataset_version"], self.manifest["dataset_version"])
        self.assertEqual(provenance["archive"]["sha256"], archive["sha256"])
        self.assertEqual(provenance["archive"]["size_bytes"], archive["size_bytes"])
        self.assertEqual(provenance["archive"]["content_type"], archive["media_type"])
        self.assertEqual(provenance["feature_count"], 67706)
        self.assertEqual(
            {source["commune_code"] for source in provenance["source_artifacts"]},
            {"15108", "15161", "16106"},
        )

    def test_image_is_digest_pinned(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        self.assertIn("caddy:2.11.4-alpine@sha256:", dockerfile)
        self.assertIn("alpine:3.22@sha256:", dockerfile)
        self.assertIn(self.manifest["archive"]["sha256"], dockerfile)
        self.assertIn("USER 10001:10001", dockerfile)

    def test_binary_assets_are_not_tracked(self) -> None:
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("dist/", gitignore)

    def test_delivery_policy_matches_server_config(self) -> None:
        caddyfile = (ROOT / "Caddyfile").read_text(encoding="utf-8")
        archive = self.manifest["archive"]
        self.assertIn(archive["public_path"], caddyfile)
        self.assertIn(self.manifest["delivery"]["cache_control"], caddyfile)
        self.assertIn(archive["media_type"], caddyfile)

    def test_compose_runtime_is_hardened(self) -> None:
        compose = (ROOT / "compose.example.yaml").read_text(encoding="utf-8")
        self.assertIn("read_only: true", compose)
        self.assertIn("no-new-privileges:true", compose)
        self.assertIn("cap_drop:", compose)
        self.assertIn("memory: 256M", compose)

    def test_workflow_actions_are_commit_pinned(self) -> None:
        for workflow_path in (ROOT / ".github" / "workflows").glob("*.yml"):
            workflow = workflow_path.read_text(encoding="utf-8")
            references = re.findall(r"uses:\s+[^@\s]+@([^\s#]+)", workflow)
            self.assertTrue(references, f"no actions found in {workflow_path.name}")
            for reference in references:
                self.assertRegex(
                    reference,
                    r"^[0-9a-f]{40}$",
                    f"floating action reference in {workflow_path.name}: {reference}",
                )

    def test_publish_workflow_matches_archive_identity(self) -> None:
        workflow = (
            ROOT / ".github" / "workflows" / "publish-image.yml"
        ).read_text(encoding="utf-8")
        archive = self.manifest["archive"]
        self.assertIn(f"DATASET_VERSION: {self.manifest['dataset_version']}", workflow)
        self.assertIn(Path(archive["path"]).name, workflow)


if __name__ == "__main__":
    unittest.main()
