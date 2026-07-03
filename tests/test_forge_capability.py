import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from tooling.artifact_schemas import ArtifactSchemaError, validate_artifact
from tooling.forge_capability import CAPABILITY_PROVENANCE_URL, CAPABILITY_VERSION
from tooling.conformance import run_conformance
from tooling.prose_conformance import manifest, schema_def
from tooling.workflow_contracts import workflow_registry_from_manifest


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
VENDORED_SCHEMA = SCHEMAS / "forge-capability" / "v1" / "forge-capability.schema.json"
EXPECTED_OPERATIONS = {
    "read-ticket",
    "create-ticket",
    "claim-work-unit",
    "record-progress",
    "deliver-change-proposal",
    "reflect-disposition",
    "apply-approved-change",
    "close-out",
}
RETIRED_FORGE_ASSETS = [
    ROOT / "mechanics" / "github",
    ROOT / "mechanics" / "sourcehut",
    ROOT / "tooling" / "forge_operations.py",
    ROOT / "scripts" / "groundwork-mechanic",
]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def vendored_schema() -> dict:
    return load_json(VENDORED_SCHEMA)


def connector_handle() -> dict:
    return {"id": "ticket:opaque-alpha", "display": "TRACK-ALPHA"}


def contains_key(node: object, key: str) -> bool:
    if isinstance(node, dict):
        return key in node or any(contains_key(value, key) for value in node.values())
    if isinstance(node, list):
        return any(contains_key(value, key) for value in node)
    return False


