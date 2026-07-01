import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TAKE_PROTOCOL = ROOT / "protocols" / "take" / "PROTOCOL.md"
CONTRACT_SKILL = ROOT / "skills" / "contract" / "SKILL.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def step(body: str, number: int) -> str:
    pattern = re.compile(
        rf"^{number}\. \*\*.*?\n(?P<section>.*?)(?=^{number + 1}\. \*\*|^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing step {number}")
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


def lifecycle_rows(body: str) -> dict[str, str]:
    rows = {}
    for line in body.splitlines():
        match = re.match(r"\| \*\*(?P<dimension>Behavior|Documentation|Code quality)\*\* \| (?P<row>.+) \|$", line)
        if match:
            rows[match.group("dimension")] = match.group("row")
    return rows


class TakeProtocolContractDimensionTests(unittest.TestCase):
    def test_primary_authoring_flow_defines_validation_for_every_dimension(self) -> None:
        body = read(TAKE_PROTOCOL)
        authoring = normalized(step(body, 4))

        expected_terms = [
            "inputs to validation",
            "validation defined",
            "behavior",
            "acceptance criteria",
            "documentation",
            "recipient outcomes",
            "code quality",
            "principles-corpus",
            "stressed universals",
            "all three dimensions",
            "`contract` skill",
        ]
        for term in expected_terms:
            with self.subTest(term=term):
                self.assertIn(term, authoring)

        self.assertRegex(authoring, r"executable (?:Given/When/Then )?scenarios")
        self.assertIn("documentation-deliverable gates", authoring)
        self.assertIn("audience-outcome checklist", authoring)
        self.assertIn("reviewer-checkable", authoring)
        self.assertIn("projected", authoring)

    def test_take_requires_authored_criteria_for_present_dimensions(self) -> None:
        authoring = normalized(step(read(TAKE_PROTOCOL), 4))

        for expected in [
            "Every present dimension gets at least one authored criterion",
            "Density may be light",
            "coverage is never zero for a present dimension",
            "hollow_delivery",
            "check_kind",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, authoring)

        forbidden = re.compile(
            r"Pointer-as-default|general contract (?:remains the validation pointer|pointer)|"
            r"silence is valid|not a mandatory per-dimension (?:declaration|block)",
            flags=re.IGNORECASE,
        )
        self.assertIsNone(forbidden.search(authoring))

    def test_take_consults_dimension_homes_without_reencoding_lifecycle_table(self) -> None:
        body = read(TAKE_PROTOCOL)

        for expected in [
            "`contract` skill",
            "`skills/contract/references/documentation-contract.md`",
            "`skills/contract/references/code-quality-contract.md`",
            "`orient`",
            "`~/.groundwork/principles/`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

        lifecycle_table = re.compile(
            r"\| \*\*(?:Behavior|Documentation|Code quality)\*\* \| .*?"
            r"(?:inputs to validation|validation defined|validation performed)",
            flags=re.IGNORECASE,
        )
        self.assertIsNone(lifecycle_table.search(body))

    def test_named_forms_conform_to_contract_skill_lifecycle(self) -> None:
        take_body = normalized(read(TAKE_PROTOCOL))
        rows = lifecycle_rows(read(CONTRACT_SKILL))

        expected_forms = {
            "Behavior": ["executable scenarios", "documentation-deliverable gates"],
            "Documentation": ["documentation outcomes"],
            "Code quality": ["reviewer-checkable projections"],
        }

        self.assertEqual({"Behavior", "Documentation", "Code quality"}, set(rows))
        for dimension, forms in expected_forms.items():
            with self.subTest(dimension=dimension):
                for form in forms:
                    self.assertIn(form, rows[dimension])
                    self.assertIn(form, take_body)

    def test_contract_delivery_declares_dimension_criteria(self) -> None:
        delivery = normalized(step(read(TAKE_PROTOCOL), 5))

        for expected in [
            "contract({",
            "dimension-agnostic criteria",
            "hollow_delivery",
            "check_kind",
            "executable",
            "attested",
            "criteria",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, delivery)

        self.assertNotIn("#454", delivery)
        self.assertNotIn("deferred", delivery)
        self.assertNotIn("behavior_form", delivery)

    def test_documentation_deliverable_gates_thread_to_carry_through_without_scenarios(self) -> None:
        carry = normalized(step(read(TAKE_PROTOCOL), 6))
        carry_lower = carry.lower()

        for expected in [
            "scenario coverage",
            "gate coverage",
            "documentation-deliverable",
            "structural, coherence, and conformance",
            "do not encode gates as scenarios",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, carry_lower)

    def test_existing_take_discipline_sections_and_corruption_modes_survive(self) -> None:
        body = read(TAKE_PROTOCOL)

        expected_sections = [
            "Steps",
            "Scale",
            "Operating Principles",
            "Corruption Modes",
            "Cross-References",
        ]
        for heading in expected_sections:
            with self.subTest(heading=heading):
                self.assertIn(f"## {heading}", body)

        corruption_modes = normalized(section(body, "Corruption Modes"))
        for mode in [
            "contract-after-code",
            "scope-creep",
            "criteria-parroting",
            "skip-preparation",
            "state-lag",
            "abandon-at-contract",
            "mechanics-as-plan",
            "delegate-to-unwired-runtime",
        ]:
            with self.subTest(mode=mode):
                self.assertIn(mode, corruption_modes)


if __name__ == "__main__":
    unittest.main()
