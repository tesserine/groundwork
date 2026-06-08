import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECOMPOSE_PROTOCOL = ROOT / "protocols" / "decompose" / "PROTOCOL.md"
DECOMPOSE_TEMPLATES = ROOT / "protocols" / "decompose" / "references" / "templates.md"


def normalized(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


class DecomposeEpicCompletionDocsTests(unittest.TestCase):
    def capability_epic_example(self) -> str:
        body = DECOMPOSE_TEMPLATES.read_text(encoding="utf-8")
        match = re.search(
            r"### Example: epic issue\n\n```markdown\n(?P<example>.*?)\n```\n\n---\n\n## Bug Report",
            body,
            re.DOTALL,
        )
        self.assertIsNotNone(match)
        return match.group("example")

    def test_protocol_names_epic_completion_taxonomy_and_terminal_steps(self) -> None:
        body = normalized(DECOMPOSE_PROTOCOL)

        expected = [
            "capability epics",
            "operator-facing capability",
            "component release work plus a terminal ecosystem-release work-unit",
            "knowledge/spike epics",
            "ADR or recorded decision",
            "decomposition/planning epics",
            "filed sub-issues",
            "process/ceremony epics",
            "adopted process",
        ]

        for phrase in expected:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, body)

    def test_capability_epic_example_includes_terminal_ecosystem_release_task(self) -> None:
        example = self.capability_epic_example()
        task_issues = re.search(
            r"## Task issues\n(?P<section>.*?)\n## Dependency graph",
            example,
            re.DOTALL,
        )
        self.assertIsNotNone(task_issues)

        self.assertRegex(
            task_issues.group("section"),
            r"- \[ \] #\d+ .*ecosystem-release.*public fact",
        )

    def test_protocol_references_commons_release_authority_without_reimplementing_it(self) -> None:
        body = normalized(DECOMPOSE_PROTOCOL)

        expected = [
            "ADR-0011",
            "ADR-0012",
            "ADR-0014",
            "ECOSYSTEM-RELEASE.md",
            "does not define the manifest schema, version choice, verification, or publication procedure",
        ]

        for phrase in expected:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, body)

    def test_epic_template_prompts_for_completion_boundary(self) -> None:
        body = normalized(DECOMPOSE_TEMPLATES)

        expected = [
            "## Completion boundary",
            "Classify the epic by the terminal step that makes its output real for its recipient.",
            "capability -> component release work plus terminal ecosystem-release work-unit",
            "knowledge/spike -> ADR or recorded decision",
            "decomposition/planning -> filed sub-issues",
            "process/ceremony -> adopted process",
        ]

        for phrase in expected:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, body)


if __name__ == "__main__":
    unittest.main()
