import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_UNIT_CRAFT = ROOT / "skills" / "work-unit-craft" / "SKILL.md"
DECOMPOSE_PROTOCOL = ROOT / "protocols" / "decompose" / "PROTOCOL.md"


def read_work_unit_craft() -> str:
    return WORK_UNIT_CRAFT.read_text(encoding="utf-8")


def read_decompose_protocol() -> str:
    return DECOMPOSE_PROTOCOL.read_text(encoding="utf-8")


def section_between(body: str, start: str, end: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(start)}\n(?P<section>.*?)(?=^## {re.escape(end)}\n)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing section boundary: {start} -> {end}")
    return match.group("section")


def section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<section>.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing section: {heading}")
    return match.group("section")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class WorkUnitCraftSkillTests(unittest.TestCase):
    def test_primary_workflow_invokes_reckon_for_verified_constraints(self) -> None:
        body = read_work_unit_craft()
        primary_workflow = section_between(
            body,
            "The Central Discipline",
            "The Sovereignty Test",
        )

        self.assertIn("`reckon`", primary_workflow)
        self.assertRegex(primary_workflow, r"\bcognitive process\b")
        self.assertRegex(primary_workflow, r"\bverified constraints\b")
        self.assertRegex(
            primary_workflow,
            r"(?s)`reckon`.*verified constraints|verified constraints.*`reckon`",
        )

    def test_reckon_invocation_is_a_pointer_not_a_second_home(self) -> None:
        body = read_work_unit_craft()
        primary_workflow = section_between(
            body,
            "The Central Discipline",
            "The Sovereignty Test",
        )

        copied_method_terms = [
            "six steps",
            "Navigational Principles",
            "Recognition Index",
            "The Move",
        ]
        for term in copied_method_terms:
            with self.subTest(term=term):
                self.assertNotIn(term, primary_workflow)

    def test_existing_craft_discipline_sections_remain_present(self) -> None:
        body = read_work_unit_craft()
        expected_sections = {
            "The Central Discipline": "Records describe what must be true",
            "The Sovereignty Test": "Is this a constraint the implementer must satisfy",
            "Milestone Discipline": "release scope then becomes a query",
            "Label Discipline": "Labels must discriminate",
            "The Body Is the Spec; Comments Are a Log": "The body must be a complete, standalone specification",
            "Corruption Modes": "stale-comment-direction",
            "What Belongs in a Record": "Acceptance criteria",
            "What Does Not Belong in a Record": "Implementation step sequences",
            "Metadata at File Time": "Label (required)",
            "Cross-References": "`decompose`",
        }

        for heading, expected_text in expected_sections.items():
            with self.subTest(heading=heading):
                self.assertIn(expected_text, normalized(section(body, heading)))

    def test_primary_workflow_authors_contract_inputs_for_every_dimension(self) -> None:
        body = read_work_unit_craft()
        primary_workflow = normalized(
            section_between(
                body,
                "The Central Discipline",
                "The Sovereignty Test",
            )
        )

        expected_inputs = [
            "contract inputs",
            "`contract`",
            "behavior",
            "acceptance criteria",
            "documentation",
            "`orient`",
            "recipient outcomes",
            "code quality",
            "principles corpus",
            "stressed universals",
        ]
        for expected in expected_inputs:
            with self.subTest(expected=expected):
                self.assertIn(expected, primary_workflow)

    def test_contract_input_density_rule_requires_teeth_not_silence(self) -> None:
        body = read_work_unit_craft()
        primary_workflow = normalized(
            section_between(
                body,
                "The Central Discipline",
                "The Sovereignty Test",
            )
        )

        for expected in [
            "consider every dimension",
            "every dimension the change has",
            "authored teeth-bearing input",
            "density may be light",
            "coverage is never zero",
            "hollow delivery",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, primary_workflow)

        forbidden = re.compile(
            r"general contract pointer|silence is valid|not a mandatory per-dimension body section",
            flags=re.IGNORECASE,
        )
        self.assertIsNone(forbidden.search(primary_workflow))

    def test_declared_contract_work_consults_the_contract_instead_of_modeling_it(self) -> None:
        body = read_work_unit_craft()
        belongs = normalized(section(body, "What Belongs in a Record"))
        corruption_modes = normalized(section(body, "Corruption Modes"))

        positive_craft = [
            "Declared contract conformance",
            "consult the declared contract",
            "derive criteria from its declarations",
            "verify positively against the declaration",
        ]
        for expected in positive_craft:
            with self.subTest(expected=expected):
                self.assertIn(expected, belongs)

        corruption_checks = [
            "contract-modeling",
            "hand-maintained model",
            "operation names or shapes",
            "consult the contract",
        ]
        for expected in corruption_checks:
            with self.subTest(expected=expected):
                self.assertIn(expected, corruption_modes)

    def test_decompose_is_titled_as_itself_and_consults_the_craft_home(self) -> None:
        body = read_decompose_protocol()

        self.assertRegex(body, r"(?m)^# Decompose$")
        self.assertIn("skills/work-unit-craft/SKILL.md", body)

    def test_decompose_corruption_modes_are_protocol_level(self) -> None:
        body = read_decompose_protocol()
        corruption_modes = normalized(section(body, "Corruption Modes"))

        self.assertIn("`work-unit-craft`", corruption_modes)
        for expected in [
            "`kitchen-sink-epic`",
            "`graph-omission`",
            "`refinement-as-first-delivery`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, corruption_modes)

    def test_decompose_procedures_apply_the_contract_input_pass(self) -> None:
        body = read_decompose_protocol()
        create_work_unit = normalized(
            section_between(
                body,
                "Procedures",
                "Triggers",
            )
        )

        expected = [
            "contract inputs",
            "behavior",
            "documentation",
            "code quality",
            "`work-unit-craft`",
            "`contract`",
            "`orient`",
            "principles corpus",
            "create-work-unit",
            "decompose-epic",
            "refine-work-unit",
        ]
        for item in expected:
            with self.subTest(item=item):
                self.assertIn(item, create_work_unit)


if __name__ == "__main__":
    unittest.main()
