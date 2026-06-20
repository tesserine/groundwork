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

    def test_behavior_artifacts_require_behavior_form(self) -> None:
        fixtures = {
            "behavior-contract": "valid-behavior-contract.json",
            "implementation-plan": "valid-implementation-plan.json",
            "test-evidence": "valid-test-evidence.json",
            "completion-evidence": "valid-completion-evidence.json",
        }

        for artifact_type, fixture_name in fixtures.items():
            with self.subTest(artifact_type=artifact_type):
                artifact = load_artifact(artifact_type, self.fixture(fixture_name))
                self.assertEqual("scenario", artifact["behavior_form"])
                artifact.pop("behavior_form")

                with self.assertRaises(ArtifactSchemaError) as context:
                    validate_artifact(artifact_type, artifact)

                self.assertIn("behavior_form", context.exception.paths)

    def test_gate_form_behavior_artifacts_validate_without_scenarios(self) -> None:
        fixtures = {
            "behavior-contract": "valid-behavior-contract-gate.json",
            "implementation-plan": "valid-implementation-plan-gate.json",
            "test-evidence": "valid-test-evidence-gate.json",
            "completion-evidence": "valid-completion-evidence-gate.json",
        }

        for artifact_type, fixture_name in fixtures.items():
            with self.subTest(artifact_type=artifact_type):
                artifact = load_artifact(artifact_type, self.fixture(fixture_name))
                serialized = json.dumps(artifact)
                self.assertEqual("gate", artifact["behavior_form"])
                self.assertNotIn('"scenarios"', serialized)
                self.assertNotIn('"scenario"', serialized)

    def test_gate_form_behavior_artifacts_reject_scenario_shaped_payloads(self) -> None:
        fixtures = {
            "behavior-contract": "invalid-behavior-contract-gate-with-scenarios.json",
            "implementation-plan": "invalid-implementation-plan-gate-with-scenario-mapping.json",
            "test-evidence": "invalid-test-evidence-gate-with-scenario-evidence.json",
            "completion-evidence": "invalid-completion-evidence-gate-with-scenarios.json",
        }

        for artifact_type, fixture_name in fixtures.items():
            with self.subTest(artifact_type=artifact_type):
                with self.assertRaises(ArtifactSchemaError):
                    load_artifact(artifact_type, self.fixture(fixture_name))

    def test_gate_form_completion_evidence_accepts_uncovered_criteria_without_gates(self) -> None:
        artifact = load_artifact(
            "completion-evidence",
            self.fixture("valid-completion-evidence-gate-uncovered.json"),
        )

        self.assertEqual("gate", artifact["behavior_form"])
        self.assertEqual("uncovered", artifact["criterion_coverage"][0]["status"])
        self.assertNotIn("gates", artifact["criterion_coverage"][0])

    def test_scenario_form_completion_evidence_accepts_uncovered_criteria_without_scenarios(self) -> None:
        artifact = load_artifact("completion-evidence", self.fixture("valid-completion-evidence.json"))
        uncovered_entries = [
            entry for entry in artifact["criterion_coverage"] if entry["status"] == "uncovered"
        ]

        self.assertGreaterEqual(len(uncovered_entries), 1)
        self.assertNotIn("scenarios", uncovered_entries[0])

    def test_completion_evidence_requires_status_evidence_for_covered_or_partial_criteria(self) -> None:
        fixtures = [
            "invalid-completion-evidence-gate-covered-without-gates.json",
            "invalid-completion-evidence-gate-partial-without-gates.json",
            "invalid-completion-evidence-scenario-covered-without-scenarios.json",
            "invalid-completion-evidence-scenario-partial-without-scenarios.json",
        ]

        for fixture_name in fixtures:
            with self.subTest(fixture=fixture_name):
                with self.assertRaises(ArtifactSchemaError):
                    load_artifact("completion-evidence", self.fixture(fixture_name))

    def test_completion_evidence_rejects_status_evidence_contradictions(self) -> None:
        fixtures = [
            "invalid-completion-evidence-gate-covered-with-failed-gate.json",
            "invalid-completion-evidence-gate-covered-with-failures.json",
            "invalid-completion-evidence-scenario-covered-with-failures.json",
            "invalid-completion-evidence-gate-partial-without-failure-signal.json",
            "invalid-completion-evidence-scenario-partial-without-failures.json",
            "invalid-completion-evidence-gate-uncovered-with-gates.json",
            "invalid-completion-evidence-gate-uncovered-with-failures.json",
            "invalid-completion-evidence-scenario-uncovered-with-scenarios.json",
            "invalid-completion-evidence-scenario-uncovered-with-failures.json",
        ]

        for fixture_name in fixtures:
            with self.subTest(fixture=fixture_name):
                with self.assertRaises(ArtifactSchemaError):
                    load_artifact("completion-evidence", self.fixture(fixture_name))

    def test_completion_evidence_accepts_coherent_status_evidence(self) -> None:
        fixtures = [
            "valid-completion-evidence.json",
            "valid-completion-evidence-gate.json",
            "valid-completion-evidence-gate-uncovered.json",
        ]

        for fixture_name in fixtures:
            with self.subTest(fixture=fixture_name):
                artifact = load_artifact("completion-evidence", self.fixture(fixture_name))
                partial_entries = [
                    entry for entry in artifact["criterion_coverage"] if entry["status"] == "partial"
                ]
                for entry in partial_entries:
                    if artifact["behavior_form"] == "scenario":
                        self.assertGreaterEqual(len(entry.get("failures", [])), 1)
                    else:
                        has_failed_gate = any(gate["result"] == "fail" for gate in entry.get("gates", []))
                        has_listed_failure = len(entry.get("failures", [])) >= 1
                        self.assertTrue(has_failed_gate or has_listed_failure)

    def test_runtime_behavior_artifact_schemas_remain_mcp_advertisable(self) -> None:
        for schema_name in [
            "behavior-contract.schema.json",
            "implementation-plan.schema.json",
            "test-evidence.schema.json",
            "completion-evidence.schema.json",
        ]:
            with self.subTest(schema=schema_name):
                schema = json.loads((SCHEMAS / schema_name).read_text(encoding="utf-8"))
                self.assertEqual("object", schema.get("type"))
                for keyword in ["oneOf", "anyOf", "allOf", "$ref"]:
                    self.assertNotIn(keyword, schema)

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

    def test_change_proposal_schema_rejects_sourcehut_proposal_ref_refspec_injection(self) -> None:
        artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
        artifact["handle"] = {
            "forge_tag": "sourcehut",
            "proposal_ref": "refs/proposals/x:refs/heads/main",
        }

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("change-proposal", artifact)

        self.assertIn("handle", context.exception.paths)

    def test_change_proposal_schema_rejects_sourcehut_proposal_ref_whitespace_and_control(self) -> None:
        for proposal_ref in ["refs/proposals/issue 316/2", "refs/proposals/issue-316/\n2"]:
            with self.subTest(proposal_ref=proposal_ref):
                artifact = load_artifact("change-proposal", self.fixture("valid-change-proposal-github-v1.json"))
                artifact["handle"] = {
                    "forge_tag": "sourcehut",
                    "proposal_ref": proposal_ref,
                }

                with self.assertRaises(ArtifactSchemaError) as context:
                    validate_artifact("change-proposal", artifact)

                self.assertIn("handle", context.exception.paths)

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
