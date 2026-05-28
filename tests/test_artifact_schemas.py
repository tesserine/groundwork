import json
import unittest
from pathlib import Path

from tooling.artifact_schemas import (
    ArtifactSchemaError,
    load_artifact,
    registry_from_manifest,
    validate_artifact,
)
from tooling.mechanics import MechanicRegistry


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"


class ArtifactSchemaTests(unittest.TestCase):
    def fixture(self, name: str) -> Path:
        return FIXTURES / name

    def test_change_proposal_schema_accepts_github_and_sourcehut_handles(self) -> None:
        for name in [
            "valid-change-proposal-github-v1.json",
            "valid-change-proposal-sourcehut-v2.json",
        ]:
            with self.subTest(fixture=name):
                artifact = load_artifact("change-proposal", self.fixture(name))

                self.assertIn(artifact["handle"]["forge_tag"], {"github", "sourcehut"})

    def test_change_proposal_schema_accepts_multi_version_sequence(self) -> None:
        first = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        second = load_artifact("change-proposal", self.fixture("valid-change-proposal-sourcehut-v2.json"))

        self.assertEqual([1, 2], [first["version"], second["version"]])

    def test_change_proposal_schema_rejects_missing_version(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-proposal", self.fixture("invalid-change-proposal-missing-version.json"))

        self.assertIn("version", context.exception.paths)

    def test_change_proposal_schema_rejects_malformed_forge_tag(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-proposal", self.fixture("invalid-change-proposal-malformed-forge-tag.json"))

        self.assertIn("handle", context.exception.paths)

    def test_change_proposal_schema_rejects_wrong_handle_variant_for_tag(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-proposal", self.fixture("invalid-change-proposal-wrong-handle-variant.json"))

        self.assertIn("handle", context.exception.paths)

    def test_change_proposal_forge_tag_resolves_against_manifest_registry(self) -> None:
        artifact = load_artifact(
            "change-proposal",
            self.fixture("valid-change-proposal-github-v1.json"),
            registry=registry_from_manifest(),
        )

        self.assertEqual("github", artifact["handle"]["forge_tag"])

    def test_change_proposal_forge_tag_rejects_unknown_registry_value(self) -> None:
        registry = MechanicRegistry(forge_tags={"github"})

        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-proposal", self.fixture("valid-change-proposal-sourcehut-v2.json"), registry=registry)

        self.assertIn("handle/forge_tag", context.exception.paths)
        self.assertIn("forge tag `sourcehut` does not resolve in registry", str(context.exception))

    def test_review_findings_schema_accepts_structured_findings(self) -> None:
        artifact = load_artifact("review-findings", self.fixture("valid-review-findings.json"))

        self.assertEqual("needs_revision", artifact["disposition"])
        self.assertEqual("blocking", artifact["findings"][0]["classification"])

    def test_review_findings_schema_rejects_unknown_disposition(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("review-findings", self.fixture("invalid-review-findings-disposition.json"))

        self.assertIn("disposition", context.exception.paths)

    def test_review_findings_schema_rejects_unclassified_finding(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("review-findings", self.fixture("invalid-review-findings-unclassified.json"))

        self.assertIn("findings/0/classification", context.exception.paths)

    def test_patch_schema_is_marked_superseded(self) -> None:
        schema = json.loads((ROOT / "schemas" / "patch.schema.json").read_text(encoding="utf-8"))

        self.assertIs(schema["deprecated"], True)
        self.assertIn("Superseded by change-proposal", schema["description"])

    def test_validate_artifact_accepts_already_loaded_json_data(self) -> None:
        artifact = load_artifact("review-findings", self.fixture("valid-review-findings-approved.json"))

        validate_artifact("review-findings", artifact)


if __name__ == "__main__":
    unittest.main()
