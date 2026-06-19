import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TAKE_PROTOCOL = ROOT / "protocols" / "take" / "PROTOCOL.md"
CONTRACT_SKILL = ROOT / "skills" / "contract" / "SKILL.md"
DOCUMENTATION_CONTRACT = ROOT / "skills" / "contract" / "references" / "documentation-contract.md"
CODE_QUALITY_CONTRACT = ROOT / "skills" / "contract" / "references" / "code-quality-contract.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def take_body() -> str:
    return read(TAKE_PROTOCOL)


def take_step_4() -> str:
    body = take_body()
    match = re.search(
        r"^4\. \*\*.*?\n(?P<section>.*?)(?=^5\. \*\*)",
        body,
        flags=re.MULTILINE | re.DOTALL,
    )
    if match is None:
        raise AssertionError("missing take step 4")
    return normalized(match.group("section"))


def section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<section>.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing section: {heading}")
    return match.group("section")


class TakeProtocolContractDimensionTests(unittest.TestCase):
    def test_primary_flow_defines_validation_for_every_contract_dimension(self) -> None:
        step = take_step_4()

        expected = [
            "inputs to validation",
            "validation defined",
            "acceptance criteria",
            "recipient outcomes",
            "corpus pointers",
            "stressed universals",
            "behavior",
            "documentation",
            "code quality",
        ]
        for item in expected:
            with self.subTest(item=item):
                self.assertIn(item, step)

        self.assertRegex(
            step,
            r"(?s)behavior.*documentation.*code quality|code quality.*documentation.*behavior",
        )

    def test_documentation_and_code_quality_defined_forms_have_teeth(self) -> None:
        step = take_step_4()

        expected = [
            "audience-outcome checklist",
            "hollow docs",
            "projected corpus universals",
            "reviewer-checkable item",
            "question",
            "failing tell",
            "locus",
        ]
        for item in expected:
            with self.subTest(item=item):
                self.assertIn(item, step)

        self.assertNotRegex(step, r"README is updated|code is clean")

    def test_behavior_form_matches_the_deliverable(self) -> None:
        step = take_step_4()

        expected = [
            "Given/When/Then scenarios",
            "runtime-behavior work-unit",
            "documentation-deliverable work-unit",
            "structural",
            "coherence",
            "conformance",
            "gates",
        ]
        for item in expected:
            with self.subTest(item=item):
                self.assertIn(item, step)

    def test_pointer_as_default_keeps_dimensions_considered_without_mandatory_blocks(self) -> None:
        step = take_step_4()

        expected = [
            "consider every dimension",
            "general contract",
            "pointer",
            "no special input",
            "density is unequal",
        ]
        for item in expected:
            with self.subTest(item=item):
                self.assertIn(item, step)

        self.assertNotIn("mandatory per-dimension", step)

    def test_take_consults_single_homes_without_reencoding_the_lifecycle(self) -> None:
        step = take_step_4()

        expected = [
            "`contract` skill",
            "documentation-contract.md",
            "code-quality-contract.md",
            "`orient`",
            "~/.groundwork/principles/",
            "consult",
        ]
        for item in expected:
            with self.subTest(item=item):
                self.assertIn(item, step)

        self.assertNotRegex(step, r"\| Dimension \| Lifecycle \|")
        self.assertNotIn("Stage Handoffs", step)

    def test_take_defined_forms_conform_to_contract_skill_single_home(self) -> None:
        step = take_step_4()
        contract = read(CONTRACT_SKILL)
        documentation_contract = read(DOCUMENTATION_CONTRACT)
        code_quality_contract = read(CODE_QUALITY_CONTRACT)

        for phrase in [
            "documentation-deliverable gates",
            "audience-outcome review",
            "reviewer-checkable projections",
            "pointer",
        ]:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, contract)

        self.assertIn("audience", documentation_contract)
        self.assertIn("outcome", documentation_contract)
        self.assertIn("checklist", documentation_contract)
        self.assertIn("question", code_quality_contract)
        self.assertIn("failing tell", code_quality_contract)
        self.assertIn("locus", code_quality_contract)
        self.assertIn("documentation-deliverable gates", step)
        self.assertIn("audience-outcome checklist", step)
        self.assertIn("projected corpus universals", step)

    def test_existing_take_discipline_sections_survive(self) -> None:
        body = take_body()
        sections = {
            "Steps": "Prepare the workspace",
            "Scale": "Depth scales with the change",
            "Operating Principles": "The contract is the spine",
            "Corruption Modes": "contract-after-code",
            "Cross-References": "`reckon`",
        }

        for heading, expected in sections.items():
            with self.subTest(heading=heading):
                self.assertIn(expected, normalized(section(body, heading)))

        for corruption_mode in [
            "scope-creep",
            "criteria-parroting",
            "skip-preparation",
            "state-lag",
            "abandon-at-contract",
            "mechanics-as-plan",
            "delegate-to-unwired-runtime",
        ]:
            with self.subTest(corruption_mode=corruption_mode):
                self.assertIn(corruption_mode, body)


if __name__ == "__main__":
    unittest.main()
