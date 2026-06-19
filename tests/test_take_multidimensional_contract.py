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


def numbered_step(body: str, number: int) -> str:
    pattern = re.compile(
        rf"^{number}\. \*\*[^*]+\.\*\*(?P<section>.*?)(?=^\d+\. \*\*|^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing numbered step {number}")
    return match.group("section")


def lifecycle_row(dimension: str) -> str:
    pattern = re.compile(
        rf"^\| \*\*{re.escape(dimension)}\*\* \| (?P<row>.+) \|$",
        flags=re.MULTILINE,
    )
    match = pattern.search(read(CONTRACT_SKILL))
    if match is None:
        raise AssertionError(f"missing lifecycle row for {dimension}")
    return match.group("row")


class TakeMultidimensionalContractTests(unittest.TestCase):
    def test_primary_authoring_step_defines_validation_for_every_dimension(self) -> None:
        authoring = normalized(numbered_step(read(TAKE_PROTOCOL), 4))

        for expected in [
            "contract inputs",
            "inputs to validation",
            "validation defined",
            "behavior",
            "documentation",
            "code quality",
            "`contract`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, authoring)

        self.assertNotIn("merely declare", authoring.lower())
        self.assertNotIn("audited at `verify`; behavior is the dimension delivered", authoring)

    def test_dimension_forms_match_the_contract_skill_lifecycle(self) -> None:
        authoring = normalized(numbered_step(read(TAKE_PROTOCOL), 4))

        behavior_terms = ["executable scenarios", "documentation-deliverable gates"]
        documentation_terms = ["audience-outcome checklist", "recipient outcome"]
        code_quality_terms = ["projected", "reviewer-checkable", "question", "failing tell", "locus"]

        for term in behavior_terms:
            with self.subTest(dimension="behavior", term=term):
                self.assertIn(term, authoring)
                self.assertIn(term, lifecycle_row("Behavior"))

        for term in ["documentation outcomes"]:
            with self.subTest(dimension="documentation lifecycle", term=term):
                self.assertIn(term, lifecycle_row("Documentation"))
        for term in documentation_terms:
            with self.subTest(dimension="documentation authoring", term=term):
                self.assertIn(term, authoring)

        self.assertIn("reviewer-checkable projections", lifecycle_row("Code quality"))
        for term in code_quality_terms:
            with self.subTest(dimension="code quality", term=term):
                self.assertIn(term, authoring)

    def test_documentation_deliverable_gates_are_realized_and_carried(self) -> None:
        body = normalized(read(TAKE_PROTOCOL))
        delivery = normalized(numbered_step(read(TAKE_PROTOCOL), 5))
        carry = normalized(numbered_step(read(TAKE_PROTOCOL), 6))

        for expected in [
            "structural",
            "coherence",
            "conformance",
            "committed",
            "tests",
            "gate coverage",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

        self.assertIn("scenario coverage", carry)
        self.assertIn("gate coverage", carry)
        self.assertIn("documentation-deliverable", delivery)
        self.assertIn("Do not encode documentation-deliverable gates as scenarios", delivery)

    def test_pointer_as_default_is_defined_without_mandatory_dimension_blocks(self) -> None:
        authoring = normalized(numbered_step(read(TAKE_PROTOCOL), 4))

        for expected in [
            "pointer-as-default",
            "considered",
            "general contract pointer",
            "no special input",
            "not a mandatory",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, authoring)

    def test_take_consults_single_homes_without_reencoding_the_lifecycle(self) -> None:
        body = read(TAKE_PROTOCOL)
        authoring = normalized(numbered_step(body, 4))

        for expected in [
            "skills/contract/references/documentation-contract.md",
            "skills/contract/references/code-quality-contract.md",
            "`orient`",
            "documentation audience taxonomy",
            "~/.groundwork/principles/",
            "consult",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, authoring)

        self.assertNotRegex(body, r"\| \*\*Behavior\*\* \|")
        self.assertNotRegex(body, r"\| \*\*Documentation\*\* \|")
        self.assertNotRegex(body, r"\| \*\*Code quality\*\* \|")

    def test_existing_take_discipline_sections_and_corruptions_survive(self) -> None:
        body = read(TAKE_PROTOCOL)

        for heading in [
            "## Steps",
            "## Scale",
            "## Operating Principles",
            "## Corruption Modes",
            "## Cross-References",
        ]:
            with self.subTest(heading=heading):
                self.assertIn(heading, body)

        for corruption in [
            "contract-after-code",
            "scope-creep",
            "criteria-parroting",
            "skip-preparation",
            "state-lag",
            "abandon-at-contract",
            "mechanics-as-plan",
            "delegate-to-unwired-runtime",
        ]:
            with self.subTest(corruption=corruption):
                self.assertIn(corruption, body)


if __name__ == "__main__":
    unittest.main()
