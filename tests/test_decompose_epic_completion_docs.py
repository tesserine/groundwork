import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DECOMPOSE_PROTOCOL = ROOT / "protocols" / "decompose" / "PROTOCOL.md"
DECOMPOSE_TEMPLATES = ROOT / "protocols" / "decompose" / "references" / "templates.md"


def normalized(path: Path) -> str:
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8"))


class DecomposeEpicCompletionDocsTests(unittest.TestCase):
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
