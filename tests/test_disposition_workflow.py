from pathlib import Path
import re
import tomllib
import unittest

from tooling.workflow_contracts import load_workflow_contract, workflow_registry_from_manifest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.toml"
LAND_CONTRACT_PATH = ROOT / "workflow-contracts" / "land.toml"
LAND_PROTOCOL_PATH = ROOT / "protocols" / "land" / "PROTOCOL.md"


def load_manifest() -> dict:
    return tomllib.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def protocol_named(name: str) -> dict:
    return next(protocol for protocol in load_manifest()["protocols"] if protocol["name"] == name)


def normalized(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


class DispositionWorkflowTests(unittest.TestCase):
    def test_live_workflow_routes_submit_review_land_through_disposition_artifacts(self) -> None:
        submit = protocol_named("submit")
        review = protocol_named("review")
        land = protocol_named("land")

        self.assertEqual(["change-proposal"], submit["produces"])
        self.assertEqual(["change-proposal"], review["requires"])
        self.assertEqual({"type": "on_change", "name": "change-proposal"}, review["trigger"])
        self.assertEqual(["change-approved"], land["requires"])
        self.assertEqual({"type": "on_artifact", "name": "change-approved"}, land["trigger"])
        self.assertEqual(["completion-record"], land["produces"])

    def test_revision_outcome_reactivates_submit_without_patch_type(self) -> None:
        manifest = load_manifest()
        submit = protocol_named("submit")
        artifact_types = {entry["name"] for entry in manifest["artifact_types"]}
        trigger_conditions = submit["trigger"]["conditions"]

        self.assertNotIn("patch", artifact_types)
        self.assertEqual(["change-proposal", "change-needs-revision"], submit["accepts"])
        self.assertIn({"type": "on_artifact", "name": "change-needs-revision"}, trigger_conditions)

    def test_land_contract_is_forge_invariant_and_produces_completion_record(self) -> None:
        contract = load_workflow_contract(LAND_CONTRACT_PATH, registry=workflow_registry_from_manifest())
        mechanics = {
            mechanic
            for node in contract["nodes"]
            for mechanic in node["mechanics"]
        }
        serialized = normalized(LAND_CONTRACT_PATH).lower()

        self.assertEqual("land", contract["name"])
        self.assertEqual({"completion-record"}, {terminal["artifact_produced"] for terminal in contract["terminals"]})
        self.assertEqual({"apply-approved-change", "reflect-disposition", "close-out"}, mechanics)
        for forbidden in ["patch", "pr-merge", "merge", "github", "sourcehut", "forge", "`gh", "gh pr"]:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized)

    def test_land_protocol_doc_preserves_completion_record_delivery_contract(self) -> None:
        body = normalized(LAND_PROTOCOL_PATH)

        self.assertIn("change-approved", body)
        self.assertIn("completion-record", body)
        self.assertIn("`completion-record` MCP tool", body)
        self.assertIn("MCP tool input, not artifact body", body)
        self.assertIn("Runa injects `work_unit` from session context", body)
        self.assertNotIn("`patch` MCP tool", body)


if __name__ == "__main__":
    unittest.main()
