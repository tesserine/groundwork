import tempfile
import unittest
from pathlib import Path

from tooling.mechanics import load_mechanic
from tooling.workflow_contracts import (
    WorkflowContractError,
    WorkflowRegistry,
    load_workflow_contract,
    validate_workflow_contract,
    workflow_registry_from_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "workflow-contracts"
MECHANIC_FIXTURES = ROOT / "tests" / "fixtures" / "mechanics"


class WorkflowContractTests(unittest.TestCase):
    def fixture(self, name: str) -> Path:
        return FIXTURES / name

    def test_schema_accepts_linear_branching_loop_and_multi_terminal_contracts(self) -> None:
        for name in [
            "valid-linear.toml",
            "valid-branching.toml",
            "valid-loop.toml",
            "valid-multiple-terminals.toml",
        ]:
            with self.subTest(fixture=name):
                contract = load_workflow_contract(self.fixture(name))

                self.assertIsInstance(contract, dict)

    def test_schema_rejects_malformed_shape_with_field_path(self) -> None:
        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-malformed-shape.toml"))

        self.assertIn("nodes/0/name", context.exception.paths)
        self.assertIn("nodes/0/name", str(context.exception))

    def test_parser_rejects_unknown_edge_endpoint_with_graph_message(self) -> None:
        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-unknown-endpoint.toml"))

        self.assertIn("edges/0/to", context.exception.paths)
        self.assertIn("edge `inspect -> missing-terminal` references unknown target `missing-terminal`", str(context.exception))

    def test_parser_rejects_disconnected_nodes(self) -> None:
        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-disconnected.toml"))

        self.assertIn("nodes/1", context.exception.paths)
        self.assertIn("node `orphaned` is not reachable from start_node `inspect`", str(context.exception))

    def test_parser_rejects_reachable_dead_end_nodes(self) -> None:
        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-dead-end.toml"))

        self.assertIn("nodes/2", context.exception.paths)
        self.assertIn("node `push-new-pr` cannot reach any terminal", str(context.exception))

    def test_parser_rejects_node_terminal_name_collisions(self) -> None:
        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-name-collision.toml"))

        self.assertIn("terminals/0/name", context.exception.paths)
        self.assertIn("name `review` is declared as both a node and a terminal", str(context.exception))

    def test_parser_rejects_overlapping_conditions_from_one_node(self) -> None:
        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-overlapping-conditions.toml"))

        self.assertIn("edges/1/condition", context.exception.paths)
        self.assertIn(
            "node `resolve-pr-delivery-path` has overlapping conditions on outgoing edges",
            str(context.exception),
        )

    def test_parser_rejects_loop_without_termination_edge(self) -> None:
        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-unterminated-loop.toml"))

        self.assertIn("edges", context.exception.paths)
        self.assertIn("loop `red, green` has no termination edge", str(context.exception))

    def test_registry_resolution_can_be_deferred_when_no_registry_is_loaded(self) -> None:
        contract = load_workflow_contract(self.fixture("valid-linear.toml"), registry=None)

        self.assertEqual(contract["name"], "verify")

    def test_registry_resolution_rejects_unknown_references_when_registry_is_loaded(self) -> None:
        registry = WorkflowRegistry(
            disciplines={"orient"},
            mechanics={"read-artifact"},
            artifact_schemas={"completion-evidence"},
        )

        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-registry-reference.toml"), registry=registry)

        self.assertIn("nodes/0/disciplines/1", context.exception.paths)
        self.assertIn("discipline `missing-discipline` does not resolve in registry", str(context.exception))

    def test_outcome_terminals_match_manifest_required_output_choice_members(self) -> None:
        registry = WorkflowRegistry(
            disciplines={"orient"},
            mechanics={"read-artifact"},
            artifact_schemas={"change-approved", "change-needs-revision"},
            outcome_types={"change-approved", "change-needs-revision"},
            required_output_choices={
                "review": [{"name": "review-disposition", "members": ["change-approved", "change-needs-revision"]}]
            },
        )

        contract = load_workflow_contract(
            self.fixture("valid-review-outcomes.toml"),
            registry=registry,
        )

        self.assertEqual("review", contract["name"])

    def test_outcome_terminals_reject_non_member_terminal_when_manifest_declares_choice_members(self) -> None:
        registry = WorkflowRegistry(
            disciplines={"orient"},
            mechanics={"read-artifact"},
            artifact_schemas={"change-approved", "change-needs-revision", "review-audit"},
            outcome_types={"change-approved", "change-needs-revision"},
            required_output_choices={
                "review": [{"name": "review-disposition", "members": ["change-approved", "change-needs-revision"]}]
            },
        )

        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(
                self.fixture("invalid-review-outcomes-with-audit-terminal.toml"),
                registry=registry,
            )

        self.assertIn("terminals/2/artifact_produced", context.exception.paths)
        self.assertIn("not a member of manifest required_output_choices `review-disposition`", str(context.exception))

    def test_outcome_terminals_reject_shared_record_type_when_manifest_declares_choice_members(self) -> None:
        registry = WorkflowRegistry(
            disciplines={"orient"},
            mechanics={"read-artifact"},
            artifact_schemas={"review-findings", "change-approved", "change-needs-revision"},
            outcome_types={"change-approved", "change-needs-revision"},
            required_output_choices={
                "review": [{"name": "review-disposition", "members": ["change-approved", "change-needs-revision"]}]
            },
        )

        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-shared-record-type-outcomes.toml"), registry=registry)

        self.assertIn("terminals/0/artifact_produced", context.exception.paths)
        self.assertIn("terminals/1/artifact_produced", context.exception.paths)
        self.assertIn("not a member of manifest required_output_choices `review-disposition`", str(context.exception))

    def test_review_shared_record_type_guard_fixture_stays_invalid(self) -> None:
        registry = workflow_registry_from_manifest()

        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("invalid-shared-record-type-outcomes.toml"), registry=registry)

        self.assertIn("not a member of manifest required_output_choices `review-disposition`", str(context.exception))

    def test_outcome_terminals_reject_manifest_group_divergence(self) -> None:
        registry = WorkflowRegistry(
            disciplines={"orient"},
            mechanics={"read-artifact"},
            artifact_schemas={"change-approved", "change-needs-revision", "review-audit", "change-rejected"},
            outcome_types={"change-approved", "change-needs-revision", "change-rejected"},
            required_output_choices={
                "review": [{"name": "review-disposition", "members": ["change-approved", "change-rejected"]}]
            },
        )

        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(
                self.fixture("valid-review-outcomes.toml"),
                registry=registry,
            )

        self.assertIn("terminals", context.exception.paths)
        self.assertIn("do not match outcome terminal artifact_produced values", str(context.exception))

    def test_outcome_terminals_reject_multiple_manifest_choice_groups(self) -> None:
        registry = WorkflowRegistry(
            disciplines={"orient"},
            mechanics={"read-artifact"},
            artifact_schemas={"change-approved", "change-needs-revision", "change-aborted", "change-escalated"},
            outcome_types={"change-approved", "change-needs-revision", "change-aborted", "change-escalated"},
            required_output_choices={
                "review": [
                    {"name": "review-disposition", "members": ["change-approved", "change-needs-revision"]},
                    {"name": "review-closure", "members": ["change-aborted", "change-escalated"]},
                ]
            },
        )

        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("valid-review-outcomes.toml"), registry=registry)

        self.assertIn("terminals", context.exception.paths)
        self.assertIn("declares 2 manifest required_output_choices groups", str(context.exception))

    def test_parser_registries_resolve_mechanic_names_across_parsers(self) -> None:
        mechanic = load_mechanic(MECHANIC_FIXTURES / "valid-github.toml")
        registry = WorkflowRegistry(
            disciplines={"orient"},
            mechanics={mechanic["name"]},
            artifact_schemas={"change-proposal"},
        )

        contract = load_workflow_contract(self.fixture("valid-mechanic-smoke.toml"), registry=registry)

        self.assertEqual("submit-smoke", contract["name"])

        renamed_registry = WorkflowRegistry(
            disciplines={"orient"},
            mechanics={f"{mechanic['name']}-renamed"},
            artifact_schemas={"change-proposal"},
        )
        with self.assertRaises(WorkflowContractError) as context:
            load_workflow_contract(self.fixture("valid-mechanic-smoke.toml"), registry=renamed_registry)

        self.assertIn("nodes/0/mechanics/0", context.exception.paths)
        self.assertIn("mechanic `deliver-change-proposal` does not resolve in registry", str(context.exception))

    def test_registry_from_manifest_resolves_nested_mechanic_directory_names(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "skills" / "orient").mkdir(parents=True)
            nested_mechanics = root / "mechanics" / "delivery"
            nested_mechanics.mkdir(parents=True)
            (nested_mechanics / "valid-github.toml").write_text(
                (MECHANIC_FIXTURES / "valid-github.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            manifest = root / "manifest.toml"
            manifest.write_text(
                """
[[artifact_types]]
name = "change-proposal"
""".lstrip(),
                encoding="utf-8",
            )

            registry = workflow_registry_from_manifest(manifest, root=root)
            self.assertIn("deliver-change-proposal", registry.mechanics)
            contract = load_workflow_contract(self.fixture("valid-mechanic-smoke.toml"), registry=registry)

        self.assertEqual("submit-smoke", contract["name"])

    def test_registry_from_manifest_carries_active_forge_resolved_mechanics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for forge_tag in ("github", "sourcehut"):
                mechanic = root / "mechanics" / forge_tag / "deliver-change-proposal.toml"
                mechanic.parent.mkdir(parents=True, exist_ok=True)
                mechanic.write_text(
                    f"""
name = "deliver-change-proposal"
purpose = "{forge_tag} delivery"
forge_tag = "{forge_tag}"
default_invocation = "printf {forge_tag}"
examples = ["printf {forge_tag}"]
parameters = []

[outcome]
description = "delivered"
""".lstrip(),
                    encoding="utf-8",
                )
            manifest = root / "manifest.toml"
            manifest.write_text(
                """
[[forge_tags]]
name = "github"

[[forge_tags]]
name = "sourcehut"

[[mechanics]]
name = "deliver-change-proposal"
forge_tags = ["github", "sourcehut"]
""".lstrip(),
                encoding="utf-8",
            )

            registry = workflow_registry_from_manifest(manifest, root=root, forge="sourcehut")

        self.assertEqual("sourcehut", registry.active_forge)
        self.assertEqual("printf sourcehut", registry.resolved_mechanics["deliver-change-proposal"]["default_invocation"])

    def test_validate_workflow_contract_accepts_already_loaded_toml_data(self) -> None:
        contract = load_workflow_contract(self.fixture("valid-linear.toml"))

        validate_workflow_contract(contract)

    def test_invalid_toml_reports_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.toml"
            path.write_text("name = [\n", encoding="utf-8")

            with self.assertRaises(WorkflowContractError) as context:
                load_workflow_contract(path)

        self.assertEqual(["<toml>"], context.exception.paths)
        self.assertIn("bad.toml is invalid TOML", str(context.exception))


if __name__ == "__main__":
    unittest.main()
