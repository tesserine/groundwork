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
INSTRUCTION_FILES = [
    *sorted((ROOT / "protocols").glob("*/PROTOCOL.md")),
    *sorted((ROOT / "protocols").glob("*/references/*.md")),
    *sorted((ROOT / "skills").glob("*/SKILL.md")),
    *sorted((ROOT / "skills").glob("*/references/*.md")),
]
NON_CONTRACT_INSTRUCTION_FILES = [
    path for path in INSTRUCTION_FILES if not path.is_relative_to(ROOT / "skills" / "contract")
]
UNMIGRATED_LIFECYCLE_CONSUMERS = [
    path
    for path in NON_CONTRACT_INSTRUCTION_FILES
    if path != ROOT / "protocols" / "take" / "PROTOCOL.md"
]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^### {re.escape(heading)}\n(?P<section>.*?)(?=^### |^## |\Z)",
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


class ContractSkillLifecycleTests(unittest.TestCase):
    def test_lifecycle_matrix_covers_every_dimension_stage_cell(self) -> None:
        rows = lifecycle_rows(read(CONTRACT_SKILL))
        expected_cells = {
            "Behavior": [
                "acceptance criteria",
                "inputs to validation",
                "validation defined",
                "executable scenarios",
                "documentation-deliverable gates",
                "carried through `implement`",
                "validation performed",
                "scenario or gate coverage",
                "recorded at `land`",
            ],
            "Documentation": [
                "recipient outcomes",
                "inputs to validation",
                "validation defined",
                "documentation outcomes",
                "carried through `implement`",
                "validation performed",
                "audience-outcome review",
                "recorded at `land`",
            ],
            "Code quality": [
                "corpus pointers",
                "stressed universals",
                "inputs to validation",
                "validation defined",
                "reviewer-checkable projections",
                "carried through `implement`",
                "validation performed",
                "diff loci or findings",
                "recorded at `land`",
            ],
        }

        self.assertEqual(set(expected_cells), set(rows))
        for dimension, cells in expected_cells.items():
            with self.subTest(dimension=dimension):
                row = rows[dimension]
                for cell in cells:
                    self.assertIn(cell, row)

    def test_stage_handoffs_have_one_receive_produce_home(self) -> None:
        handoffs = normalized(section(read(CONTRACT_SKILL), "Stage Handoffs"))
        expected_handoffs = [
            "`work-unit-craft`/`decompose` produces inputs to validation",
            "`take` consumes inputs to validation and produces validation defined",
            "`implement` consumes validation defined",
            "`verify` consumes validation defined and produces validation performed",
            "`land` consumes validation performed",
        ]

        for handoff in expected_handoffs:
            with self.subTest(handoff=handoff):
                self.assertIn(handoff, handoffs)

        duplicated_lifecycle_terms = re.compile(
            r"inputs to validation|validation defined|validation performed|documentation-deliverable gates"
        )
        for path in UNMIGRATED_LIFECYCLE_CONSUMERS:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(duplicated_lifecycle_terms.search(read(path)))

    def test_contract_surface_uses_public_work_unit_authoring_stage_names(self) -> None:
        deprecated_stage_name = re.compile(r"\bissue-craft\b", flags=re.IGNORECASE)

        for path in CONTRACT_SURFACE:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(deprecated_stage_name.search(read(path)))

        handoffs = normalized(section(read(CONTRACT_SKILL), "Stage Handoffs"))
        first_handoff = handoffs.split(".")[0]
        self.assertIn("`work-unit-craft`/`decompose` produces inputs to validation", first_handoff)
        self.assertNotRegex(first_handoff, r"\bissue-craft\b")

    def test_lifecycle_single_home_claim_is_scoped_to_contract_surface(self) -> None:
        body = read(CONTRACT_SKILL)
        intro = normalized(body.split("## The teeth principle", maxsplit=1)[0])

        self.assertIn("declares the lifecycle as the single home for the contract surface", intro)
        self.assertIn("migration proceeds unit by unit across epic #443", intro)
        present_tense_protocol_claim = re.compile(
            r"(?:per-stage|consuming) protocols (?:now |already )?consult this home|"
            r"protocols consult this home|instead of keeping their own lifecycle statement",
            flags=re.IGNORECASE,
        )
        self.assertNotRegex(
            intro,
            present_tense_protocol_claim,
        )

    def test_contract_surface_replaces_entry_only_framing_everywhere(self) -> None:
        forbidden = re.compile(
            r"declared at `take`|At `take`, the contract declares|declared at entry|"
            r"Each dimension is \*\*declared\*\* at `take`",
            flags=re.IGNORECASE,
        )

        for path in CONTRACT_SURFACE:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(forbidden.search(read(path)))

    def test_pointer_as_default_distinguishes_consideration_from_dense_inputs(self) -> None:
        pointer = normalized(section(read(CONTRACT_SKILL), "Pointer-as-default"))

        self.assertRegex(pointer, r"consider every dimension")
        self.assertRegex(pointer, r"not a mandatory per-dimension declaration")
        self.assertRegex(pointer, r"general contract remains the validation pointer")
        self.assertRegex(pointer, r"density across dimensions is unequal; consideration is equal")
        self.assertNotRegex(pointer, r"no special input[^.]+not validated")

    def test_documentation_deliverable_gates_define_behavior_teeth(self) -> None:
        gates = normalized(section(read(CONTRACT_SKILL), "Documentation-deliverable behavior gates"))
        required_mappings = [
            r"Structural gates[^.]+reference-link resolution",
            r"Structural gates[^.]+script-path resolution",
            r"Conformance gates[^.]+template-schema conformance",
            r"Coherence gates[^.]+internal coherence",
            r"broken links fail structural validation",
            r"schema fails conformance",
            r"lifecycle[^.]+sections fails internal coherence",
        ]

        for mapping in required_mappings:
            with self.subTest(mapping=mapping):
                self.assertRegex(gates, mapping)


if __name__ == "__main__":
    unittest.main()
