import re
import unittest
from pathlib import Path

from tooling.prose_conformance import (
    artifact_schema,
    delivery_boundaries,
    manifest_protocols,
    markdown_section,
    markdown_table_rows,
    read,
)


ROOT = Path(__file__).resolve().parents[1]
TAKE_PROTOCOL = ROOT / "protocols" / "take" / "PROTOCOL.md"
CONTRACT_SKILL = ROOT / "skills" / "contract" / "SKILL.md"


def protocol(name: str) -> dict:
    return {entry["name"]: entry for entry in manifest_protocols(ROOT)}[name]


class TakeProtocolContractDimensionTests(unittest.TestCase):
    def test_manifest_declares_take_as_scoped_contract_entry(self) -> None:
        take = protocol("take")

        self.assertTrue(take["scoped"])
        self.assertEqual(["work-unit"], take["requires"])
        self.assertEqual(["contract"], take["produces"])

    def test_contract_schema_requires_dimension_agnostic_teeth_fields(self) -> None:
        schema = artifact_schema(ROOT, "contract")
        criterion = schema["properties"]["criteria"]["items"]

        self.assertIn("dimension", criterion["required"])
        self.assertIn("hollow_delivery", criterion["required"])
        self.assertIn("check_kind", criterion["required"])
        self.assertEqual(["executable", "attested"], criterion["properties"]["check_kind"]["enum"])
        self.assertNotIn("behavior_form", criterion["properties"])

    def test_take_delivery_block_matches_manifest_and_schema_boundary(self) -> None:
        take = {boundary.protocol: boundary for boundary in delivery_boundaries(ROOT)}["take"]

        self.assertTrue(take.passed)
        self.assertEqual("contract", take.artifact)
        self.assertTrue(take.scoped)
        self.assertTrue(take.schema_requires_work_unit)

    def test_take_consults_contract_dimension_authorities(self) -> None:
        body = read(TAKE_PROTOCOL)
        rows = {
            row["Dimension"]: row
            for row in markdown_table_rows(markdown_section(read(CONTRACT_SKILL), "The dimensions"))
        }

        self.assertEqual({"**Behavior**", "**Documentation**", "**Code quality**"}, set(rows))
        for relative in [
            "skills/contract/references/documentation-contract.md",
            "skills/contract/references/code-quality-contract.md",
        ]:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())
                self.assertIn(relative, body)

    def test_take_ends_at_contract_capstone_with_named_corruption_modes(self) -> None:
        steps = markdown_section(read(TAKE_PROTOCOL), "Steps")
        corruption_modes = markdown_section(read(TAKE_PROTOCOL), "Corruption Modes")

        self.assertIsNone(re.search(r"^6\. \*\*", steps, flags=re.MULTILINE))
        self.assertIn("contract-after-code", corruption_modes)
        self.assertIn("dimension-declaration-only", corruption_modes)
        self.assertIn("lifecycle-modeling", corruption_modes)


if __name__ == "__main__":
    unittest.main()
