import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs" / "architecture" / "groundwork-skill-ontology-row-1-audit.md"

EXPECTED_SECTIONS = [
    "Purpose",
    "Method",
    "Groundwork Row",
    "Protocol Reduction Test",
    "Projection Seams",
    "Lateral Harmonics",
    "Mendeleev Gaps",
    "Distilled-Table Crossings",
    "Substrate Fine-Tuning Findings",
    "Row 2 Extension Shape",
]

ALLOWED_DOMAIN_COUPLING = {"universal", "domain:software"}
ALLOWED_FORMS = {"skill", "protocol"}


def skill_names() -> set[str]:
    return {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}


def protocol_names() -> set[str]:
    return {path.parent.name for path in (ROOT / "protocols").glob("*/PROTOCOL.md")}


def audit_text() -> str:
    return AUDIT.read_text(encoding="utf-8")


def section_body(heading: str) -> str:
    body = audit_text()
    match = re.search(
        rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)",
        body,
        flags=re.DOTALL | re.MULTILINE,
    )
    if match is None:
        raise AssertionError(f"missing section: {heading}")
    return match.group("body")


def table_rows(section: str, required_columns: list[str]) -> list[dict[str, str]]:
    body = section_body(section)
    lines = [line.strip() for line in body.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        raise AssertionError(f"{section} must contain a markdown table")

    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    for column in required_columns:
        if column not in header:
            raise AssertionError(f"{section} table missing column: {column}")

    rows = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(header):
            raise AssertionError(f"{section} row has {len(cells)} cells, expected {len(header)}: {line}")
        rows.append(dict(zip(header, cells)))
    return rows


class GroundworkSkillOntologyRow1AuditTests(unittest.TestCase):
    def test_audit_document_exists_with_required_sections(self) -> None:
        self.assertTrue(AUDIT.is_file(), "row-1 audit architecture document is missing")
        body = audit_text()
        for section in EXPECTED_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(f"## {section}", body)

    def test_groundwork_row_covers_every_skill_and_protocol_once(self) -> None:
        rows = table_rows(
            "Groundwork Row",
            ["Asset", "Kind", "Domain Coupling", "Form", "Membership-Test Ground"],
        )
        skill_assets = {row["Asset"] for row in rows if row["Kind"] == "skill"}
        protocol_assets = {row["Asset"] for row in rows if row["Kind"] == "protocol"}

        self.assertEqual(skill_names(), skill_assets)
        self.assertEqual(protocol_names(), protocol_assets)
        self.assertEqual(len(rows), len(skill_assets) + len(protocol_assets))

    def test_groundwork_row_coordinates_and_membership_tests_are_explicit(self) -> None:
        rows = table_rows(
            "Groundwork Row",
            ["Asset", "Kind", "Domain Coupling", "Form", "Membership-Test Ground"],
        )
        for row in rows:
            with self.subTest(asset=row["Asset"]):
                self.assertIn(row["Domain Coupling"], ALLOWED_DOMAIN_COUPLING)
                self.assertIn(row["Form"], ALLOWED_FORMS)
                self.assertEqual(row["Kind"], row["Form"])
                self.assertRegex(
                    row["Membership-Test Ground"].lower(),
                    r"gazette|another domain|non-code",
                )

    def test_protocol_reduction_covers_every_protocol_and_computes_aggregate_finding(self) -> None:
        rows = table_rows(
            "Protocol Reduction Test",
            ["Protocol", "Universal Candidate", "Reduction", "Reason"],
        )
        self.assertEqual(protocol_names(), {row["Protocol"] for row in rows})
        self.assertIn("no", {row["Reduction"].lower() for row in rows})
        self.assertNotEqual(
            {"yes"},
            {row["Reduction"].lower() for row in rows},
            "the table, not aggregate prose, decides whether every protocol reduces",
        )

    def test_domain_specific_skills_declare_projection_edges(self) -> None:
        row_entries = table_rows(
            "Groundwork Row",
            ["Asset", "Kind", "Domain Coupling", "Form", "Membership-Test Ground"],
        )
        domain_specific_skills = {
            row["Asset"]
            for row in row_entries
            if row["Kind"] == "skill" and row["Domain Coupling"] == "domain:software"
        }
        projection_rows = table_rows(
            "Projection Seams",
            ["Domain Skill", "Domain Scope", "Projects From", "Inherited Discipline", "Domain Delta"],
        )

        self.assertEqual(domain_specific_skills, {row["Domain Skill"] for row in projection_rows})
        for row in projection_rows:
            with self.subTest(skill=row["Domain Skill"]):
                self.assertEqual("domain:software", row["Domain Scope"])
                self.assertNotEqual("", row["Projects From"])
                self.assertNotEqual(row["Domain Skill"], row["Projects From"])
                self.assertNotEqual("", row["Inherited Discipline"])
                self.assertNotEqual("", row["Domain Delta"])

    def test_harmonics_gaps_crossings_and_fine_tuning_are_structured(self) -> None:
        expectations = [
            (
                "Lateral Harmonics",
                ["Atomic Bead", "Kin Assets", "Shared Invariant", "Extraction Value"],
            ),
            (
                "Mendeleev Gaps",
                ["Predicted Position", "Properties Implied", "Missing Asset"],
            ),
            (
                "Distilled-Table Crossings",
                ["Pairing", "Behavioral Invariant", "Convergence"],
            ),
            (
                "Substrate Fine-Tuning Findings",
                ["Finding", "Witness Marks", "Disposition"],
            ),
        ]
        for section, columns in expectations:
            with self.subTest(section=section):
                rows = table_rows(section, columns)
                self.assertGreaterEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
