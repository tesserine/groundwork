import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUBMIT_PROTOCOL = ROOT / "protocols" / "submit" / "PROTOCOL.md"
REVIEW_PROTOCOL = ROOT / "protocols" / "review" / "PROTOCOL.md"
LAND_PROTOCOL = ROOT / "protocols" / "land" / "PROTOCOL.md"


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


class CloseProtocolContractDimensionTests(unittest.TestCase):
    def test_submit_packages_every_declared_dimension_from_the_uniform_surface(self) -> None:
        body = normalized(read(SUBMIT_PROTOCOL))
        prepare = normalized(step(read(SUBMIT_PROTOCOL), 3))

        for expected in [
            "multidimensional contract",
            "one result per contract criterion",
            "`completion-evidence.results[]`",
            "behavior, documentation, and code-quality dimensions alike",
            "`contract` skill",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

        for expected in [
            "per-criterion behavior coverage",
            "documentation outcomes",
            "code-quality findings",
            "`completion-evidence.results[]`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, prepare)

    def test_review_judges_every_declared_dimension_through_the_same_join(self) -> None:
        inspection = normalized(step(read(REVIEW_PROTOCOL), 2))

        for expected in [
            "every declared dimension",
            "`contract.criteria[]`",
            "`completion-evidence.results[]`",
            "`check_kind`",
            "run or artifact evidence",
            "reviewer attestations",
            "audience-outcome",
            "diff loci",
            "The same join judges every dimension",
            "`contract` skill",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, inspection)

    def test_land_records_every_dimension_from_the_uniform_evidence_surface(self) -> None:
        delivery = normalized(step(read(LAND_PROTOCOL), 5))

        for expected in [
            "`completion-evidence.results[]`",
            "criterion_summary",
            "every declared dimension",
            "behavior, documentation, and code quality alike",
            "documentation_status",
            "documentation dimension's recorded results",
            "code-quality dimension's recorded findings",
            "completion-record",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, delivery)

        self.assertNotIn("#454", delivery)
        self.assertNotIn("deferred", delivery)
        self.assertIn("Do not assert a field the completion-record schema does not define", delivery)

    def test_close_protocols_carry_no_privileged_dimension_form(self) -> None:
        for path in [SUBMIT_PROTOCOL, REVIEW_PROTOCOL, LAND_PROTOCOL]:
            body = normalized(read(path))
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn("behavior_form", body)
                self.assertNotIn("deliverable's behavior form", body)
                self.assertNotIn("scenario-keyed", body)
                self.assertNotRegex(body, r"gate-form (?:packaging|behavior|mappings|evidence)")
                self.assertIn("`completion-evidence.results[]`", body)

    def test_close_protocols_consult_contract_lifecycle_without_reencoding_it(self) -> None:
        dimension_row = re.compile(
            r"\| \*\*(?:Behavior|Documentation|Code quality)\*\* \|",
        )

        for path in [SUBMIT_PROTOCOL, REVIEW_PROTOCOL, LAND_PROTOCOL]:
            body = read(path)
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("`contract` skill", normalized(body))
                self.assertIn("`skills/contract/SKILL.md`", body)
                self.assertIn("lifecycle", body)
                self.assertIsNone(dimension_row.search(body))

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
