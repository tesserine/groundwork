import unittest
from pathlib import Path

from tooling.prose_conformance import (
    artifact_schema,
    delivery_boundaries,
    manifest_protocols,
    markdown_section,
    read,
)


ROOT = Path(__file__).resolve().parents[1]
SUBMIT_PROTOCOL = ROOT / "protocols" / "submit" / "PROTOCOL.md"
REVIEW_PROTOCOL = ROOT / "protocols" / "review" / "PROTOCOL.md"
LAND_PROTOCOL = ROOT / "protocols" / "land" / "PROTOCOL.md"


def protocol(name: str) -> dict:
    return {entry["name"]: entry for entry in manifest_protocols(ROOT)}[name]


class CloseProtocolContractDimensionTests(unittest.TestCase):
    def test_manifest_threads_close_protocols_through_contract_and_evidence(self) -> None:
        submit = protocol("submit")
        review = protocol("review")
        land = protocol("land")

        self.assertIn("contract", submit["requires"])
        self.assertIn("completion-evidence", submit["requires"])
        self.assertEqual(["change-proposal"], submit["produces"])
        self.assertIn("contract", review["requires"])
        self.assertIn("change-proposal", review["requires"])
        self.assertIn("change-approved", land["requires"])
        self.assertEqual(["completion-record"], land["produces"])

    def test_close_artifact_schemas_join_completion_results_to_records(self) -> None:
        evidence = artifact_schema(ROOT, "completion-evidence")
        record = artifact_schema(ROOT, "completion-record")
        proposal = artifact_schema(ROOT, "change-proposal")

        result = evidence["properties"]["results"]["items"]
        self.assertIn("criterion_id", result["required"])
        self.assertIn("evidence", result["required"])
        self.assertIn("attestation", result["properties"]["evidence"]["properties"])
        self.assertIn("criterion_summary", record["required"])
        self.assertIn("documentation_status", record["required"])
        self.assertIn("version", proposal["required"])

    def test_close_protocol_delivery_blocks_match_manifest_and_schema_boundaries(self) -> None:
        boundaries = {boundary.protocol: boundary for boundary in delivery_boundaries(ROOT)}

        self.assertTrue(boundaries["submit"].passed)
        self.assertTrue(boundaries["land"].passed)
        self.assertEqual("change-proposal", boundaries["submit"].artifact)
        self.assertEqual("completion-record", boundaries["land"].artifact)

    def test_close_protocols_do_not_reintroduce_privileged_behavior_fields(self) -> None:
        for artifact in ["completion-evidence", "change-proposal", "completion-record"]:
            schema = artifact_schema(ROOT, artifact)
            with self.subTest(artifact=artifact):
                self.assertNotIn("behavior_form", schema.get("properties", {}))
                self.assertNotIn("criterion_coverage", schema.get("properties", {}))

    def test_review_and_land_keep_independent_judgment_sections(self) -> None:
        self.assertIn("## The Independence of the Gate", read(REVIEW_PROTOCOL))
        self.assertIn("## Failure Policy", read(LAND_PROTOCOL))
        self.assertIn("## Corruption Modes", read(SUBMIT_PROTOCOL))
        self.assertIn("dimension-drop", markdown_section(read(LAND_PROTOCOL), "Corruption Modes"))


if __name__ == "__main__":
    unittest.main()
