import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tooling.conformance import discover_units, main, run_conformance
from tooling.workflow_contracts import WorkflowRegistry


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"
MECHANIC_FIXTURES = ROOT / "tests" / "fixtures" / "mechanics"
WORKFLOW_FIXTURES = ROOT / "tests" / "fixtures" / "workflow-contracts"
SCHEMAS = ROOT / "schemas"


class ConformanceTests(unittest.TestCase):
    def run_manifest_conformance(self, manifest_source: str) -> list:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.toml"
            manifest.write_text(manifest_source.lstrip(), encoding="utf-8")

            return run_conformance([manifest])

    def review_outcome_manifest(self, successor_trigger: str) -> str:
        return f"""
name = "review-methodology"

[[artifact_types]]
name = "change-proposal"

[[artifact_types]]
name = "review-findings"

[[artifact_types]]
name = "change-approved"

[[artifact_types]]
name = "change-needs-revision"

[[outcome_types]]
name = "change-approved"

[[outcome_types]]
name = "change-needs-revision"

[[protocols]]
name = "review"
produces = ["review-findings"]
trigger = {{ type = "on_change", name = "change-proposal" }}

[[protocols.required_output_choices]]
name = "review-disposition"
members = ["change-approved", "change-needs-revision"]

[[protocols]]
name = "successor"
{successor_trigger}
"""

    def test_explicit_dispatch_accepts_valid_step_1_units(self) -> None:
        results = run_conformance(
            [
                WORKFLOW_FIXTURES / "valid-linear.toml",
                MECHANIC_FIXTURES / "valid-git.toml",
                ARTIFACT_FIXTURES / "valid-change-proposal-github-v1.json",
                SCHEMAS / "change-proposal.schema.json",
            ]
        )

        self.assertEqual(
            [
                "C-2 workflow-contract",
                "C-3 mechanic",
                "C-4 artifact-instance",
                "C-4 schema-definition",
            ],
            [result.category for result in results],
        )
        self.assertTrue(all(result.passed for result in results))

    def test_invalid_units_return_failures_without_raising(self) -> None:
        results = run_conformance(
            [
                WORKFLOW_FIXTURES / "invalid-malformed-shape.toml",
                MECHANIC_FIXTURES / "invalid-malformed-shape.toml",
                ARTIFACT_FIXTURES / "invalid-change-proposal-missing-version.json",
            ]
        )

        self.assertEqual(3, len(results))
        self.assertTrue(all(not result.passed for result in results))
        self.assertTrue(all(result.errors for result in results))
        self.assertIn("nodes/0/name", results[0].errors[0])
        self.assertIn("purpose", " ".join(results[1].errors))
        self.assertIn("version", results[2].errors[0])

    def test_workflow_registry_references_are_validated_by_runner(self) -> None:
        results = run_conformance([WORKFLOW_FIXTURES / "invalid-registry-reference.toml"])

        self.assertEqual(1, len(results))
        self.assertEqual("C-2 workflow-contract", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("discipline `missing-discipline` does not resolve in registry", " ".join(results[0].errors))

    def test_missing_explicit_path_fails_without_aborting_remaining_units(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.schema.json"

            results = run_conformance([missing, WORKFLOW_FIXTURES / "valid-linear.toml"])

        self.assertEqual(2, len(results))
        self.assertEqual("C-4 schema-definition", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("cannot read conformance unit", " ".join(results[0].errors))
        self.assertEqual("C-2 workflow-contract", results[1].category)
        self.assertTrue(results[1].passed)

    def test_non_utf8_explicit_path_fails_without_aborting_remaining_units(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            malformed = Path(directory) / "malformed.schema.json"
            malformed.write_bytes(b"\xff")

            results = run_conformance([malformed, WORKFLOW_FIXTURES / "valid-linear.toml"])

        self.assertEqual(2, len(results))
        self.assertEqual("C-4 schema-definition", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("cannot read conformance unit", " ".join(results[0].errors))
        self.assertEqual("C-2 workflow-contract", results[1].category)
        self.assertTrue(results[1].passed)

    def test_invalid_schema_definition_returns_failure_result(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            schema = Path(directory) / "broken.schema.json"
            schema.write_text(json.dumps({"type": 7}), encoding="utf-8")

            results = run_conformance([schema])

        self.assertEqual(1, len(results))
        self.assertEqual("C-4 schema-definition", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("not valid under any of the given schemas", " ".join(results[0].errors))

    def test_unknown_explicit_path_fails_instead_of_silently_skipping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            unknown = Path(directory) / "unit.txt"
            unknown.write_text("not a conformance unit", encoding="utf-8")

            results = run_conformance([unknown])

        self.assertEqual(1, len(results))
        self.assertEqual("unknown", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("unsupported conformance unit", results[0].errors)

    def test_directory_argument_discovers_only_recognized_units(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text(
                """
name = "example"

[[artifact_types]]
name = "completion-evidence"

[[mechanics]]
name = "read-artifact"
""".lstrip(),
                encoding="utf-8",
            )
            (root / "skills" / "orient").mkdir(parents=True)
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            contract = contracts / "verify.toml"
            contract.write_text((WORKFLOW_FIXTURES / "valid-linear.toml").read_text(encoding="utf-8"), encoding="utf-8")

            results = run_conformance([root])

        self.assertEqual([root / "manifest.toml", contract], [result.path for result in results])
        self.assertEqual(["C-5 manifest", "C-2 workflow-contract"], [result.category for result in results])
        self.assertTrue(all(result.passed for result in results))

    def test_directory_argument_validates_units_against_self_contained_local_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text(
                """
name = "local-methodology"

[[artifact_types]]
name = "completion-evidence"

[[mechanics]]
name = "read-artifact"
""".lstrip(),
                encoding="utf-8",
            )
            (root / "skills" / "orient").mkdir(parents=True)
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            contract = contracts / "verify.toml"
            contract.write_text((WORKFLOW_FIXTURES / "valid-linear.toml").read_text(encoding="utf-8"), encoding="utf-8")
            mechanics = root / "mechanics"
            mechanics.mkdir()
            mechanic = mechanics / "produce-artifact.toml"
            mechanic.write_text((MECHANIC_FIXTURES / "valid-mcp-tool.toml").read_text(encoding="utf-8"), encoding="utf-8")

            results = run_conformance([root])

        self.assertEqual(
            [
                "C-5 manifest",
                "C-2 workflow-contract",
                "C-3 mechanic",
            ],
            [result.category for result in results],
        )
        self.assertTrue(all(result.passed for result in results))

    def test_directory_workflow_contract_uses_self_contained_local_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text(
                """
name = "local-methodology"

[[artifact_types]]
name = "completion-evidence"

[[artifact_types]]
name = "test-evidence"

[[outcome_types]]
name = "completion-evidence"

[[outcome_types]]
name = "test-evidence"

[[mechanics]]
name = "read-artifact"

[[protocols]]
name = "verify"

[[protocols.required_output_choices]]
name = "verify-disposition"
members = ["completion-evidence", "test-evidence"]
""".lstrip(),
                encoding="utf-8",
            )
            (root / "skills" / "orient").mkdir(parents=True)
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            contract = contracts / "verify.toml"
            contract.write_text((WORKFLOW_FIXTURES / "valid-linear.toml").read_text(encoding="utf-8"), encoding="utf-8")

            results = run_conformance([root])

        workflow_result = next(result for result in results if result.path == contract)
        self.assertEqual("C-2 workflow-contract", workflow_result.category)
        self.assertFalse(workflow_result.passed)
        self.assertIn("do not match outcome terminal artifact_produced values", " ".join(workflow_result.errors))

    def test_directory_workflow_contract_rejects_non_member_terminal_for_required_choice_group(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text(
                """
name = "local-methodology"

[[artifact_types]]
name = "change-approved"

[[artifact_types]]
name = "change-needs-revision"

[[artifact_types]]
name = "review-audit"

[[outcome_types]]
name = "change-approved"

[[outcome_types]]
name = "change-needs-revision"

[[mechanics]]
name = "read-artifact"

[[protocols]]
name = "review"

[[protocols.required_output_choices]]
name = "review-disposition"
members = ["change-approved", "change-needs-revision"]
""".lstrip(),
                encoding="utf-8",
            )
            (root / "skills" / "orient").mkdir(parents=True)
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            contract = contracts / "review.toml"
            contract.write_text(
                (WORKFLOW_FIXTURES / "invalid-review-outcomes-with-audit-terminal.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            results = run_conformance([root])

        workflow_result = next(result for result in results if result.path == contract)
        self.assertEqual("C-2 workflow-contract", workflow_result.category)
        self.assertFalse(workflow_result.passed)
        self.assertIn("terminals/2/artifact_produced", " ".join(workflow_result.errors))

    def test_directory_workflow_contract_rejects_multiple_required_choice_groups(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text(
                """
name = "local-methodology"

[[artifact_types]]
name = "change-approved"

[[artifact_types]]
name = "change-needs-revision"

[[artifact_types]]
name = "change-aborted"

[[artifact_types]]
name = "change-escalated"

[[outcome_types]]
name = "change-approved"

[[outcome_types]]
name = "change-needs-revision"

[[outcome_types]]
name = "change-aborted"

[[outcome_types]]
name = "change-escalated"

[[mechanics]]
name = "read-artifact"

[[protocols]]
name = "review"

[[protocols.required_output_choices]]
name = "review-disposition"
members = ["change-approved", "change-needs-revision"]

[[protocols.required_output_choices]]
name = "review-closure"
members = ["change-aborted", "change-escalated"]
""".lstrip(),
                encoding="utf-8",
            )
            (root / "skills" / "orient").mkdir(parents=True)
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            contract = contracts / "review.toml"
            contract.write_text(
                (WORKFLOW_FIXTURES / "valid-review-outcomes.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            results = run_conformance([root])

        workflow_result = next(result for result in results if result.path == contract)
        self.assertEqual("C-2 workflow-contract", workflow_result.category)
        self.assertFalse(workflow_result.passed)
        self.assertIn("declares 2 manifest required_output_choices groups", " ".join(workflow_result.errors))

    def test_directory_mechanic_uses_self_contained_local_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text(
                """
name = "local-methodology"

[[artifact_types]]
name = "change-proposal"
""".lstrip(),
                encoding="utf-8",
            )
            mechanics = root / "mechanics"
            mechanics.mkdir()
            mechanic = mechanics / "produce-artifact.toml"
            mechanic.write_text((MECHANIC_FIXTURES / "valid-mcp-tool.toml").read_text(encoding="utf-8"), encoding="utf-8")

            results = run_conformance([root])

        mechanic_result = next(result for result in results if result.path == mechanic)
        self.assertEqual("C-3 mechanic", mechanic_result.category)
        self.assertFalse(mechanic_result.passed)
        self.assertIn("artifact schema `completion-evidence` does not resolve in registry", " ".join(mechanic_result.errors))

    def test_manifest_forge_tagged_mechanic_binding_requires_matching_c3_mechanic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.toml"
            manifest.write_text(
                """
[[forge_tags]]
name = "github"

[[mechanics]]
name = "deliver-change-proposal"
forge_tags = ["github"]
""".lstrip(),
                encoding="utf-8",
            )

            results = run_conformance([manifest])

        self.assertEqual(1, len(results))
        self.assertEqual("C-5 manifest", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn(
            "mechanic binding `deliver-change-proposal` for forge tag `github` resolves to 0 C-3 mechanics",
            " ".join(results[0].errors),
        )

    def test_manifest_forge_tagged_mechanic_binding_rejects_unknown_forge_tag(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.toml"
            manifest.write_text(
                """
[[mechanics]]
name = "deliver-change-proposal"
forge_tags = ["github"]
""".lstrip(),
                encoding="utf-8",
            )

            results = run_conformance([manifest])

        self.assertEqual(1, len(results))
        self.assertEqual("C-5 manifest", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("forge tag `github` does not resolve in forge_tags", " ".join(results[0].errors))

    def test_manifest_forge_tagged_mechanic_binding_rejects_duplicate_c3_mechanics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.toml"
            manifest.write_text(
                """
[[forge_tags]]
name = "github"

[[artifact_types]]
name = "change-proposal"

[[mechanics]]
name = "deliver-change-proposal"
forge_tags = ["github"]
""".lstrip(),
                encoding="utf-8",
            )
            mechanics = root / "mechanics"
            mechanics.mkdir()
            mechanic_source = (MECHANIC_FIXTURES / "valid-github.toml").read_text(encoding="utf-8")
            (mechanics / "one.toml").write_text(mechanic_source, encoding="utf-8")
            (mechanics / "two.toml").write_text(mechanic_source, encoding="utf-8")

            results = run_conformance([manifest])

        self.assertEqual(1, len(results))
        self.assertEqual("C-5 manifest", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn(
            "mechanic binding `deliver-change-proposal` for forge tag `github` resolves to 2 C-3 mechanics",
            " ".join(results[0].errors),
        )

    def test_manifest_forge_tagged_operation_requires_every_supported_forge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.toml"
            manifest.write_text(
                """
[[forge_tags]]
name = "github"

[[forge_tags]]
name = "sourcehut"

[[mechanics]]
name = "close-out"
forge_tags = ["github"]
""".lstrip(),
                encoding="utf-8",
            )
            (root / "mechanics" / "github").mkdir(parents=True)
            (root / "mechanics" / "github" / "close-out.toml").write_text(
                """
name = "close-out"
purpose = "Close GitHub work."
forge_tag = "github"
default_invocation = "true"
examples = ["true"]

[outcome]
description = "Closed."
""".lstrip(),
                encoding="utf-8",
            )

            results = run_conformance([manifest])

        self.assertEqual("C-5 manifest", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("mechanic `close-out` does not declare forge tag `sourcehut`", " ".join(results[0].errors))

    def test_manifest_no_leakage_rejects_forge_specific_body_for_operation_referencing_protocol(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text(
                """
[[artifact_types]]
name = "completion-record"

[[forge_tags]]
name = "github"

[[forge_tags]]
name = "sourcehut"

[[mechanics]]
name = "close-out"
forge_tags = ["github", "sourcehut"]
""".lstrip(),
                encoding="utf-8",
            )
            (root / "skills" / "orient").mkdir(parents=True)
            (root / "protocols" / "land").mkdir(parents=True)
            (root / "protocols" / "land" / "PROTOCOL.md").write_text(
                "# Land\n\nRun `gh issue close 350` after applying the change.\n",
                encoding="utf-8",
            )
            for forge in ["github", "sourcehut"]:
                (root / "mechanics" / forge).mkdir(parents=True)
                (root / "mechanics" / forge / "close-out.toml").write_text(
                    f"""
name = "close-out"
purpose = "Close {forge} work."
forge_tag = "{forge}"
default_invocation = "true"
examples = ["true"]

[outcome]
description = "Closed."
""".lstrip(),
                    encoding="utf-8",
                )
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            (contracts / "land.toml").write_text(
                """
name = "land"
purpose = "Close out approved work."
session_role = "release gate"
preconditions = ["approval exists"]
start_node = "close-out"
failure_modes = ["close-out fails"]
corruption_modes = ["forge leakage"]

[[nodes]]
name = "close-out"
intent = "Close out the work unit."
disciplines = ["orient"]
mechanics = ["close-out"]
outcomes = ["closed"]

[[edges]]
from = "close-out"
to = "completed"
condition = { type = "always" }

[[terminals]]
name = "completed"
outcome = "Closed."
artifact_produced = "completion-record"
""".lstrip(),
                encoding="utf-8",
            )

            results = run_conformance([root])

        manifest_result = next(result for result in results if result.path == root / "manifest.toml")
        self.assertFalse(manifest_result.passed)
        self.assertIn("forge-specific body leakage", " ".join(manifest_result.errors))

    def test_malformed_directory_manifest_does_not_abort_sibling_registry_checks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text("name = [\n", encoding="utf-8")
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            contract = contracts / "verify.toml"
            contract.write_text((WORKFLOW_FIXTURES / "valid-linear.toml").read_text(encoding="utf-8"), encoding="utf-8")

            results = run_conformance([root])

        self.assertEqual([root / "manifest.toml", contract], [result.path for result in results])
        self.assertFalse(all(result.passed for result in results))
        self.assertIn("invalid TOML", " ".join(error for result in results for error in result.errors))

    def test_malformed_local_manifest_registry_shape_does_not_abort_sibling_checks(self) -> None:
        cases = {
            "workflow-artifact-types": (
                "artifact_types = 7\n",
                "workflow-contracts",
                WORKFLOW_FIXTURES / "valid-linear.toml",
                "C-2 workflow-contract",
            ),
            "workflow-protocols": (
                "protocols = 7\n",
                "workflow-contracts",
                WORKFLOW_FIXTURES / "valid-linear.toml",
                "C-2 workflow-contract",
            ),
            "mechanic-artifact-types": (
                "artifact_types = 7\n",
                "mechanics",
                MECHANIC_FIXTURES / "valid-mcp-tool.toml",
                "C-3 mechanic",
            ),
        }
        for label, (manifest_source, unit_directory_name, fixture, expected_category) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "manifest.toml").write_text(manifest_source, encoding="utf-8")
                unit_directory = root / unit_directory_name
                unit_directory.mkdir()
                unit = unit_directory / "unit.toml"
                unit.write_text(fixture.read_text(encoding="utf-8"), encoding="utf-8")

                results = run_conformance([root])

                self.assertEqual([root / "manifest.toml", unit], [result.path for result in results])
                self.assertEqual(["C-5 manifest", expected_category], [result.category for result in results])
                self.assertTrue(all(not result.passed for result in results))
                self.assertIn("manifest registry could not be loaded", " ".join(results[1].errors))

    def test_direct_schema_directory_argument_validates_schema_definitions(self) -> None:
        results = run_conformance([SCHEMAS])

        self.assertGreater(len(results), 0)
        self.assertTrue(all(result.path.parent == SCHEMAS for result in results))
        self.assertTrue(all(result.category == "C-4 schema-definition" for result in results))
        self.assertTrue(all(result.passed for result in results))

    def test_direct_unit_directory_argument_reports_invalid_units(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            invalid = contracts / "invalid.toml"
            invalid.write_text(
                (WORKFLOW_FIXTURES / "invalid-malformed-shape.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

            results = run_conformance([contracts])

        self.assertEqual(1, len(results))
        self.assertEqual(invalid.resolve(), results[0].path)
        self.assertEqual("C-2 workflow-contract", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertTrue(results[0].errors)

    def test_explicit_non_unit_toml_path_fails_instead_of_silently_skipping(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "settings.toml"
            settings.write_text("name = \"example\"\n", encoding="utf-8")

            results = run_conformance([settings])

        self.assertEqual(1, len(results))
        self.assertEqual("unknown", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("unsupported conformance unit", results[0].errors)

    def test_cli_exit_code_reflects_aggregate_result(self) -> None:
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            passing = main([str(WORKFLOW_FIXTURES / "valid-linear.toml")])
        with contextlib.redirect_stdout(stdout):
            failing = main([str(WORKFLOW_FIXTURES / "invalid-malformed-shape.toml")])

        self.assertEqual(0, passing)
        self.assertEqual(1, failing)
        self.assertIn("PASS", stdout.getvalue())
        self.assertIn("FAIL", stdout.getvalue())

    def test_default_discovery_finds_schema_definitions_without_requiring_future_dirs(self) -> None:
        discovered = discover_units(ROOT)

        self.assertIn(ROOT / "manifest.toml", discovered)
        self.assertIn(SCHEMAS / "change-proposal.schema.json", discovered)
        self.assertIn(SCHEMAS / "change-approved.schema.json", discovered)
        self.assertIn(SCHEMAS / "change-needs-revision.schema.json", discovered)
        self.assertFalse(any("tests/fixtures" in path.as_posix() for path in discovered))

    def test_future_r1_contract_is_discovered_without_runner_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            contract = contracts / "verify.toml"
            contract.write_text((WORKFLOW_FIXTURES / "valid-linear.toml").read_text(encoding="utf-8"), encoding="utf-8")

            discovered = discover_units(root)
            results = run_conformance(discovered)

        self.assertEqual([contract], discovered)
        self.assertEqual(1, len(results))
        self.assertEqual("C-2 workflow-contract", results[0].category)
        self.assertTrue(results[0].passed)

    def test_manifest_dispatch_validates_registered_outcome_members_and_routing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.toml"
            manifest.write_text(
                """
name = "review-methodology"

[[artifact_types]]
name = "change-proposal"

[[artifact_types]]
name = "change-approved"

[[artifact_types]]
name = "change-needs-revision"

[[artifact_types]]
name = "completion-record"

[[outcome_types]]
name = "change-approved"

[[outcome_types]]
name = "change-needs-revision"

[[protocols]]
name = "review"
requires = ["change-proposal"]
trigger = { type = "on_artifact", name = "change-proposal" }

[[protocols.required_output_choices]]
name = "review-disposition"
members = ["change-approved", "change-needs-revision"]

[[protocols]]
name = "land"
requires = ["change-approved"]
produces = ["completion-record"]
trigger = { type = "on_artifact", name = "change-approved" }
""".lstrip(),
                encoding="utf-8",
            )

            results = run_conformance([manifest])

        self.assertEqual(1, len(results))
        self.assertEqual("C-5 manifest", results[0].category)
        self.assertTrue(results[0].passed)

    def test_manifest_dispatch_rejects_choice_member_outside_outcome_vocabulary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.toml"
            manifest.write_text(
                """
name = "review-methodology"

[[artifact_types]]
name = "change-approved"

[[artifact_types]]
name = "change-needs-revision"

[[outcome_types]]
name = "change-approved"

[[protocols]]
name = "review"
trigger = { type = "on_artifact", name = "change-approved" }

[[protocols.required_output_choices]]
name = "review-disposition"
members = ["change-approved", "change-needs-revision"]
""".lstrip(),
                encoding="utf-8",
            )

            results = run_conformance([manifest])

        self.assertEqual("C-5 manifest", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("is not registered in outcome_types", " ".join(results[0].errors))

    def test_manifest_dispatch_rejects_malformed_required_output_choices_declarations(self) -> None:
        cases = {
            "scalar": """
[[protocols]]
name = "review"
required_output_choices = "review-disposition"
""",
            "single-table": """
[[protocols]]
name = "review"

[protocols.required_output_choices]
name = "review-disposition"
members = ["change-approved", "change-needs-revision"]
""",
        }
        for label, toml_source in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                manifest = Path(directory) / "manifest.toml"
                manifest.write_text(toml_source.lstrip(), encoding="utf-8")

                results = run_conformance([manifest])

            self.assertEqual("C-5 manifest", results[0].category)
            self.assertFalse(results[0].passed)
            self.assertIn("protocols/0/required_output_choices", " ".join(results[0].errors))
            self.assertIn("must be an array of tables", " ".join(results[0].errors))

    def test_manifest_dispatch_rejects_malformed_known_shapes_it_reads(self) -> None:
        cases = {
            "artifact-types": (
                'artifact_types = "change-approved"\n',
                "artifact_types",
                "must be an array of tables",
            ),
            "outcome-types": (
                'outcome_types = "change-approved"\n',
                "outcome_types",
                "must be an array of tables",
            ),
            "protocols": (
                'protocols = "review"\n',
                "protocols",
                "must be an array of tables",
            ),
            "produces": (
                """
[[protocols]]
name = "review"
produces = "review-findings"

[[protocols.required_output_choices]]
name = "review-disposition"
members = ["change-approved", "change-needs-revision"]
""",
                "protocols/0/produces",
                "must be an array",
            ),
            "trigger": (
                """
[[protocols]]
name = "review"
trigger = "change-approved"
""",
                "protocols/0/trigger",
                "must be a table",
            ),
            "conditions": (
                """
[[protocols]]
name = "review"
trigger = { type = "all_of", conditions = "change-approved" }
""",
                "protocols/0/trigger/conditions",
                "must be an array of tables",
            ),
        }
        for label, (toml_source, error_path, message) in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                manifest = Path(directory) / "manifest.toml"
                manifest.write_text(toml_source.lstrip(), encoding="utf-8")

                results = run_conformance([manifest])

            self.assertEqual("C-5 manifest", results[0].category)
            self.assertFalse(results[0].passed)
            self.assertIn(error_path, " ".join(results[0].errors))
            self.assertIn(message, " ".join(results[0].errors))

    def test_manifest_dispatch_rejects_non_artifact_outcome_trigger_forms_and_composites(self) -> None:
        cases = {
            "on_change": 'trigger = { type = "on_change", name = "change-approved" }',
            "on_invalid": 'trigger = { type = "on_invalid", name = "change-approved" }',
            "all_of": (
                'trigger = { type = "all_of", conditions = ['
                ' { type = "on_change", name = "change-approved" }'
                " ] }"
            ),
            "any_of": (
                'trigger = { type = "any_of", conditions = ['
                ' { type = "on_invalid", name = "change-approved" }'
                " ] }"
            ),
        }
        for label, successor_trigger in cases.items():
            with self.subTest(label=label):
                results = self.run_manifest_conformance(self.review_outcome_manifest(successor_trigger))

            self.assertEqual("C-5 manifest", results[0].category)
            self.assertFalse(results[0].passed)
            self.assertIn("outcome trigger must use on_artifact", " ".join(results[0].errors))

    def test_manifest_dispatch_rejects_disposition_agnostic_successor_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.toml"
            manifest.write_text(
                """
name = "review-methodology"

[[artifact_types]]
name = "review-findings"

[[artifact_types]]
name = "change-approved"

[[artifact_types]]
name = "change-needs-revision"

[[outcome_types]]
name = "change-approved"

[[outcome_types]]
name = "change-needs-revision"

[[protocols]]
name = "review"
produces = ["review-findings"]
trigger = { type = "on_artifact", name = "review-findings" }

[[protocols.required_output_choices]]
name = "review-disposition"
members = ["change-approved", "change-needs-revision"]

[[protocols]]
name = "land"
trigger = { type = "on_artifact", name = "review-findings" }
""".lstrip(),
                encoding="utf-8",
            )

            results = run_conformance([manifest])

        self.assertEqual("C-5 manifest", results[0].category)
        self.assertFalse(results[0].passed)
        self.assertIn("successor routes on disposition-agnostic output", " ".join(results[0].errors))

    def test_manifest_dispatch_rejects_disposition_agnostic_change_and_invalid_triggers(self) -> None:
        cases = {
            "on_change": 'trigger = { type = "on_change", name = "review-findings" }',
            "on_invalid": 'trigger = { type = "on_invalid", name = "review-findings" }',
        }
        for label, successor_trigger in cases.items():
            with self.subTest(label=label):
                results = self.run_manifest_conformance(self.review_outcome_manifest(successor_trigger))

            self.assertEqual("C-5 manifest", results[0].category)
            self.assertFalse(results[0].passed)
            self.assertIn("successor routes on disposition-agnostic output", " ".join(results[0].errors))

    def test_manifest_dispatch_rejects_disposition_agnostic_composite_trigger(self) -> None:
        cases = {
            "all_of": (
                'trigger = { type = "all_of", conditions = ['
                ' { type = "on_change", name = "review-findings" },'
                ' { type = "on_artifact", name = "change-approved" }'
                " ] }"
            ),
            "any_of": (
                'trigger = { type = "any_of", conditions = ['
                ' { type = "on_change", name = "review-findings" },'
                ' { type = "on_artifact", name = "change-approved" }'
                " ] }"
            ),
        }
        for label, successor_trigger in cases.items():
            with self.subTest(label=label):
                results = self.run_manifest_conformance(self.review_outcome_manifest(successor_trigger))

            self.assertEqual("C-5 manifest", results[0].category)
            self.assertFalse(results[0].passed)
            self.assertIn("protocols/1/trigger/conditions/0", " ".join(results[0].errors))
            self.assertIn("successor routes on disposition-agnostic output", " ".join(results[0].errors))

    def test_manifest_dispatch_accepts_re_review_change_trigger_on_protocol_input(self) -> None:
        results = self.run_manifest_conformance(
            self.review_outcome_manifest('trigger = { type = "on_change", name = "change-proposal" }')
        )

        self.assertEqual("C-5 manifest", results[0].category)
        self.assertTrue(results[0].passed)
        self.assertEqual([], results[0].errors)

    def test_source_verify_workflow_contract_is_discovered_and_registry_validated(self) -> None:
        contract = ROOT / "workflow-contracts" / "verify.toml"

        discovered = discover_units(ROOT)
        self.assertIn(contract, discovered)

        results = run_conformance([contract])
        self.assertEqual(1, len(results))
        self.assertEqual("C-2 workflow-contract", results[0].category)
        self.assertTrue(results[0].passed)
        self.assertEqual([], results[0].errors)

    def test_source_review_workflow_contract_is_discovered_and_registry_validated(self) -> None:
        contract = ROOT / "workflow-contracts" / "review.toml"

        discovered = discover_units(ROOT)
        self.assertIn(contract, discovered)

        results = run_conformance([contract])
        self.assertEqual(1, len(results))
        self.assertEqual("C-2 workflow-contract", results[0].category)
        self.assertTrue(results[0].passed)
        self.assertEqual([], results[0].errors)

        with mock.patch(
            "tooling.conformance.workflow_registry_from_manifest",
            return_value=WorkflowRegistry(),
        ):
            registry_results = run_conformance([contract])

        self.assertEqual(1, len(registry_results))
        self.assertFalse(registry_results[0].passed)
        self.assertIn(
            "discipline `orient` does not resolve in registry",
            " ".join(registry_results[0].errors),
        )

    def test_source_submit_workflow_contract_is_discovered_and_registry_validated(self) -> None:
        contract = ROOT / "workflow-contracts" / "submit.toml"

        discovered = discover_units(ROOT)
        self.assertIn(contract, discovered)

        results = run_conformance([contract])
        self.assertEqual(1, len(results))
        self.assertEqual("C-2 workflow-contract", results[0].category)
        self.assertTrue(results[0].passed)
        self.assertEqual([], results[0].errors)

    def test_source_land_workflow_contract_is_discovered_and_registry_validated(self) -> None:
        contract = ROOT / "workflow-contracts" / "land.toml"

        discovered = discover_units(ROOT)
        self.assertIn(contract, discovered)

        results = run_conformance([contract])
        self.assertEqual(1, len(results))
        self.assertEqual("C-2 workflow-contract", results[0].category)
        self.assertTrue(results[0].passed)
        self.assertEqual([], results[0].errors)

    def test_bare_relative_workflow_contract_validates_from_contract_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            contracts = root / "workflow-contracts"
            contracts.mkdir()
            contract = contracts / "verify.toml"
            contract.write_text((WORKFLOW_FIXTURES / "valid-linear.toml").read_text(encoding="utf-8"), encoding="utf-8")

            original_cwd = Path.cwd()
            try:
                os.chdir(contracts)
                results = run_conformance([Path("verify.toml")])
            finally:
                os.chdir(original_cwd)

        self.assertEqual(1, len(results))
        self.assertEqual("C-2 workflow-contract", results[0].category)
        self.assertTrue(results[0].passed)


if __name__ == "__main__":
    unittest.main()
