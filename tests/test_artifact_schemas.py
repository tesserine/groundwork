import unittest
from pathlib import Path

from tooling.artifact_schemas import (
    ArtifactSchemaError,
    load_artifact,
    registry_from_manifest,
    validate_artifact,
)


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

    def test_change_proposal_schema_accepts_capability_handle(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        artifact["handle"] = {
            "id": "github:tesserine/groundwork:pull/440",
            "display": "tesserine/groundwork#440",
        }

        validate_artifact("change-proposal", artifact, registry=registry_from_manifest())

    def test_change_proposal_schema_rejects_provider_shaped_handle(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        artifact["handle"] = {
            "forge_tag": "github",
            "url": "https://github.com/tesserine/groundwork/pull/440",
            "number": 440,
        }

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("change-proposal", artifact, registry=registry_from_manifest())

        self.assertIn("handle", context.exception.paths)

    def test_change_proposal_schema_accepts_multi_version_sequence(self) -> None:
        first = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        second = load_artifact("change-proposal", self.fixture("valid-change-proposal-sourcehut-v2.json"))

        self.assertEqual([1, 2], [first["version"], second["version"]])

    def test_change_proposal_schema_rejects_missing_version(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-proposal", self.fixture("invalid-change-proposal-missing-version.json"))

        self.assertIn("version", context.exception.paths)

    def test_change_proposal_schema_rejects_branch_and_base_refspec_injection_shapes(self) -> None:
        cases = [
            ("branch", "issue-316/bad:refs/heads/main"),
            ("branch", "issue-316/bad branch"),
            ("branch", "issue-316/bad\nbranch"),
            ("branch", "issue-316/bad\x7fbranch"),
            ("branch", "issue-316/../main"),
            ("base", "main:refs/heads/other"),
            ("base", "release candidate"),
            ("base", "main\tunsafe"),
            ("base", "main\x7funsafe"),
            ("base", "release/../main"),
        ]

        for field, value in cases:
            with self.subTest(field=field, value=repr(value)):
                artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
                artifact[field] = value

                with self.assertRaises(ArtifactSchemaError) as context:
                    validate_artifact("change-proposal", artifact)

                self.assertIn(field, context.exception.paths)

    def test_change_proposal_handle_resolves_against_manifest_registry(self) -> None:
        artifact = load_artifact(
            "change-proposal",
            self.fixture("valid-change-proposal-github-v1.json"),
            registry=registry_from_manifest(),
        )

        self.assertEqual({"id", "display"}, set(artifact["handle"]))

    def test_work_unit_schema_accepts_optional_capability_handles(self) -> None:
        for name in [
            "valid-work-unit.json",
            "valid-work-unit-github-handle.json",
        ]:
            with self.subTest(fixture=name):
                artifact = load_artifact("work-unit", self.fixture(name), registry=registry_from_manifest())

                if "handle" in artifact:
                    self.assertEqual({"id", "display"}, set(artifact["handle"]))

    def test_work_unit_schema_rejects_top_level_work_unit_field(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("work-unit", self.fixture("invalid-work-unit-top-level-work-unit.json"))

        self.assertIn("<root>", context.exception.paths)

    def test_work_unit_schema_rejects_provider_shaped_handle(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("work-unit", self.fixture("invalid-work-unit-malformed-handle.json"))

        self.assertIn("handle", context.exception.paths)

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
