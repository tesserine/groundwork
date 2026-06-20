import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMIT_PROTOCOL = ROOT / "protocols" / "submit" / "PROTOCOL.md"
REVIEW_PROTOCOL = ROOT / "protocols" / "review" / "PROTOCOL.md"
LAND_PROTOCOL = ROOT / "protocols" / "land" / "PROTOCOL.md"
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


class CloseProtocolContractDimensionTests(unittest.TestCase):
    def test_submit_packages_every_declared_dimension(self) -> None:
        body = normalized(read(SUBMIT_PROTOCOL))
        prepare = normalized(step(read(SUBMIT_PROTOCOL), 3))

        for expected in [
            "multidimensional contract",
            "behavior dimension",
            "documentation dimension",
            "code-quality dimension",
            "validation-performed",
            "`contract` skill",
            "completion evidence",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

        for expected in [
            "behavior coverage",
            "documentation outcomes",
            "code-quality findings",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, prepare)

    def test_review_judges_every_declared_dimension(self) -> None:
        inspection = normalized(step(read(REVIEW_PROTOCOL), 2))

        for expected in [
            "multidimensional contract",
            "behavior dimension",
            "documentation dimension",
            "code-quality dimension",
            "performed validation",
            "audience-outcome review",
            "code-quality findings",
            "`contract` skill",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, inspection)

    def test_land_records_all_dimensions_without_claiming_new_schema_fields(self) -> None:
        delivery = normalized(step(read(LAND_PROTOCOL), 5))

        for expected in [
            "behavior dimension",
            "criterion_summary",
            "documentation dimension",
            "documentation_status",
            "code-quality dimension",
            "committed evidence",
            "completion-record",
            "existing schema fields",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, delivery)

        self.assertNotIn("#454", delivery)
        self.assertNotIn("deferred", delivery)
        self.assertNotRegex(delivery, r"code_quality[\":]")

    def test_close_protocols_carry_behavior_in_the_deliverable_form(self) -> None:
        for path in [SUBMIT_PROTOCOL, REVIEW_PROTOCOL, LAND_PROTOCOL]:
            body = normalized(read(path))
            with self.subTest(path=path.relative_to(ROOT)):
                for expected in [
                    "runtime-behavior work-unit",
                    "documentation-deliverable work-unit",
                    "deliverable's behavior form",
                    "scenario or gate",
                    "gate-form",
                ]:
                    self.assertIn(expected, body)
                self.assertNotRegex(body, r"documentation-deliverable work-unit[^.]+scenarios")

    def test_close_protocols_consult_contract_lifecycle_without_reencoding_it(self) -> None:
        lifecycle_table = re.compile(
            r"\| \*\*(?:Behavior|Documentation|Code quality)\*\* \| .*?"
            r"(?:inputs to validation|validation defined|validation performed)",
            flags=re.IGNORECASE,
        )

        for path in [SUBMIT_PROTOCOL, REVIEW_PROTOCOL, LAND_PROTOCOL]:
            body = read(path)
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("`contract` skill", body)
                self.assertIn("`skills/contract/SKILL.md`", body)
                self.assertIn("lifecycle", body)
                self.assertIsNone(lifecycle_table.search(body))

    def test_named_behavior_forms_agree_with_contract_skill_lifecycle(self) -> None:
        behavior_row = lifecycle_rows(read(CONTRACT_SKILL))["Behavior"]
        combined = normalized(
            read(SUBMIT_PROTOCOL) + "\n" + read(REVIEW_PROTOCOL) + "\n" + read(LAND_PROTOCOL)
        )

        for expected in [
            "executable scenarios",
            "documentation-deliverable gates",
            "scenario or gate coverage",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, behavior_row)
                self.assertIn(expected, combined)

    def test_gate_form_close_artifact_delivery_uses_existing_schema_context(self) -> None:
        for path, expected_artifact in [
            (SUBMIT_PROTOCOL, "`change-proposal`"),
            (LAND_PROTOCOL, "`completion-record`"),
        ]:
            delivery = normalized(step(read(path), 5))
            with self.subTest(path=path.relative_to(ROOT)):
                for expected in [
                    "runtime-behavior work-unit",
                    "scenario-keyed",
                    expected_artifact,
                    "documentation-deliverable work-unit",
                    "gate-form",
                    "committed evidence",
                    "existing",
                ]:
                    self.assertIn(expected, delivery)
                self.assertNotIn("#454", delivery)
                self.assertNotIn("deferred", delivery)

        review_disposition = normalized(step(read(REVIEW_PROTOCOL), 4))
        for expected in [
            "runtime-behavior work-unit",
            "scenario-keyed",
            "documentation-deliverable work-unit",
            "gate-form",
            "committed evidence",
            "existing",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, review_disposition)
        self.assertNotIn("#454", review_disposition)
        self.assertNotIn("deferred", review_disposition)

    def test_dimension_omission_corruption_modes_and_invariants_survive(self) -> None:
        corruption_modes = normalized(
            section(read(SUBMIT_PROTOCOL), "Corruption Modes")
            + "\n"
            + section(read(REVIEW_PROTOCOL), "Corruption Modes")
            + "\n"
            + section(read(LAND_PROTOCOL), "Corruption Modes")
        )
        combined = normalized(read(SUBMIT_PROTOCOL) + "\n" + read(REVIEW_PROTOCOL) + "\n" + read(LAND_PROTOCOL))

        for expected in [
            "summary-drift",
            "rubber-stamp-review",
            "declared dimension",
            "behavior-only",
            "documentation or code-quality",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, corruption_modes)

        for expected in [
            "new valid `change-proposal` whose `version` advances",
            "exactly one typed outcome artifact",
            "independence from the author",
            "change-approved",
            "whose `version` equals `change-approved.against_version`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, combined)


if __name__ == "__main__":
    unittest.main()
