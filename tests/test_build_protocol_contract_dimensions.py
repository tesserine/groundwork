import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN_PROTOCOL = ROOT / "protocols" / "plan" / "PROTOCOL.md"
IMPLEMENT_PROTOCOL = ROOT / "protocols" / "implement" / "PROTOCOL.md"
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


class BuildProtocolContractDimensionTests(unittest.TestCase):
    def test_plan_maps_every_contract_criterion_across_all_dimensions(self) -> None:
        body = normalized(read(PLAN_PROTOCOL))

        for expected in [
            "multidimensional contract",
            "behavior dimension",
            "documentation",
            "code-quality",
            "every contract criterion",
            "`criterion_id`",
            "`contract.criteria[]`",
            "`contract` skill",
            "One mapping shape serves every dimension",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

    def test_implement_drives_executable_criteria_check_first(self) -> None:
        cycle = normalized(section(read(IMPLEMENT_PROTOCOL), "Steps"))

        for expected in [
            "contract criterion",
            "executable criterion",
            "attested criterion",
            "scenario test",
            "structural, coherence,",
            "conformance gate",
            "watch the check fail",
            "every declared dimension",
            "`contract` skill",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, cycle)

    def test_build_protocols_consult_contract_lifecycle_without_reencoding_it(self) -> None:
        dimension_row = re.compile(
            r"\| \*\*(?:Behavior|Documentation|Code quality)\*\* \|",
        )

        for path in [PLAN_PROTOCOL, IMPLEMENT_PROTOCOL]:
            body = read(path)
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("`contract` skill", normalized(body))
                self.assertIn("`skills/contract/SKILL.md`", body)
                self.assertIn("contract lifecycle", body)
                self.assertIsNone(dimension_row.search(body))

    def test_named_apparatus_agrees_with_contract_skill(self) -> None:
        skill_body = normalized(read(CONTRACT_SKILL)).lower()
        combined = normalized(read(PLAN_PROTOCOL) + "\n" + read(IMPLEMENT_PROTOCOL)).lower()

        for expected in [
            "executable scenario",
            "conformance gate",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, skill_body)
                self.assertIn(expected, combined)

    def test_artifact_delivery_is_criterion_keyed_for_every_dimension(self) -> None:
        plan_delivery = normalized(step(read(PLAN_PROTOCOL), 5))
        implement_delivery = normalized(section(read(IMPLEMENT_PROTOCOL), "Deliver `test-evidence`"))

        for delivery, artifact, mapping_key in [
            (plan_delivery, "`implementation-plan` MCP tool", "criterion_mapping"),
            (implement_delivery, "`test-evidence` MCP tool", "evidence"),
        ]:
            with self.subTest(artifact=artifact):
                for expected in [
                    artifact,
                    mapping_key,
                    "criterion_id",
                    "every dimension",
                ]:
                    self.assertIn(expected, delivery)
                self.assertNotIn("#454", delivery)
                self.assertNotIn("deferred", delivery)
                self.assertNotIn("behavior_form", delivery)

        self.assertIn("one mapping per contract criterion", plan_delivery)
        self.assertIn("each executable criterion's cycle", implement_delivery)

    def test_scenario_only_corruption_modes_and_cross_references_are_generalized(self) -> None:
        plan_body = read(PLAN_PROTOCOL)
        implement_body = read(IMPLEMENT_PROTOCOL)
        corruption_modes = normalized(
            section(plan_body, "Corruption Modes") + "\n" + section(implement_body, "Corruption Modes")
        )
        cross_references = normalized(
            section(plan_body, "Cross-References") + "\n" + section(implement_body, "Cross-References")
        )
        combined = corruption_modes + " " + cross_references

        for expected in [
            "contract criterion",
            "contract's criteria",
            "criterion ordering",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, combined)

        scenario_only_phrases = [
            r"map to no scenario",
            r"from named scenarios",
            r"each RED test corresponds to a named scenario",
            r"scenario ordering this protocol executes",
            r"deliverable's behavior form",
        ]
        for phrase in scenario_only_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotRegex(combined, phrase)

    def test_reckon_invocation_iron_law_and_versions_survive(self) -> None:
        plan_body = read(PLAN_PROTOCOL)
        implement_body = read(IMPLEMENT_PROTOCOL)

        self.assertIn("version: \"2.5.0\"", plan_body)
        self.assertIn("version: \"2.4.0\"", implement_body)
        self.assertIn("the reckon skill is the move", plan_body)
        self.assertIn("the reckon skill is the move", implement_body)
        self.assertIn("NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST", implement_body)


if __name__ == "__main__":
    unittest.main()
