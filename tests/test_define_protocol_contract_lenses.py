import re
import tempfile
import unittest
from pathlib import Path

from tooling.prose_conformance import (
    artifact_schema,
    contract_lens_rows,
    delivery_boundaries,
    manifest_protocols,
    markdown_section,
    read,
)


ROOT = Path(__file__).resolve().parents[1]
DEFINE_PROTOCOL = ROOT / "protocols" / "define" / "PROTOCOL.md"
CONTRACT_SKILL = ROOT / "skills" / "contract" / "SKILL.md"
PRINCIPLE_DERIVED_CONTRACTS = (
    ROOT / "skills" / "contract" / "references" / "principle-derived-contracts.md"
)
EXPECTED_CONTRACT_LENSES = {
    "**Behavior**",
    "**Documentation**",
    "**Code quality**",
}


def protocol(name: str) -> dict:
    return {entry["name"]: entry for entry in manifest_protocols(ROOT)}[name]


class DefineProtocolContractDimensionTests(unittest.TestCase):
    def test_manifest_declares_define_as_scoped_contract_entry(self) -> None:
        define = protocol("define")

        self.assertTrue(define["scoped"])
        self.assertEqual(["work-unit"], define["requires"])
        self.assertEqual(["contract"], define["produces"])

    def test_contract_schema_requires_kind_lens_and_operational_check(self) -> None:
        schema = artifact_schema(ROOT, "contract")
        criterion = schema["properties"]["criteria"]["items"]

        self.assertIn("lens", criterion["required"])
        self.assertIn("hollow_delivery", criterion["required"])
        self.assertIn("kind", criterion["required"])
        self.assertEqual(["behavior", "meaning"], criterion["properties"]["kind"]["enum"])
        check = criterion["properties"]["check"]
        self.assertEqual("object", check["type"])
        self.assertEqual(
            ["actor", "procedure", "observable", "conforming_case", "falsifying_case"],
            check["required"],
        )
        self.assertFalse(check["additionalProperties"])
        self.assertNotIn("check_kind", criterion["properties"])
        self.assertNotIn("dimension", criterion["properties"])
        self.assertNotIn("behavior_form", criterion["properties"])

    def test_acceptance_criterion_source_mapping_exposes_dual_use(self) -> None:
        schema = artifact_schema(ROOT, "contract")
        body = read(DEFINE_PROTOCOL)
        source_mapping = markdown_section(read(PRINCIPLE_DERIVED_CONTRACTS), "Source Mapping")
        acceptance_criterion = schema["properties"]["criteria"]["items"]["properties"][
            "acceptance_criterion"
        ]

        self.assertEqual(
            "Source for this contract criterion: numbered work-unit acceptance criterion or explicit body-ground obligation.",
            acceptance_criterion["description"],
        )
        self.assertIn(
            'acceptance_criterion: "<numbered acceptance criterion or explicit body-ground obligation source>",',
            body,
        )
        self.assertIn("numbered acceptance criterion", source_mapping)
        self.assertIn("explicit body-ground source", source_mapping)
        self.assertIn("Body-ground mapping is not scope expansion", source_mapping)
        self.assertNotIn("<acceptance criterion this refines>", body)

    def test_define_delivery_block_matches_manifest_and_schema_boundary(self) -> None:
        define = {boundary.protocol: boundary for boundary in delivery_boundaries(ROOT)}["define"]

        self.assertTrue(define.passed)
        self.assertEqual("contract", define.artifact)
        self.assertTrue(define.scoped)
        self.assertTrue(define.schema_requires_work_unit)

    def test_define_consults_contract_lens_authorities(self) -> None:
        body = read(DEFINE_PROTOCOL)
        rows = contract_lens_rows(ROOT)

        self.assertEqual(EXPECTED_CONTRACT_LENSES, set(rows))
        for relative in [
            "skills/contract/references/documentation-contract.md",
            "skills/contract/references/code-quality-contract.md",
        ]:
            with self.subTest(relative=relative):
                self.assertTrue((ROOT / relative).is_file())
                self.assertIn(relative, body)

    def test_contract_lens_gate_flips_when_skill_table_changes(self) -> None:
        self.assertEqual(EXPECTED_CONTRACT_LENSES, set(contract_lens_rows(ROOT)))

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            skill = tree / "skills" / "contract" / "SKILL.md"
            skill.parent.mkdir(parents=True)
            body = read(CONTRACT_SKILL).replace(
                "| **Documentation** | `work-unit-craft`/`decompose` recipient outcomes |",
                "| **Release notes** | `work-unit-craft`/`decompose` recipient outcomes |",
                1,
            )
            skill.write_text(body, encoding="utf-8")

            mutated_lenses = set(contract_lens_rows(tree))

        self.assertNotEqual(EXPECTED_CONTRACT_LENSES, mutated_lenses)
        self.assertEqual(
            {"**Behavior**", "**Release notes**", "**Code quality**"},
            mutated_lenses,
        )

    def test_define_ends_at_contract_capstone_with_named_corruption_modes(self) -> None:
        steps = markdown_section(read(DEFINE_PROTOCOL), "Steps")
        corruption_modes = markdown_section(read(DEFINE_PROTOCOL), "Corruption Modes")

        self.assertIsNone(re.search(r"^6\. \*\*", steps, flags=re.MULTILINE))
        self.assertIn("contract-after-code", corruption_modes)
        self.assertIn("lens-declaration-only", corruption_modes)
        self.assertIn("lifecycle-modeling", corruption_modes)


if __name__ == "__main__":
    unittest.main()
