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
VERIFY_PROTOCOL = ROOT / "protocols" / "verify" / "PROTOCOL.md"


def protocol(name: str) -> dict:
    return {entry["name"]: entry for entry in manifest_protocols(ROOT)}[name]


class VerifyProtocolGateCoverageTests(unittest.TestCase):
    def test_manifest_requires_contract_and_test_evidence_for_verify(self) -> None:
        verify = protocol("verify")

        self.assertTrue(verify["scoped"])
        self.assertIn("contract", verify["requires"])
        self.assertIn("test-evidence", verify["requires"])
        self.assertIn("work-unit", verify["requires"])
        self.assertEqual(["completion-evidence"], verify["produces"])

    def test_completion_evidence_schema_is_contract_criterion_keyed(self) -> None:
        schema = artifact_schema(ROOT, "completion-evidence")
        result = schema["properties"]["results"]["items"]
        evidence = result["properties"]["evidence"]

        self.assertIn("criterion_id", result["required"])
        self.assertIn("result", result["required"])
        self.assertIn("evidence", result["required"])
        self.assertEqual(["pass", "fail"], result["properties"]["result"]["enum"])
        self.assertEqual(
            [{"required": ["run"]}, {"required": ["artifact"]}, {"required": ["attestation"]}],
            evidence["anyOf"],
        )

    def test_verify_delivery_block_matches_manifest_and_schema_boundary(self) -> None:
        verify = {boundary.protocol: boundary for boundary in delivery_boundaries(ROOT)}["verify"]

        self.assertTrue(verify.passed)
        self.assertEqual("completion-evidence", verify.artifact)

    def test_verify_review_references_resolve_to_declared_review_guides(self) -> None:
        review = markdown_section(read(VERIFY_PROTOCOL), "Steps")

        for relative in [
            "protocols/verify/references/documentation-review.md",
            "protocols/verify/references/code-quality-review.md",
        ]:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())
                self.assertIn(relative.removeprefix("protocols/verify/"), review)

    def test_verify_schema_drops_retired_coverage_fields(self) -> None:
        schema = artifact_schema(ROOT, "completion-evidence")

        self.assertNotIn("criterion_coverage", schema.get("properties", {}))
        self.assertNotIn("behavior_form", schema.get("properties", {}))


if __name__ == "__main__":
    unittest.main()
