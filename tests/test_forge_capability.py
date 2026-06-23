import json
import subprocess
import sys
import unittest
from pathlib import Path

from tooling.artifact_schemas import validate_artifact


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
MATERIALIZE = ROOT / "skills" / "acquire" / "scripts" / "materialize.py"
FORGE_OPERATIONS = {
    "read-ticket",
    "create-ticket",
    "claim-work-unit",
    "record-progress",
    "deliver-change-proposal",
    "reflect-disposition",
    "apply-approved-change",
    "close-out",
}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class ForgeCapabilityContractTests(unittest.TestCase):
    def test_vendored_forge_capability_schema_records_immutable_provenance(self) -> None:
        schema = load_json(SCHEMAS / "forge-capability.schema.json")

        self.assertEqual(
            {
                "version": "1.1.0",
                "schema_url": (
                    "https://raw.githubusercontent.com/tesserine/commons/"
                    "6924159fc4ff58745f0e2c68ed16849ffd9b4086/"
                    "schemas/forge-capability/v1/forge-capability.schema.json"
                ),
                "prose_url": (
                    "https://raw.githubusercontent.com/tesserine/commons/"
                    "6924159fc4ff58745f0e2c68ed16849ffd9b4086/FORGE-CAPABILITY.md"
                ),
            },
            schema["x-tesserine-canonical"],
        )
        self.assertEqual("forge", schema["properties"]["capability"]["const"])
        self.assertEqual("1.1.0", schema["properties"]["version"]["const"])
        self.assertEqual("#/$defs/handle", schema["properties"]["handle_schema"]["const"])

    def test_artifact_handle_schemas_consult_the_vendored_handle_definition(self) -> None:
        forge_schema = load_json(SCHEMAS / "forge-capability.schema.json")
        handle_schema = forge_schema["$defs"]["handle"]

        for schema_name in ("work-unit.schema.json", "change-proposal.schema.json"):
            with self.subTest(schema=schema_name):
                schema = load_json(SCHEMAS / schema_name)
                self.assertEqual("#/$defs/handle", schema["properties"]["handle"]["$ref"])
                self.assertEqual(handle_schema, schema["$defs"]["handle"])
                self.assertNotIn("github-handle", schema.get("$defs", {}))
                self.assertNotIn("sourcehut-handle", schema.get("$defs", {}))

    def test_artifact_schemas_accept_opaque_handles_and_reject_provider_shapes(self) -> None:
        work_unit = {
            "title": "Opaque work unit",
            "description": "A connector-issued handle backs this work unit.",
            "acceptance_criteria": ["The handle conforms to the forge capability contract."],
            "handle": {"id": "tenant-alpha:tracker-main:ticket-blue", "display": "GW-blue"},
        }
        validate_artifact("work-unit", work_unit)

        proposal = {
            "work_unit": "work-unit-issue-440",
            "branch": "issue-440/forge-capability",
            "commit": "abc123",
            "base": "main",
            "summary": "Consume forge capability",
            "version": 1,
            "handle": {"id": "tenant-alpha:proposal:review-blue", "display": "review-blue"},
        }
        validate_artifact("change-proposal", proposal)

        for artifact_type, artifact in (
            (
                "work-unit",
                {
                    **work_unit,
                    "handle": {
                        "forge_tag": "github",
                        "url": "https://github.com/tesserine/groundwork/issues/440",
                        "number": 440,
                    },
                },
            ),
            (
                "change-proposal",
                {
                    **proposal,
                    "handle": {
                        "forge_tag": "sourcehut",
                        "proposal_ref": "refs/proposals/issue-440/1",
                    },
                },
            ),
        ):
            with self.subTest(artifact_type=artifact_type):
                with self.assertRaises(Exception):
                    validate_artifact(artifact_type, artifact)

    def test_manifest_forge_operations_are_capability_operations_not_provider_bindings(self) -> None:
        manifest = (ROOT / "manifest.toml").read_text(encoding="utf-8")
        for forbidden in ("[[forge_tags]]", "forge_tags", "github", "sourcehut"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, manifest)

        for operation in FORGE_OPERATIONS:
            with self.subTest(operation=operation):
                self.assertIn(f'name = "{operation}"', manifest)

    def test_provider_forge_mechanics_and_dispatch_are_retired(self) -> None:
        self.assertFalse((ROOT / "mechanics" / "github").exists())
        self.assertFalse((ROOT / "mechanics" / "sourcehut").exists())
        self.assertFalse((ROOT / "tooling" / "forge_operations.py").exists())
        self.assertFalse((ROOT / "scripts" / "groundwork-mechanic").exists())

    def test_acquire_materializer_accepts_non_numeric_opaque_handles(self) -> None:
        snapshot = {
            "handle": {
                "id": "tenant-alpha:tracker-main:ticket-blue",
                "display": "tracker main ticket blue",
            },
            "title": "task(connectors): consume opaque handle",
            "body": (
                "Connector issued handles are opaque.\n\n"
                "## Acceptance criteria\n\n"
                "- The materializer accepts non-numeric handles\n"
            ),
            "state": "open",
        }

        result = subprocess.run(
            [sys.executable, str(MATERIALIZE)],
            input=json.dumps(snapshot),
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        validate_artifact("work-unit", payload["artifact"])
        self.assertEqual(snapshot["handle"], payload["artifact"]["handle"])
        self.assertRegex(
            payload["instance_id"],
            r"^work-unit-[0-9a-f]{12}-task-connectors-consume-opaque-handle$",
        )
