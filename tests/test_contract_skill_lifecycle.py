import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SKILL = ROOT / "skills" / "contract" / "SKILL.md"
CONTRACT_SURFACE = [
    CONTRACT_SKILL,
    ROOT / "skills" / "contract" / "references" / "documentation-contract.md",
    ROOT / "skills" / "contract" / "references" / "code-quality-contract.md",
]


def contract_text() -> str:
    return CONTRACT_SKILL.read_text(encoding="utf-8")


def normalized_contract_text() -> str:
    return re.sub(r"\s+", " ", contract_text())


class ContractSkillLifecycleTests(unittest.TestCase):
    def test_lifecycle_roles_are_stated_for_every_dimension(self) -> None:
        body = contract_text()

        for dimension in ["Behavior", "Documentation", "Code quality"]:
            with self.subTest(dimension=dimension):
                row = re.search(rf"\| \*\*{dimension}\*\* \|(?P<row>[^\n]+)", body)
                self.assertIsNotNone(row)
                for expected in [
                    "inputs to validation",
                    "validation defined",
                    "validation performed",
                    "carried through `implement`",
                    "recorded at `land`",
                ]:
                    self.assertIn(expected, row.group("row"))

    def test_stage_handoffs_name_inputs_and_outputs(self) -> None:
        body = normalized_contract_text()

        for expected in [
            "issue-craft produces inputs to validation",
            "`take` consumes inputs to validation and produces validation defined",
            "`verify` consumes validation defined and produces validation performed",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

    def test_pointer_as_default_distinguishes_consideration_from_declaration(self) -> None:
        body = normalized_contract_text()

        for expected in [
            "Pointer-as-default",
            "consider every dimension",
            "not a mandatory per-dimension declaration",
            "general contract remains the validation pointer",
            "density across dimensions is unequal; consideration is equal",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

    def test_documentation_deliverable_behavior_gates_are_named(self) -> None:
        body = normalized_contract_text()

        for expected in [
            "documentation-deliverable",
            "structural",
            "coherence",
            "conformance",
            "reference-link resolution",
            "template-schema conformance",
            "internal coherence",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

    def test_contract_skill_remains_lifecycle_single_home(self) -> None:
        body = normalized_contract_text()

        self.assertNotIn("Each dimension is **declared** at `take`", contract_text())
        for expected in [
            "per-stage protocols point here for their role",
            "do not duplicate this lifecycle",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

    def test_contract_surface_does_not_keep_entry_only_lifecycle_framing(self) -> None:
        forbidden = [
            "At `take`, the contract declares",
            "declared at `take`",
        ]

        for path in CONTRACT_SURFACE:
            body = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                with self.subTest(path=path.relative_to(ROOT), phrase=phrase):
                    self.assertNotIn(phrase, body)


if __name__ == "__main__":
    unittest.main()
