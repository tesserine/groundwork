import unittest
from pathlib import Path

from tooling.prose_conformance import (
    artifact_schema,
    delivery_boundaries,
    frontmatter,
    manifest_protocols,
    markdown_section,
    read,
)


ROOT = Path(__file__).resolve().parents[1]
PLAN_PROTOCOL = ROOT / "protocols" / "plan" / "PROTOCOL.md"
IMPLEMENT_PROTOCOL = ROOT / "protocols" / "implement" / "PROTOCOL.md"


def protocol(name: str) -> dict:
    return {entry["name"]: entry for entry in manifest_protocols(ROOT)}[name]


class BuildProtocolContractDimensionTests(unittest.TestCase):
    def test_manifest_threads_contract_through_plan_and_implement(self) -> None:
        plan = protocol("plan")
        implement = protocol("implement")

        self.assertIn("contract", plan["requires"])
        self.assertEqual(["implementation-plan"], plan["produces"])
        self.assertIn("contract", implement["requires"])
        self.assertIn("implementation-plan", implement["requires"])
        self.assertEqual(["test-evidence"], implement["produces"])

    def test_build_artifact_schemas_are_criterion_keyed(self) -> None:
        plan_schema = artifact_schema(ROOT, "implementation-plan")
        evidence_schema = artifact_schema(ROOT, "test-evidence")

        mapping = plan_schema["properties"]["criterion_mapping"]["items"]
        evidence = evidence_schema["properties"]["evidence"]["items"]

        self.assertIn("criterion_id", mapping["required"])
        self.assertIn("steps", mapping["required"])
        self.assertIn("criterion_id", evidence["required"])
        self.assertIn("command", evidence["required"])

    def test_build_protocol_delivery_blocks_match_manifest_and_schema_boundaries(self) -> None:
        boundaries = {boundary.protocol: boundary for boundary in delivery_boundaries(ROOT)}

        self.assertTrue(boundaries["plan"].passed)
        self.assertTrue(boundaries["implement"].passed)
        self.assertEqual("implementation-plan", boundaries["plan"].artifact)
        self.assertEqual("test-evidence", boundaries["implement"].artifact)

    def test_build_protocols_do_not_reintroduce_retired_behavior_form_fields(self) -> None:
        for artifact in ["implementation-plan", "test-evidence"]:
            schema = artifact_schema(ROOT, artifact)
            with self.subTest(artifact=artifact):
                self.assertNotIn("behavior_form", schema.get("properties", {}))

    def test_build_protocol_frontmatter_and_red_gate_are_structured(self) -> None:
        plan_metadata = frontmatter(read(PLAN_PROTOCOL))["metadata"]
        implement_metadata = frontmatter(read(IMPLEMENT_PROTOCOL))["metadata"]

        self.assertRegex(plan_metadata["version"], r"^[0-9]+[.][0-9]+[.][0-9]+$")
        self.assertRegex(implement_metadata["version"], r"^[0-9]+[.][0-9]+[.][0-9]+$")
        self.assertIn("NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST", markdown_section(read(IMPLEMENT_PROTOCOL), "The Iron Law"))


if __name__ == "__main__":
    unittest.main()
