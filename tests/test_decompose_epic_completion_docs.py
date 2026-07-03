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
        body = DECOMPOSE_PROTOCOL.read_text(encoding="utf-8")
        procedure = re.search(
            r"### decompose-epic\n(?P<section>.*?)(?=^### )",
            body,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(procedure)

        for boundary in ["capability", "knowledge/spike", "decomposition/planning", "process/ceremony"]:
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, procedure.group("section"))

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

        for authority in ["ADR-0011", "ADR-0012", "ADR-0014", "ECOSYSTEM-RELEASE.md"]:
            with self.subTest(authority=authority):
                self.assertIn(authority, body)

    def test_epic_template_prompts_for_completion_boundary(self) -> None:
        body = DECOMPOSE_TEMPLATES.read_text(encoding="utf-8")
        boundary = re.search(
            r"## Completion boundary\n(?P<section>.*?)(?=^## )",
            body,
            re.DOTALL | re.MULTILINE,
        )
        self.assertIsNotNone(boundary)
        checklist = re.findall(r"^- (?P<boundary>[^-]+)->", boundary.group("section"), re.MULTILINE)
        self.assertEqual(
            ["capability ", "knowledge/spike ", "decomposition/planning ", "process/ceremony "],
            checklist,
        )


if __name__ == "__main__":
    unittest.main()
