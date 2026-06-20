import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERIFY_PROTOCOL = ROOT / "protocols" / "verify" / "PROTOCOL.md"
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
        match = re.match(
            r"\| \*\*(?P<dimension>Behavior|Documentation|Code quality)\*\* \| (?P<row>.+) \|$",
            line,
        )
        if match:
            rows[match.group("dimension")] = match.group("row")
    return rows


class VerifyProtocolGateCoverageTests(unittest.TestCase):
    def test_primary_coverage_assessment_reports_gate_coverage_for_documentation_deliverables(self) -> None:
        coverage = normalized(step(read(VERIFY_PROTOCOL), 3)).lower()

        for expected in [
            "documentation-deliverable work-unit",
            "gate coverage",
            "structural",
            "coherence",
            "conformance",
            "acceptance criteria",
            "results",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, coverage)

    def test_behavior_coverage_is_conditional_by_deliverable_type(self) -> None:
        body = normalized(step(read(VERIFY_PROTOCOL), 1) + step(read(VERIFY_PROTOCOL), 3)).lower()

        for expected in [
            "runtime-behavior work-unit",
            "scenario coverage",
            "documentation-deliverable work-unit",
            "gate coverage",
            "`contract` skill",
            "behavior lifecycle",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

    def test_documentation_and_code_quality_reviews_remain_present(self) -> None:
        review = normalized(step(read(VERIFY_PROTOCOL), 4))

        for expected in [
            "For **documentation**",
            "declared pillar's outcome",
            "existing docs honest",
            "[references/documentation-review.md](references/documentation-review.md)",
            "For **code quality**",
            "declared universal",
            "[references/code-quality-review.md](references/code-quality-review.md)",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, review)

    def test_verify_consults_contract_lifecycle_without_reencoding_it(self) -> None:
        body = read(VERIFY_PROTOCOL)

        for expected in [
            "`contract` skill",
            "behavior lifecycle",
            "`skills/contract/SKILL.md`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

        lifecycle_table = re.compile(
            r"\| \*\*(?:Behavior|Documentation|Code quality)\*\* \| .*?"
            r"(?:inputs to validation|validation defined|validation performed)",
            flags=re.IGNORECASE,
        )
        self.assertIsNone(lifecycle_table.search(body))

    def test_gate_keyed_completion_evidence_runtime_delivery_uses_existing_mcp_tool(self) -> None:
        delivery = normalized(step(read(VERIFY_PROTOCOL), 5))

        for expected in [
            "runtime-behavior work-unit",
            "scenario-keyed",
            "`completion-evidence` MCP tool",
            "documentation-deliverable work-unit",
            "gate coverage",
            "behavior_form",
            "gate",
            "structural, coherence, and conformance",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, delivery)

        self.assertNotIn("#454", delivery)
        self.assertNotIn("deferred", delivery)
        self.assertNotRegex(delivery, r"documentation-deliverable work-unit[^.]+scenarios")

    def test_named_gate_form_agrees_with_contract_skill_lifecycle(self) -> None:
        verify_body = normalized(read(VERIFY_PROTOCOL))
        behavior_row = lifecycle_rows(read(CONTRACT_SKILL))["Behavior"]

        for expected in [
            "documentation-deliverable gates",
            "scenario or gate coverage",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, behavior_row)
                self.assertIn(expected, verify_body)


if __name__ == "__main__":
    unittest.main()
