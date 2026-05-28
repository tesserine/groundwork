import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

from tooling.conformance import discover_units, main, run_conformance


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"
MECHANIC_FIXTURES = ROOT / "tests" / "fixtures" / "mechanics"
WORKFLOW_FIXTURES = ROOT / "tests" / "fixtures" / "workflow-contracts"
SCHEMAS = ROOT / "schemas"


class ConformanceTests(unittest.TestCase):
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

        self.assertIn(SCHEMAS / "change-proposal.schema.json", discovered)
        self.assertIn(SCHEMAS / "review-findings.schema.json", discovered)
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
