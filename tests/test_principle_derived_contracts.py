import json
import re
import unittest
from pathlib import Path

from tooling.artifact_schemas import validate_artifact
from tooling.prose_conformance import frontmatter, markdown_section, markdown_table_rows


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SKILL = ROOT / "skills" / "contract" / "SKILL.md"
REFERENCE = ROOT / "skills" / "contract" / "references" / "principle-derived-contracts.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def fenced_json_after(body: str, marker: str) -> dict:
    pattern = re.compile(
        rf"{re.escape(marker)}.*?```json\n(?P<json>.*?)\n```",
        flags=re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing JSON block after {marker!r}")
    return json.loads(match.group("json"))


def markdown_links(body: str) -> list[str]:
    prose = re.sub(r"^`{3,}.*?^`{3,}", "", body, flags=re.DOTALL | re.MULTILINE)
    return [
        target
        for target in re.findall(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)\s]*)?\)", prose)
        if "://" not in target and not target.startswith("mailto:")
    ]


class PrincipleDerivedContractTests(unittest.TestCase):
    def test_contract_skill_routes_to_principle_derived_contract_reference(self) -> None:
        body = read(CONTRACT_SKILL)
        metadata = frontmatter(body)["metadata"]
        route = markdown_section(body, "Principle-Derived Contracts")
        cross_references = markdown_section(body, "Cross-References")

        self.assertEqual("2.8.0", metadata["version"])
        self.assertEqual("2026-07-07", metadata["updated"])
        self.assertIn("references/principle-derived-contracts.md", route)
        self.assertIn("references/principle-derived-contracts.md", cross_references)

    def test_principle_derived_contract_reference_links_resolve_both_ways(self) -> None:
        self.assertTrue(REFERENCE.is_file())
        skill = read(CONTRACT_SKILL)
        reference = read(REFERENCE)

        self.assertIn("references/principle-derived-contracts.md", skill)
        self.assertIn("../SKILL.md", reference)
        for target in markdown_links(reference):
            with self.subTest(target=target):
                self.assertTrue((REFERENCE.parent / target).resolve().is_file())

    def test_reference_carries_the_planned_method_sections(self) -> None:
        body = read(REFERENCE)
        expected_sections = {
            "Trigger and Boundary",
            "Derivation Method",
            "Mechanism-Open, Quality-Closed",
            "Operational Hollows",
            "Source Mapping",
            "Attested Checks With Teeth",
            "Evolvability Outcome",
            "Worked Example",
            "Corruption Modes",
            "Cross-References",
        }

        actual_sections = set(re.findall(r"^## (.+)$", body, flags=re.MULTILINE))

        self.assertTrue(expected_sections <= actual_sections)

    def test_source_mapping_table_uses_the_existing_acceptance_criterion_field(self) -> None:
        source_mapping = markdown_section(read(REFERENCE), "Source Mapping")
        rows = markdown_table_rows(source_mapping)
        labels = {row["Source"] for row in rows}

        self.assertIn("Numbered acceptance criterion", labels)
        self.assertIn("Body-ground source", labels)
        self.assertIn("Floating criterion", labels)
        self.assertIn("acceptance_criterion", source_mapping)
        self.assertIn("`contract.criteria[]`", source_mapping)

    def test_worked_example_is_valid_on_the_existing_contract_schema(self) -> None:
        example = fenced_json_after(read(REFERENCE), "Schema-valid example")

        validate_artifact("contract", example)
        self.assertEqual(
            {"behavior", "documentation", "code-quality"},
            {criterion["dimension"] for criterion in example["criteria"]},
        )
        self.assertTrue(
            any(
                criterion["acceptance_criterion"].startswith("Body ground")
                for criterion in example["criteria"]
            )
        )

    def test_changelog_records_the_contract_version_coupling(self) -> None:
        unreleased = read(CHANGELOG).split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]

        self.assertIn("#531", unreleased)
        self.assertIn("contract 2.7.1->2.8.0", unreleased)


if __name__ == "__main__":
    unittest.main()
