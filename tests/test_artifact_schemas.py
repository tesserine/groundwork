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
SCHEMAS = ROOT / "schemas"


def artifact_type_for_fixture(name: str) -> str:
    stem = name.removesuffix(".json")
    for prefix in ("valid-", "invalid-"):
        if stem.startswith(prefix):
            stem = stem.removeprefix(prefix)
            break

    artifact_types = sorted(
        (path.name.removesuffix(".schema.json") for path in SCHEMAS.glob("*.schema.json")),
        key=len,
        reverse=True,
    )
    for artifact_type in artifact_types:
        if stem == artifact_type or stem.startswith(f"{artifact_type}-"):
            return artifact_type
    raise AssertionError(f"Could not infer artifact type for fixture {name}")


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

    def test_change_proposal_schema_accepts_sourcehut_proposal_ref_handle(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-sourcehut-v2.json"))

        self.assertEqual("sourcehut", artifact["handle"]["forge_tag"])
        self.assertIn("proposal_ref", artifact["handle"])
        self.assertTrue(artifact["handle"]["proposal_ref"].startswith("refs/proposals/"))
        self.assertNotIn("m" + "box", artifact["handle"])

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

    def test_change_proposal_schema_rejects_sourcehut_legacy_mail_carrier_handle(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        legacy_carrier = "m" + "box"
        artifact["handle"] = {
            "forge_tag": "sourcehut",
            legacy_carrier: "artifact://change-proposals/issue-316/v2",
        }

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("change-proposal", artifact)

        self.assertIn("handle", context.exception.paths)

    def test_change_proposal_schema_rejects_sourcehut_handle_missing_proposal_ref(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        artifact["handle"] = {"forge_tag": "sourcehut"}

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("change-proposal", artifact)

        self.assertIn("handle", context.exception.paths)

    def test_change_proposal_schema_rejects_sourcehut_proposal_ref_outside_namespace(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        artifact["handle"] = {
            "forge_tag": "sourcehut",
            "proposal_ref": "refs/heads/issue-316/2",
        }

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("change-proposal", artifact)

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

    def test_work_unit_schema_accepts_optional_forge_ticket_handles(self) -> None:
        for name in [
            "valid-work-unit.json",
            "valid-work-unit-github-handle.json",
            "valid-work-unit-sourcehut-handle.json",
        ]:
            with self.subTest(fixture=name):
                artifact = load_artifact("work-unit", self.fixture(name), registry=registry_from_manifest())

                if "handle" in artifact:
                    self.assertIn(artifact["handle"]["forge_tag"], {"github", "sourcehut"})

    def test_work_unit_schema_rejects_top_level_work_unit_field(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("work-unit", self.fixture("invalid-work-unit-top-level-work-unit.json"))

        self.assertIn("<root>", context.exception.paths)

    def test_work_unit_schema_rejects_wrong_handle_variant_for_tag(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("work-unit", self.fixture("invalid-work-unit-wrong-handle-variant.json"))

        self.assertIn("handle", context.exception.paths)

    def test_work_unit_schema_rejects_malformed_handle(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("work-unit", self.fixture("invalid-work-unit-malformed-handle.json"))

        self.assertIn("handle", context.exception.paths)

    def test_work_unit_schema_rejects_github_url_number_mismatch(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("work-unit", self.fixture("invalid-work-unit-github-url-number-mismatch.json"))

        self.assertIn("handle/url", context.exception.paths)
        self.assertIn("does not agree with handle number", str(context.exception))

    def test_work_unit_forge_tag_rejects_unknown_registry_value(self) -> None:
        registry = MechanicRegistry(forge_tags={"github"})

        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("work-unit", self.fixture("valid-work-unit-sourcehut-handle.json"), registry=registry)

        self.assertIn("handle/forge_tag", context.exception.paths)
        self.assertIn("forge tag `sourcehut` does not resolve in registry", str(context.exception))

    def test_change_needs_revision_schema_accepts_structured_findings(self) -> None:
        artifact = load_artifact("change-needs-revision", self.fixture("valid-change-needs-revision.json"))

        self.assertEqual("blocking", artifact["findings"][0]["classification"])

    def test_change_approved_schema_accepts_approval_without_blocking_findings(self) -> None:
        artifact = load_artifact("change-approved", self.fixture("valid-change-approved.json"))

        self.assertEqual([], artifact["findings"])
        self.assertNotIn("disposition", artifact)

    def test_change_approved_schema_rejects_unclassified_finding(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-approved", self.fixture("invalid-change-approved-unclassified.json"))

        self.assertIn("findings/0/classification", context.exception.paths)

    def test_change_approved_schema_rejects_blocking_findings(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-approved", self.fixture("invalid-change-approved-with-blocking.json"))

        self.assertIn("findings", context.exception.paths)

    def test_change_needs_revision_schema_rejects_missing_blocking_finding(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-needs-revision", self.fixture("invalid-change-needs-revision-without-blocking.json"))

        self.assertIn("findings", context.exception.paths)

    def test_change_approved_schema_rejects_bad_review_timestamp(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-approved", self.fixture("invalid-change-approved-bad-timestamp.json"))

        self.assertIn("reviewed_at", context.exception.paths)

    def test_valid_artifact_fixtures_pass(self) -> None:
        for fixture in sorted(FIXTURES.glob("valid-*.json")):
            with self.subTest(fixture=fixture.name):
                load_artifact(artifact_type_for_fixture(fixture.name), fixture)

    def test_invalid_artifact_fixtures_reject(self) -> None:
        for fixture in sorted(FIXTURES.glob("invalid-*.json")):
            with self.subTest(fixture=fixture.name):
                with self.assertRaises(ArtifactSchemaError):
                    load_artifact(artifact_type_for_fixture(fixture.name), fixture)

    def test_validate_artifact_accepts_already_loaded_json_data(self) -> None:
        artifact = load_artifact("change-approved", self.fixture("valid-change-approved.json"))

        validate_artifact("change-approved", artifact)


if __name__ == "__main__":
    unittest.main()
