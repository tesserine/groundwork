import json
import unittest
from pathlib import Path

from tooling.artifact_schemas import (
    ArtifactSchemaError,
    detect_contract_evidence_defects,
    load_artifact,
    registry_from_manifest,
    validate_contract_evidence,
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

    def test_change_proposal_schema_accepts_connector_handles(self) -> None:
        for name in [
            "valid-change-proposal-github-v1.json",
            "valid-change-proposal-sourcehut-v2.json",
        ]:
            with self.subTest(fixture=name):
                artifact = load_artifact("change-proposal", self.fixture(name))

                self.assertEqual({"id", "display"}, set(artifact["handle"]))

    def test_contract_criteria_require_dimension_hollow_delivery_and_check_kind(self) -> None:
        artifact = load_artifact("contract", self.fixture("valid-contract.json"))
        self.assertEqual(
            {"behavior", "documentation", "code-quality"},
            {criterion["dimension"] for criterion in artifact["criteria"]},
        )

        for fixture_name, expected_path in [
            ("invalid-contract.json", "criteria/0/hollow_delivery"),
            ("invalid-contract-missing-check-kind.json", "criteria/0/check_kind"),
            ("invalid-contract-dimension-check-kind.json", "<root>"),
        ]:
            with self.subTest(fixture=fixture_name):
                with self.assertRaises(ArtifactSchemaError) as context:
                    load_artifact("contract", self.fixture(fixture_name))
                self.assertIn(expected_path, context.exception.paths)

    def test_contract_accepts_new_dimension_without_schema_change(self) -> None:
        artifact = load_artifact("contract", self.fixture("valid-contract-fourth-dimension.json"))

        self.assertEqual("release-notes", artifact["criteria"][0]["dimension"])

    def test_completion_evidence_records_one_result_shape(self) -> None:
        artifact = load_artifact("completion-evidence", self.fixture("valid-completion-evidence.json"))

        self.assertEqual(
            {
                "behavior-api-validates-records",
                "documentation-api-reference",
                "code-quality-single-validation-path",
            },
            {result["criterion_id"] for result in artifact["results"]},
        )
        self.assertNotIn("behavior_form", artifact)
        self.assertNotIn("criterion_coverage", artifact)

    def test_completion_evidence_rejects_attested_bare_pass(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact(
                "completion-evidence",
                self.fixture("invalid-completion-evidence-attested-bare-pass.json"),
            )

        self.assertIn("results/0/evidence", context.exception.paths)

    def test_completion_evidence_validates_against_contract_check_kind(self) -> None:
        contract = load_artifact("contract", self.fixture("valid-contract.json"))
        evidence = load_artifact("completion-evidence", self.fixture("valid-completion-evidence.json"))

        validate_contract_evidence(
            contract,
            evidence,
            warranted_dimensions={"behavior", "documentation", "code-quality"},
        )

        missing = json.loads(json.dumps(evidence))
        missing["results"] = missing["results"][:-1]
        with self.assertRaises(ArtifactSchemaError) as context:
            validate_contract_evidence(contract, missing)
        self.assertIn("results", context.exception.paths)

        wrong_kind = json.loads(json.dumps(evidence))
        wrong_kind["results"][1]["evidence"] = {
            "summary": "A run cannot satisfy an attested criterion.",
            "run": {
                "command": "python -m unittest",
                "result": "pass",
                "output_summary": "tests passed",
            },
        }
        with self.assertRaises(ArtifactSchemaError) as context:
            validate_contract_evidence(contract, wrong_kind)
        self.assertIn("results/1/evidence", context.exception.paths)

    def test_validate_artifact_rejects_completion_evidence_not_matching_contract(self) -> None:
        contract = load_artifact("contract", self.fixture("valid-contract.json"))
        evidence = load_artifact("completion-evidence", self.fixture("valid-completion-evidence.json"))

        unknown = json.loads(json.dumps(evidence))
        unknown["results"][0]["criterion_id"] = "unknown-contract-criterion"
        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("completion-evidence", unknown, related_artifacts={"contract": contract})
        self.assertIn("results/0/criterion_id", context.exception.paths)

        missing = json.loads(json.dumps(evidence))
        missing["results"] = missing["results"][:-1]
        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("completion-evidence", missing, related_artifacts={"contract": contract})
        self.assertIn("results", context.exception.paths)

    def test_completion_evidence_rejects_empty_documentation_entries(self) -> None:
        evidence = load_artifact("completion-evidence", self.fixture("valid-completion-evidence.json"))

        for field in ["updated", "verified_accurate", "follow_up_work_units"]:
            with self.subTest(field=field):
                invalid = json.loads(json.dumps(evidence))
                invalid["documentation"][field] = [""]

                with self.assertRaises(ArtifactSchemaError) as context:
                    validate_artifact("completion-evidence", invalid)

                self.assertIn(f"documentation/{field}/0", context.exception.paths)

    def test_detectability_mechanism_is_dimension_agnostic(self) -> None:
        contract = load_artifact("contract", self.fixture("valid-contract.json"))
        evidence = load_artifact("completion-evidence", self.fixture("valid-completion-evidence.json"))

        defects = detect_contract_evidence_defects(
            contract,
            evidence,
            warranted_dimensions={"behavior", "release-notes"},
            warranted_acceptance_criteria={
                "code-quality": {"Validation remains centralized", "Public APIs stay typed"},
            },
        )

        messages = " ".join(message for _path, message in defects)
        self.assertIn("release-notes", messages)
        self.assertIn("Public APIs stay typed", messages)

    def test_runtime_behavior_artifact_schemas_remain_mcp_advertisable(self) -> None:
        for schema_name in [
            "contract.schema.json",
            "implementation-plan.schema.json",
            "test-evidence.schema.json",
            "completion-evidence.schema.json",
        ]:
            with self.subTest(schema=schema_name):
                schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
                self.assertEqual("object", schema.get("type"))
                for keyword in ["oneOf", "anyOf", "allOf", "$ref"]:
                    self.assertNotIn(keyword, schema)

    def test_change_proposal_schema_accepts_opaque_proposal_handle(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-sourcehut-v2.json"))

        self.assertEqual({"id", "display"}, set(artifact["handle"]))
        self.assertTrue(artifact["handle"]["id"].startswith("proposal:"))

    def test_change_proposal_schema_accepts_multi_version_sequence(self) -> None:
        first = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        second = load_artifact("change-proposal", self.fixture("valid-change-proposal-sourcehut-v2.json"))

        self.assertEqual([1, 2], [first["version"], second["version"]])

    def test_change_proposal_schema_rejects_missing_version(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-proposal", self.fixture("invalid-change-proposal-missing-version.json"))

        self.assertIn("version", context.exception.paths)

    def test_change_proposal_schema_rejects_provider_shaped_handle(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-proposal", self.fixture("invalid-change-proposal-malformed-forge-tag.json"))

        self.assertIn("handle/display", context.exception.paths)

    def test_change_proposal_schema_rejects_wrong_handle_variant_for_tag(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("change-proposal", self.fixture("invalid-change-proposal-wrong-handle-variant.json"))

        self.assertIn("handle/display", context.exception.paths)

    def test_change_proposal_schema_rejects_extra_provider_handle_fields(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        artifact["handle"] = {
            "id": "proposal:123",
            "display": "proposal 123",
            "url": "https://example.invalid/proposal/123",
        }

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("change-proposal", artifact)

        self.assertIn("handle", context.exception.paths)

    def test_change_proposal_schema_rejects_missing_handle_display(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        artifact["handle"] = {"id": "proposal:123"}

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("change-proposal", artifact)

        self.assertIn("handle/display", context.exception.paths)

    def test_change_proposal_schema_rejects_empty_handle_id(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        artifact["handle"] = {"id": "", "display": "proposal 123"}

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("change-proposal", artifact)

        self.assertIn("handle/id", context.exception.paths)

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

    def test_change_proposal_connector_handle_validates_with_manifest_registry(self) -> None:
        artifact = load_artifact(
            "change-proposal",
            self.fixture("valid-change-proposal-github-v1.json"),
            registry=registry_from_manifest(),
        )

        self.assertEqual({"id", "display"}, set(artifact["handle"]))

    def test_work_unit_schema_requires_connector_ticket_handles(self) -> None:
        for name in [
            "valid-work-unit.json",
            "valid-work-unit-github-handle.json",
            "valid-work-unit-sourcehut-handle.json",
        ]:
            with self.subTest(fixture=name):
                artifact = load_artifact("work-unit", self.fixture(name), registry=registry_from_manifest())

                self.assertEqual({"id", "display"}, set(artifact["handle"]))

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

    def test_work_unit_schema_rejects_provider_shaped_handle(self) -> None:
        with self.assertRaises(ArtifactSchemaError) as context:
            load_artifact("work-unit", self.fixture("invalid-work-unit-github-url-number-mismatch.json"))

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
