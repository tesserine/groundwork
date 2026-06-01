from pathlib import Path
import re
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.toml"
SUBMIT_CONTRACT_PATH = ROOT / "workflow-contracts" / "submit.toml"
SUBMIT_PROTOCOL_PATH = ROOT / "protocols" / "submit" / "PROTOCOL.md"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"


def load_manifest() -> dict:
    return tomllib.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def submit_protocol() -> dict:
    manifest = load_manifest()
    return next(protocol for protocol in manifest["protocols"] if protocol["name"] == "submit")


def normalized(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


class SubmitProtocolTests(unittest.TestCase):
    def test_submit_contract_exists_and_produces_change_proposal(self) -> None:
        contract = tomllib.loads(SUBMIT_CONTRACT_PATH.read_text(encoding="utf-8"))

        self.assertEqual("submit", contract["name"])
        self.assertEqual({"change-proposal"}, {terminal["artifact_produced"] for terminal in contract["terminals"]})

    def test_submit_contract_uses_only_forge_invariant_delivery_operations(self) -> None:
        contract = tomllib.loads(SUBMIT_CONTRACT_PATH.read_text(encoding="utf-8"))
        mechanics = {
            mechanic
            for node in contract["nodes"]
            for mechanic in node["mechanics"]
        }
        serialized = normalized(SUBMIT_CONTRACT_PATH)

        self.assertIn("deliver-change-proposal", mechanics)
        self.assertIn("revise", mechanics)
        self.assertNotIn("patch", serialized)
        for forbidden in ["create-pr", "pr-merge", "github", "sourcehut", "`gh", "gh pr"]:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, serialized.lower())

    def test_manifest_routes_submit_to_change_proposal_not_patch(self) -> None:
        protocol = submit_protocol()
        mechanic_names = {mechanic["name"] for mechanic in load_manifest()["mechanics"]}

        self.assertEqual(["completion-evidence", "documentation-record"], protocol["requires"])
        self.assertEqual(["change-proposal", "change-needs-revision"], protocol["accepts"])
        self.assertEqual(["change-proposal"], protocol["produces"])
        self.assertEqual([], protocol["may_produce"])
        self.assertEqual({"type": "on_artifact", "name": "documentation-record"}, protocol["trigger"])
        self.assertIn("deliver-change-proposal", mechanic_names)
        self.assertIn("revise", mechanic_names)

    def test_submit_keeps_protocol_doc_for_release_metadata(self) -> None:
        body = normalized(SUBMIT_PROTOCOL_PATH)

        self.assertIn("change-proposal", body)
        self.assertIn("`change-proposal` MCP tool", body)
        self.assertIn("MCP tool input, not artifact body", body)
        self.assertIn("Runa injects `work_unit` from session context", body)
        self.assertNotIn("`patch` MCP tool", body)

    def test_changelog_records_submit_contract_conversion(self) -> None:
        changelog = normalized(CHANGELOG_PATH)

        self.assertIn("Submit C-2 workflow contract", changelog)
        self.assertIn("change-proposal", changelog)
        self.assertIn("closes #330", changelog)


if __name__ == "__main__":
    unittest.main()
