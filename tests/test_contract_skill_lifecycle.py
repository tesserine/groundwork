import re
import unittest
from pathlib import Path

from tooling.prose_conformance import frontmatter


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_SKILL = ROOT / "skills" / "contract" / "SKILL.md"
CHANGELOG = ROOT / "CHANGELOG.md"
CONTRACT_SURFACE = [
    CONTRACT_SKILL,
    ROOT / "skills" / "contract" / "references" / "documentation-contract.md",
    ROOT / "skills" / "contract" / "references" / "code-quality-contract.md",
]
AUTHORING_DOCTRINE_SURFACE = [
    CONTRACT_SKILL,
    ROOT / "protocols" / "take" / "PROTOCOL.md",
    ROOT / "protocols" / "decompose" / "PROTOCOL.md",
    ROOT / "skills" / "work-unit-craft" / "SKILL.md",
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
MIGRATED_LIFECYCLE_CONSUMERS = {
    ROOT / "protocols" / "land" / "PROTOCOL.md",
    ROOT / "protocols" / "plan" / "PROTOCOL.md",
    ROOT / "protocols" / "implement" / "PROTOCOL.md",
    ROOT / "protocols" / "review" / "PROTOCOL.md",
    ROOT / "protocols" / "submit" / "PROTOCOL.md",
    ROOT / "protocols" / "take" / "PROTOCOL.md",
    ROOT / "protocols" / "verify" / "PROTOCOL.md",
}
UNMIGRATED_LIFECYCLE_CONSUMERS = [
    path for path in NON_CONTRACT_INSTRUCTION_FILES if path not in MIGRATED_LIFECYCLE_CONSUMERS
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


def top_section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<section>.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing section: {heading}")
    return match.group("section")


def nested_section(body: str, heading: str, level: int) -> str:
    marks = "#" * level
    parent_or_sibling_heading = rf"#{{1,{min(level, 6)}}}"
    pattern = re.compile(
        rf"^{marks} {re.escape(heading)}\n(?P<section>.*?)(?=^{parent_or_sibling_heading} |\Z)",
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
    def test_nested_section_stops_at_parent_heading(self) -> None:
        body = """## Parent
### Sibling
#### Target
target content
##### Child
child content
## Next Parent
outside content
"""

        result = nested_section(body, "Target", 4)

        self.assertIn("target content", result)
        self.assertIn("child content", result)
        self.assertNotIn("outside content", result)

    def test_contract_version_and_changelog_record_disposition_default(self) -> None:
        body = read(CONTRACT_SKILL)
        changelog = read(CHANGELOG)
        metadata = frontmatter(body)["metadata"]
        unreleased = changelog.split("## [Unreleased]", 1)[1].split("\n## [", 1)[0]

        self.assertRegex(metadata["version"], r"^[0-9]+[.][0-9]+[.][0-9]+$")
        self.assertRegex(metadata["updated"], r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
        self.assertEqual(1, changelog.splitlines().count("## [Unreleased]"))
        self.assertRegex(unreleased, r"(?m)^- \*\*.+\*\* \(#\d+\)")
        self.assertRegex(unreleased, r"\bcontract [0-9]+[.][0-9]+[.][0-9]+->[0-9]+[.][0-9]+[.][0-9]+")

    def test_disposition_default_is_sibling_of_teeth_principle(self) -> None:
        body = read(CONTRACT_SKILL)

        self.assertIn("## The disposition default", body)
        teeth_index = body.index("## The teeth principle")
        disposition_index = body.index("## The disposition default")
        dimensions_index = body.index("## The dimensions")

        self.assertLess(teeth_index, disposition_index)
        self.assertLess(disposition_index, dimensions_index)
        self.assertNotIn("## The dimensions", body[teeth_index:disposition_index])

    def test_teeth_principle_distinguishes_uniform_structure_from_checking_apparatus(self) -> None:
        teeth = normalized(top_section(read(CONTRACT_SKILL), "The teeth principle"))

        for expected in [
            "same contract structure",
            "same evidence obligation",
            "checking apparatus may vary per criterion",
            "`check_kind`",
            "executable",
            "attested",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, teeth)

        forbidden = re.compile(
            r"form of the check fits the dimension|"
            r"forcing one form .* onto every dimension is the mistake|"
            r"documentation earns them through a checklist|"
            r"code quality earns them through corpus principles",
            flags=re.IGNORECASE,
        )
        self.assertIsNone(forbidden.search(teeth))

    def test_dimensions_are_first_class_citizens_of_one_machine(self) -> None:
        dimensions = normalized(top_section(read(CONTRACT_SKILL), "The dimensions"))

        for expected in [
            "first-class symmetric citizen",
            "one contract machine",
            "Behavior is one dimension among N",
            "documentation and code quality carry the identical teeth obligation",
            "same performed-evidence obligation",
            "every dimension a change has carries at least one authored teeth-bearing criterion",
            "coverage is never zero",
            "fewer, simpler teeth-bearing criteria",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, dimensions)

        forbidden = re.compile(
            r"behavior is always present|declared as the change warrants|"
            r"the most developed dimension|behavior is the unit of progress|"
            r"completion is behavior coverage|need not exercise every code path",
            flags=re.IGNORECASE,
        )
        self.assertIsNone(forbidden.search(read(CONTRACT_SKILL)))

    def test_attested_judgment_is_recorded_inside_the_uniform_evidence_surface(self) -> None:
        body = normalized(read(CONTRACT_SKILL))

        for expected in [
            "every criterion in every dimension names the hollow delivery",
            "attested criteria",
            "`completion-evidence.results[]`",
            "reviewer identity",
            "finding",
            "free-form reviewer prose outside the artifact is not evidence",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

        self.assertNotIn("reviewed, looks fine", body.lower())

    def test_contract_richness_is_load_bearing(self) -> None:
        body = normalized(read(CONTRACT_SKILL))
        corruption_modes = normalized(top_section(read(CONTRACT_SKILL), "Corruption Modes"))

        for expected in [
            "contract richness determines product richness",
            "thin labels",
            "generic checklist assertions",
            "empty pass/fail attestations",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

        self.assertIn("**Thin contract.**", corruption_modes)
        self.assertIn("contract richness", corruption_modes)

    def test_dimension_references_emit_typed_criteria_into_the_uniform_surface(self) -> None:
        body = normalized(read(CONTRACT_SKILL))
        documentation = normalized(read(ROOT / "skills" / "contract" / "references" / "documentation-contract.md"))
        code_quality = normalized(read(ROOT / "skills" / "contract" / "references" / "code-quality-contract.md"))

        for text, expected in [
            (body, "typed criteria into the uniform surface"),
            (documentation, "`contract.criteria[]`"),
            (documentation, "`check_kind: \"attested\"`"),
            (code_quality, "`contract.criteria[]`"),
            (code_quality, "`check_kind: \"attested\"`"),
            (code_quality, "consult, do not model"),
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_disposition_default_defines_regenerate_as_the_review_default(self) -> None:
        disposition = normalized(top_section(read(CONTRACT_SKILL), "The disposition default"))

        for expected in [
            "default disposition is regenerate",
            "implementation, planning through submission, carries the burden of proof",
            "contract is corrected",
            "unit is regenerated",
            "unless the delivery proves it qualifies to remain",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, disposition)

    def test_qualification_to_remain_is_positive_per_dimension_and_conjunctive(self) -> None:
        disposition = normalized(top_section(read(CONTRACT_SKILL), "The disposition default"))

        for expected in [
            "Qualification-to-remain is positive, per-dimension, and conjunctive",
            "every declared contract dimension",
            "as sound and elegant as a fresh derivation from the corrected contract",
            "failing the proof on any one dimension regenerates",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, disposition)

        self.assertNotRegex(disposition, r"preference|feels bounded|clearly bounded")

    def test_qualification_test_uses_teeth_form_and_boundary_default(self) -> None:
        disposition = normalized(top_section(read(CONTRACT_SKILL), "The disposition default"))

        for expected in [
            "could a patched branch pass this dimension while carrying structure a fresh derivation from the corrected contract would not",
            "A boundary is necessary, not sufficient",
            "small enough that the in-place fix is indistinguishable from a fresh derivation",
            "When qualification is not clear, the default decides: regenerate",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, disposition)

    def test_disposition_default_stays_distinct_from_failing_test_classification(self) -> None:
        body = read(CONTRACT_SKILL)
        disposition = normalized(top_section(body, "The disposition default"))
        failing_test = normalized(nested_section(body, "When an existing test fails after a change", 4))

        for expected in [
            "where the defect lives",
            "what survives",
            "`When an existing test fails after a change`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, disposition)

        self.assertNotIn("qualifies to remain", failing_test)
        self.assertNotIn("default disposition is regenerate", failing_test)

    def test_refine_default_corruption_mode_is_named(self) -> None:
        corruption_modes = normalized(top_section(read(CONTRACT_SKILL), "Corruption Modes"))

        for expected in [
            "**Refine-default.**",
            "defective branch keeps its branch by default",
            "strictly-bounded-but-large correction",
            "in-place fix",
            "fresh derivation would be simpler or sounder",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, corruption_modes)

    def test_lifecycle_is_stated_once_and_uniformly_for_every_dimension(self) -> None:
        dimensions = normalized(top_section(read(CONTRACT_SKILL), "The dimensions"))

        for expected in [
            "one lifecycle for every dimension",
            "typed criteria in `contract.criteria[]` at `take`",
            "carried through `implement` by `criterion_id`",
            "one result per criterion in `completion-evidence.results[]`",
            "`check_kind`",
            "`land` records the result from that uniform evidence surface",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, dimensions)

    def test_dimension_rows_carry_inputs_and_apparatus_without_stage_variance(self) -> None:
        rows = lifecycle_rows(read(CONTRACT_SKILL))
        expected_cells = {
            "Behavior": [
                "acceptance criteria",
                "scenarios",
                "documentation-deliverable gates",
                '`check_kind: "executable"`',
            ],
            "Documentation": [
                "recipient outcomes",
                "udience-outcome",
                '`check_kind: "attested"`',
            ],
            "Code quality": [
                "corpus pointers",
                "stressed universals",
                "projections",
                "diff loci or findings",
                '`check_kind: "attested"`',
            ],
        }

        self.assertEqual(set(expected_cells), set(rows))
        stage_terms = re.compile(
            r"inputs to validation|validation defined|validation performed|"
            r"carried through|recorded at",
            flags=re.IGNORECASE,
        )
        for dimension, cells in expected_cells.items():
            with self.subTest(dimension=dimension):
                row = rows[dimension]
                for cell in cells:
                    self.assertIn(cell, row)
                self.assertIsNone(
                    stage_terms.search(row),
                    "a dimension row re-encodes lifecycle stages",
                )

    def test_stage_handoffs_have_one_receive_produce_home(self) -> None:
        handoffs = normalized(section(read(CONTRACT_SKILL), "Stage Handoffs"))
        expected_handoffs = [
            "`work-unit-craft`/`decompose` produces inputs to validation",
            "`take` consumes inputs to validation and produces validation defined",
            "typed criteria in `contract.criteria[]`",
            "`plan` consumes validation defined and maps every criterion",
            "`implement` consumes validation defined",
            "`verify` consumes validation defined and produces validation performed",
            "one result per criterion in `completion-evidence.results[]`",
            "`land` consumes validation performed and records what shipped from the uniform evidence surface",
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
        self.assertIn("Consuming protocol migration is complete", intro)
        self.assertIn("epic #443 landed every downstream unit", intro)

    def test_contract_surface_replaces_entry_only_framing_everywhere(self) -> None:
        forbidden = re.compile(
            r"declared at `take`|At `take`, the contract declares|declared at entry|"
            r"Each dimension is \*\*declared\*\* at `take`",
            flags=re.IGNORECASE,
        )

        for path in CONTRACT_SURFACE:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(forbidden.search(read(path)))

    def test_density_rule_distinguishes_simple_criteria_from_zero_coverage(self) -> None:
        dimensions = normalized(top_section(read(CONTRACT_SKILL), "The dimensions"))

        for expected in [
            "Density is situational",
            "coverage and teeth are not situational",
            "never zero for a dimension the change has",
            "simple criteria are legitimate",
            "silent dimensions are not",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, dimensions)

        self.assertNotIn("Pointer-as-default", read(CONTRACT_SKILL))

    def test_authoring_surfaces_reject_pointer_and_silence_doctrine(self) -> None:
        forbidden = re.compile(
            r"Pointer-as-default|"
            r"general contract pointer|"
            r"general contract remains the validation pointer|"
            r"silence is valid|"
            r"not a mandatory per-dimension (?:declaration|body section|block)|"
            r"dimension with no special input (?:uses|remains covered by)|"
            r"no special input uses its general contract|"
            r"need not exercise every code path",
            flags=re.IGNORECASE,
        )

        for path in AUTHORING_DOCTRINE_SURFACE:
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIsNone(forbidden.search(read(path)))

    def test_silent_dimension_corruption_mode_is_named(self) -> None:
        corruption_modes = normalized(top_section(read(CONTRACT_SKILL), "Corruption Modes"))

        for expected in [
            "**Silent dimension.**",
            "a dimension the change has, left with no authored teeth-bearing criterion",
            "pointer has no teeth",
            "uncovered dimension hollows the contract",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, corruption_modes)

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