class ForgeCapabilityTests(unittest.TestCase):
    def test_capability_schema_is_vendored_with_immutable_provenance(self) -> None:
        schema = vendored_schema()

        self.assertEqual("forge", schema["properties"]["capability"]["const"])
        self.assertEqual(CAPABILITY_VERSION, schema["properties"]["version"]["const"])
        self.assertEqual("#/$defs/handle", schema["properties"]["handle_schema"]["const"])
        self.assertEqual(
            {
                "version": CAPABILITY_VERSION,
                "schema_url": CAPABILITY_PROVENANCE_URL,
            },
            schema["x-tesserine-canonical"],
        )

    def test_operation_surface_derives_from_vendored_schema(self) -> None:
        schema = vendored_schema()
        operation_names = set(schema["$defs"]["operation-name"]["enum"])
        tool_operations = {
            schema["$defs"][name]["allOf"][1]["properties"]["operation"]["const"]
            for name in schema["$defs"]
            if name.endswith("-tool") and name != "tool"
        }
        registry = workflow_registry_from_manifest()

        self.assertEqual(EXPECTED_OPERATIONS, operation_names)
        self.assertEqual(operation_names, tool_operations)
        self.assertTrue(operation_names.issubset(registry.mechanics))

    def test_artifact_handle_schemas_are_self_contained_copies_of_the_vendored_handle(self) -> None:
        handle_schema = vendored_schema()["$defs"]["handle"]

        for schema_name in ["work-unit.schema.json", "change-proposal.schema.json"]:
            with self.subTest(schema=schema_name):
                artifact_schema = load_json(SCHEMAS / schema_name)
                self.assertEqual(handle_schema, artifact_schema["$defs"]["handle"])
                self.assertEqual({"$ref": "#/$defs/handle"}, artifact_schema["properties"]["handle"])
                if schema_name == "work-unit.schema.json":
                    self.assertIn("handle", artifact_schema["required"])

    def test_work_unit_and_change_proposal_accept_only_connector_handles(self) -> None:
        work_unit = {
            "title": "Opaque connector work",
            "description": "## Acceptance criteria\n- [ ] Prove the handle shape",
            "acceptance_criteria": ["Prove the handle shape"],
            "handle": connector_handle(),
        }
        change_proposal = {
            "work_unit": "work-unit-abc",
            "branch": "issue-440/capability",
            "commit": "abc123",
            "base": "main",
            "summary": "Use connector handle.",
            "version": 1,
            "handle": {"id": "proposal:opaque-alpha:v1", "display": "PR alpha"},
        }

        validate_artifact("work-unit", work_unit)
        validate_artifact("change-proposal", change_proposal)

        work_unit["handle"] = {
            "forge_tag": "github",
            "url": "https://github.com/tesserine/groundwork/issues/440",
            "number": 440,
        }
        change_proposal["handle"] = {
            "forge_tag": "sourcehut",
            "proposal_ref": "refs/proposals/issue-440/1",
        }
        for artifact_type, artifact in [("work-unit", work_unit), ("change-proposal", change_proposal)]:
            with self.subTest(artifact_type=artifact_type):
                with self.assertRaises(ArtifactSchemaError):
                    validate_artifact(artifact_type, artifact)

    def test_conformance_discovers_and_checks_nested_vendored_schema(self) -> None:
        results = run_conformance([SCHEMAS])
        checked_paths = {result.path for result in results}

        self.assertIn(VENDORED_SCHEMA.resolve(), checked_paths)
        self.assertTrue(all(result.passed for result in results))

    def test_source_manifest_retains_non_forge_mechanics_and_no_provider_forge_mechanics(self) -> None:
        parsed_manifest = manifest(ROOT)
        registry = workflow_registry_from_manifest()

        for mechanic in ["read-artifact", "inspect-change-proposals", "revise", "review", "inspect-worktree", "run-test"]:
            with self.subTest(mechanic=mechanic):
                self.assertIn(mechanic, registry.mechanics)
        self.assertFalse(contains_key(parsed_manifest, "forge_tags"))
        for path in RETIRED_FORGE_ASSETS:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertFalse(path.exists())

    def test_methodology_docs_present_connector_model_without_retired_mechanism(self) -> None:
        schema = vendored_schema()
        operations = schema["$defs"]["operation-name"]["enum"]
        documents = [
            ROOT / "README.md",
            ROOT / "schemas" / "README.md",
            ROOT / "docs" / "architecture" / "connecting-structure.md",
            ROOT / "docs" / "architecture" / "decisions" / "0002-methodology-sovereignty.md",
            ROOT / "docs" / "architecture" / "decisions" / "0004-contract-first-scoped-pipeline.md",
            ROOT / "docs" / "architecture" / "decisions" / "0006-runtime-driven-self-install-surface.md",
            ROOT / "skills" / "acquire" / "SKILL.md",
            ROOT / "protocols" / "decompose" / "PROTOCOL.md",
            ROOT / "protocols" / "submit" / "PROTOCOL.md",
            ROOT / "protocols" / "land" / "PROTOCOL.md",
            ROOT / "protocols" / "take" / "references" / "workspace.md",
        ]

        combined = "\n".join(document.read_text(encoding="utf-8") for document in documents)
        for operation in operations:
            with self.subTest(operation=operation):
                self.assertIn(operation, combined)
        for path in RETIRED_FORGE_ASSETS:
            with self.subTest(retired_asset=path.relative_to(ROOT)):
                self.assertFalse(path.exists())

    def test_land_protocol_maps_apply_input_to_vendored_connector_schema(self) -> None:
        schema = vendored_schema()
        apply_input = schema["$defs"]["apply-approved-change-input"]
        proposal = load_json(SCHEMAS / "change-proposal.schema.json")
        body = (ROOT / "protocols" / "land" / "PROTOCOL.md").read_text(encoding="utf-8")

        for field in apply_input["required"]:
            with self.subTest(field=field):
                self.assertIn(f"`{field}`", body)
        self.assertIn("branch", proposal["required"])
        self.assertNotIn("branch", apply_input["required"])

    def test_methodology_docs_preserve_connector_model_coherence(self) -> None:
        handle_schema = vendored_schema()["$defs"]["handle"]
        work_unit_schema = load_json(SCHEMAS / "work-unit.schema.json")
        connecting_structure = (ROOT / "docs" / "architecture" / "connecting-structure.md").read_text(encoding="utf-8")
        adr_0006 = (
            ROOT / "docs" / "architecture" / "decisions" / "0006-runtime-driven-self-install-surface.md"
        ).read_text(encoding="utf-8")

        self.assertEqual(handle_schema, work_unit_schema["$defs"]["handle"])
        for field in handle_schema["required"]:
            with self.subTest(handle_field=field):
                self.assertIn(field, connecting_structure)
        self.assertRegex(adr_0006, r"`~/.groundwork` is a self-contained\s+methodology layout")
        self.assertIn("`schemas/{artifact_type}.schema.json`", adr_0006)
        self.assertIn("`protocols/{name}/PROTOCOL.md`", adr_0006)
        for path in RETIRED_FORGE_ASSETS:
            with self.subTest(retired_asset=path.relative_to(ROOT)):
                self.assertFalse(path.exists())

    def test_read_ticket_output_schema_declares_connector_handle(self) -> None:
        schema = vendored_schema()
        ticket_snapshot_ref = schema["$defs"]["read-ticket-tool"]["allOf"][1]["properties"]["output_schema"]["const"]
        ticket_snapshot = schema_def(schema, ticket_snapshot_ref)

        handle = connector_handle()
        snapshot = {
            "handle": handle,
            "title": "Opaque ticket",
            "body": "## Acceptance criteria\n- [ ] Materialize opaque ticket",
            "state": "open",
        }
        Draft202012Validator(schema).evolve(schema=ticket_snapshot).validate(snapshot)
        snapshot["comments"] = [
            {"body": "Freshen record."},
            {
                "body": "Review round 2: required correction.",
                "author": "operator",
                "created_at": "2026-07-02T10:53:26Z",
            },
        ]
        Draft202012Validator(schema).evolve(schema=ticket_snapshot).validate(snapshot)

    def test_entry_surfaces_ground_on_the_whole_ticket(self) -> None:
        acquire = (ROOT / "skills" / "acquire" / "SKILL.md").read_text(encoding="utf-8")
        take = (ROOT / "protocols" / "take" / "PROTOCOL.md").read_text(encoding="utf-8")

        for token in [
            "`comments`",
            "entry context",
            "never persisted into the artifact",
            "`log-blindness`",
        ]:
            with self.subTest(surface="acquire", token=token):
                self.assertIn(token, acquire)

        for token in [
            "comment log",
            "newest review directives at the submitted head",
            "`stale-directive-followership`",
        ]:
            with self.subTest(surface="take", token=token):
                self.assertIn(token, take)


if __name__ == "__main__":
    unittest.main()
