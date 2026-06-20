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


class BuildProtocolContractDimensionTests(unittest.TestCase):
    def test_plan_maps_behavior_in_deliverable_form_and_serves_all_dimensions(self) -> None:
        body = normalized(read(PLAN_PROTOCOL))

        for expected in [
            "multidimensional contract",
            "behavior dimension",
            "documentation dimension",
            "code-quality dimension",
            "runtime-behavior work-unit",
            "executable scenarios",
            "documentation-deliverable work-unit",
            "structural, coherence, and conformance gates",
            "`contract` skill",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

    def test_implement_drives_behavior_items_check_first_in_deliverable_form(self) -> None:
        cycle = normalized(section(read(IMPLEMENT_PROTOCOL), "Steps"))

        for expected in [
            "behavior item",
            "runtime-behavior work-unit",
            "scenario test",
            "documentation-deliverable work-unit",
            "structural, coherence, and conformance gate",
            "watch the check fail",
            "all three declared dimensions",
            "`contract` skill",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, cycle)

    def test_build_protocols_consult_contract_lifecycle_without_reencoding_it(self) -> None:
        lifecycle_table = re.compile(
            r"\| \*\*(?:Behavior|Documentation|Code quality)\*\* \| .*?"
            r"(?:inputs to validation|validation defined|validation performed)",
            flags=re.IGNORECASE,
        )

        for path in [PLAN_PROTOCOL, IMPLEMENT_PROTOCOL]:
            body = read(path)
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("`contract` skill", body)
                self.assertIn("`skills/contract/SKILL.md`", body)
                self.assertIn("behavior lifecycle", body)
                self.assertIsNone(lifecycle_table.search(body))

    def test_named_behavior_forms_agree_with_contract_skill_lifecycle(self) -> None:
        behavior_row = lifecycle_rows(read(CONTRACT_SKILL))["Behavior"]
        combined = normalized(read(PLAN_PROTOCOL) + "\n" + read(IMPLEMENT_PROTOCOL))

        for expected in [
            "executable scenarios",
            "documentation-deliverable gates",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, behavior_row)
                self.assertIn(expected, combined)

    def test_gate_form_runtime_artifact_delivery_names_454_deferral(self) -> None:
        plan_delivery = normalized(step(read(PLAN_PROTOCOL), 5))
        implement_delivery = normalized(section(read(IMPLEMENT_PROTOCOL), "Deliver `test-evidence`"))

        for delivery, artifact in [
            (plan_delivery, "`implementation-plan` MCP tool"),
            (implement_delivery, "`test-evidence` MCP tool"),
        ]:
            with self.subTest(artifact=artifact):
                for expected in [
                    "runtime-behavior work-unit",
                    "scenario-keyed",
                    artifact,
                    "documentation-deliverable work-unit",
                    "gate-form",
                    "committed evidence",
                    "#454",
                    "deferred",
                ]:
                    self.assertIn(expected, delivery)
                self.assertNotRegex(delivery, r"documentation-deliverable work-unit[^.]+scenario")

    def test_scenario_only_corruption_modes_and_cross_references_are_generalized(self) -> None:
        plan_body = read(PLAN_PROTOCOL)
        implement_body = read(IMPLEMENT_PROTOCOL)
        corruption_modes = normalized(
            section(plan_body, "Corruption Modes") + "\n" + section(implement_body, "Corruption Modes")
        )
        cross_references = normalized(
            section(plan_body, "Cross-References") + "\n" + section(implement_body, "Cross-References")
        )

        for expected in [
            "behavior item",
            "deliverable's behavior form",
            "scenario or gate",
            "structural, coherence, and conformance gate",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, corruption_modes + " " + cross_references)

        scenario_only_phrases = [
            r"map to no scenario",
            r"from named scenarios",
            r"each RED test corresponds to a named scenario",
            r"scenario ordering this protocol executes",
        ]
        for phrase in scenario_only_phrases:
            with self.subTest(phrase=phrase):
                self.assertNotRegex(corruption_modes + " " + cross_references, phrase)

    def test_reckon_invocation_iron_law_and_versions_survive(self) -> None:
        plan_body = read(PLAN_PROTOCOL)
        implement_body = read(IMPLEMENT_PROTOCOL)

        self.assertIn("version: \"2.3.0\"", plan_body)
        self.assertIn("version: \"2.2.0\"", implement_body)
        self.assertIn("the reckon skill is the move", plan_body)
        self.assertIn("the reckon skill is the move", implement_body)
        self.assertIn("NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST", implement_body)


if __name__ == "__main__":
    unittest.main()
