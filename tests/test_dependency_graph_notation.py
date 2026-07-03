"""The dependency-graph notation has exactly one canonical definition.

Canonical: docs/architecture/work-unit-model.md § Dependency Graph Format —
a Mermaid ``graph TD`` diagram plus a layered text summary. The decompose
protocol and its templates reference must defer to it, and no instruction
file may mandate a competing notation. This gate exists because the
methodology once shipped two conflicting canonical formats (Mermaid in the
model/protocol, ASCII art in the templates reference) and an agent
decomposing an epic had to guess.
"""

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_UNIT_MODEL = ROOT / "docs" / "architecture" / "work-unit-model.md"
DECOMPOSE_PROTOCOL = ROOT / "protocols" / "decompose" / "PROTOCOL.md"
TEMPLATES = ROOT / "protocols" / "decompose" / "references" / "templates.md"


def instruction_files() -> list[Path]:
    return sorted(
        [
            *ROOT.glob("protocols/*/PROTOCOL.md"),
            *ROOT.glob("protocols/*/references/*.md"),
            *ROOT.glob("skills/*/SKILL.md"),
            *ROOT.glob("skills/*/references/*.md"),
        ]
    )


class DependencyGraphNotationTests(unittest.TestCase):
    def test_work_unit_model_defines_the_canonical_format(self) -> None:
        body = WORK_UNIT_MODEL.read_text(encoding="utf-8")
        section = re.search(
            r"## Dependency Graph Format\n(?P<section>.*?)(?:\n## |\Z)",
            body,
            re.DOTALL,
        )
        self.assertIsNotNone(
            section, "work-unit-model.md must keep its Dependency Graph Format section"
        )
        text = section.group("section")
        self.assertIn("```mermaid", text)
        self.assertIn("graph TD", text)
        self.assertIn("Layered text summary", text)

    def test_decompose_protocol_defers_to_the_canonical_format(self) -> None:
        body = DECOMPOSE_PROTOCOL.read_text(encoding="utf-8")
        self.assertIn("Mermaid `graph TD`", body)
        self.assertIn("work-unit-model.md", body)

    def test_templates_reference_defers_and_shows_both_representations(self) -> None:
        body = TEMPLATES.read_text(encoding="utf-8")
        notation = re.search(
            r"## Dependency Graph Notation\n(?P<section>.*?)(?:\n## |\Z)",
            body,
            re.DOTALL,
        )
        self.assertIsNotNone(
            notation, "templates.md must keep its Dependency Graph Notation section"
        )
        text = notation.group("section")
        self.assertIn("work-unit-model.md", text)
        self.assertIn("```mermaid", text)
        self.assertIn("Layer 0", text)

    def test_every_templates_dependency_graph_block_is_mermaid(self) -> None:
        body = TEMPLATES.read_text(encoding="utf-8")
        sections = re.findall(
            r"^## Dependency graph\n(.*?)(?=^## )", body, re.DOTALL | re.MULTILINE
        )
        self.assertNotEqual(
            [], sections, "templates.md should contain dependency graph blocks"
        )
        for section in sections:
            self.assertIn(
                "```mermaid",
                section,
                "every dependency graph block in templates.md must use the "
                "canonical Mermaid representation",
            )

    def test_instruction_files_do_not_declare_a_rival_dependency_graph_block(self) -> None:
        for path in instruction_files():
            body = path.read_text(encoding="utf-8")
            graph_sections = re.findall(
                r"^##[^\n]*Dependency [Gg]raph[^\n]*\n(?P<section>.*?)(?=^## |\Z)",
                body,
                re.DOTALL | re.MULTILINE,
            )
            with self.subTest(source=path.relative_to(ROOT)):
                for section in graph_sections:
                    if "```" in section:
                        self.assertIn("```mermaid", section)


if __name__ == "__main__":
    unittest.main()
