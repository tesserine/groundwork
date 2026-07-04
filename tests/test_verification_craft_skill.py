import re
import unittest
from pathlib import Path

from tooling.prose_conformance import frontmatter, has_semantic_clause, markdown_section


ROOT = Path(__file__).resolve().parents[1]
VERIFICATION_CRAFT = ROOT / "skills" / "verification-craft" / "SKILL.md"
README = ROOT / "README.md"


def read_skill() -> str:
    return VERIFICATION_CRAFT.read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class VerificationCraftSkillTests(unittest.TestCase):
    def test_skill_frontmatter_declares_discoverable_verification_craft(self) -> None:
        body = read_skill()
        data = frontmatter(body)

        self.assertEqual("verification-craft", data["name"])
        self.assertIn("Use when authoring or reviewing a verification gate", body)
        self.assertIn("matching vocabulary as a proxy", body)
        self.assertIn("metadata", data)
        self.assertEqual("1.0.0", data["metadata"]["version"])
        self.assertRegex(data["metadata"]["updated"], r"^2026-07-04$")

    def test_readme_skill_index_links_the_discovery_path(self) -> None:
        readme = README.read_text(encoding="utf-8")
        skills = markdown_section(readme, "The Shape of the Methodology")

        self.assertIn("[`skills/verification-craft/SKILL.md`](skills/verification-craft/SKILL.md)", skills)
        self.assertIn("verification gates", skills)

    def test_rule_is_positive_and_names_the_three_regrounded_forms(self) -> None:
        body = read_skill()

        self.assertTrue(
            has_semantic_clause(
                body,
                r"\bgate\b",
                r"\bconsults?\b",
                r"\binvariant\b",
                r"\bowning authority\b",
                r"\bsubstrate structure\b",
            )
        )
        self.assertTrue(
            has_semantic_clause(
                body,
                r"\bdoes not match\b",
                r"\bliteral vocabulary\b",
                r"\bproxy\b",
            )
        )
        for heading in ["Authority-Consultation", "Model-Coherence", "Structural"]:
            with self.subTest(heading=heading):
                self.assertIn(f"### {heading}", body)

    def test_each_regrounded_form_points_to_a_live_head_example(self) -> None:
        body = read_skill()

        expected_examples = {
            "Authority-Consultation": [
                "tests/test_protocol_artifact_delivery_docs.py",
                "delivery_boundaries",
                "manifest.toml",
            ],
            "Model-Coherence": [
                "test_entry_surfaces_ground_on_the_whole_ticket",
                "entry_surface_coherence",
                "comment-log lifecycle",
            ],
            "Structural": [
                "test_every_templates_dependency_graph_block_is_mermaid",
                "tests/test_dependency_graph_notation.py",
                "Markdown structure",
            ],
        }
        for heading, expected_terms in expected_examples.items():
            section = markdown_section(body, heading, level=3)
            with self.subTest(heading=heading):
                for term in expected_terms:
                    self.assertIn(term, section)

    def test_retain_boundary_teaches_token_is_invariant_with_a_retained_example(self) -> None:
        body = read_skill()
        section = normalized(markdown_section(body, "Retain Boundary: Token Is Invariant"))

        self.assertRegex(section, r"\bliteral-token check is legitimate\b")
        self.assertRegex(section, r"\btoken is the invariant\b")
        self.assertRegex(section, r"\bretired identifiers\b")
        self.assertRegex(section, r"\bschema fields\b")
        self.assertIn("RETIRED_FORGE_IDENTIFIER_PATTERNS", section)
        self.assertIn("forge_tags", section)
        self.assertIn("RUNA_FORGE_", section)
        self.assertRegex(section, r"\bfull owning surface\b")

    def test_paraphrase_residual_boundary_rejects_synonym_lists(self) -> None:
        body = read_skill()
        section = normalized(markdown_section(body, "Paraphrase-Residual Boundary"))

        self.assertRegex(section, r"\bdoes not enumerate anticipated paraphrases\b")
        self.assertRegex(section, r"\bpositive authority-consultation or model-coherence check\b")
        self.assertRegex(section, r"\btoken-is-invariant detectors\b")
        self.assertRegex(section, r"\bfull owning surface\b")
        self.assertRegex(section, r"\bnovel paraphrase\b")
        self.assertRegex(section, r"\bdo not grow a synonym list\b")
        for invented_phrase in ["not yet wired", "until it is wired", "you drive the session"]:
            with self.subTest(invented_phrase=invented_phrase):
                self.assertNotIn(invented_phrase, section)

    def test_surface_is_structured_for_the_sibling_positive_form_face(self) -> None:
        body = normalized(read_skill())

        self.assertRegex(body, r"\bvocabulary-proxy face\b")
        self.assertRegex(body, r"\bpositive-form face\b")
        self.assertRegex(body, r"\bsibling section\b")

    def test_procedure_requires_authority_classification_fixture_and_full_surface(self) -> None:
        procedure = normalized(markdown_section(read_skill(), "Authoring Procedure"))

        for expected in [
            "Name the protected invariant",
            "Name the owning authority",
            "Classify the gate",
            "Add a proof fixture",
            "Scan the full owning surface",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, procedure)


if __name__ == "__main__":
    unittest.main()
