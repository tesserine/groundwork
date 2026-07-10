import json
import unittest
from pathlib import Path

from tooling.artifact_schemas import (
    ArtifactSchemaError,
    detect_contract_evidence_defects,
    load_artifact,
    validate_artifact,
    validate_contract_evidence,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"

# The three recipient-pillar outcomes the pillar exemplar declares. The
# fixture is the exemplar home; these constants are pinned equal to it below
# and then reused as the warranted acceptance-criteria input, so the test
# consults the fixture rather than keeping a second editable copy.
USER_OUTCOME = "A new user completes the primary task from the README alone"
DEVELOPER_OUTCOME = (
    "A contributor locates where the change lives and integrates"
    " against its documented contract"
)
DISCOVERY_OUTCOME = (
    "A discovery reader tells what the project is, who it is for,"
    " and why to choose it from the entry surface"
)
PILLAR_OUTCOMES = {USER_OUTCOME, DEVELOPER_OUTCOME, DISCOVERY_OUTCOME}

# The canonical exemplar's documentation criterion is the user pillar for its
# own change: an API consumer acting from the reference alone.
CANONICAL_USER_OUTCOME = (
    "An API consumer submits a valid record and handles each"
    " validation failure from the reference alone"
)


def fixture(name: str) -> Path:
    return FIXTURES / name


def canonical_contract() -> dict:
    return load_artifact("contract", fixture("valid-contract.json"))


def canonical_evidence() -> dict:
    return load_artifact(
        "completion-evidence", fixture("valid-completion-evidence.json")
    )


def pillar_contract() -> dict:
    return load_artifact(
        "contract", fixture("valid-contract-documentation-pillars.json")
    )


def pillar_evidence() -> dict:
    return load_artifact(
        "completion-evidence",
        fixture("valid-completion-evidence-documentation-pillars.json"),
    )


def hollow_contract() -> dict:
    return load_artifact("contract", fixture("hollow-contract-documentation.json"))


def hollow_evidence() -> dict:
    return load_artifact(
        "completion-evidence",
        fixture("hollow-completion-evidence-documentation.json"),
    )


def documentation_criteria(contract: dict) -> list[dict]:
    return [
        criterion
        for criterion in contract["criteria"]
        if criterion["lens"] == "documentation"
    ]


class PillarExemplarTests(unittest.TestCase):
    """The three recipient pillars are behavior-kind criteria: a cold
    recipient's procedure reproduces each stated outcome."""

    def test_pillar_exemplar_declares_the_three_recipient_outcomes(self) -> None:
        criteria = documentation_criteria(pillar_contract())

        self.assertEqual(
            PILLAR_OUTCOMES,
            {criterion["acceptance_criterion"] for criterion in criteria},
        )
        for criterion in criteria:
            with self.subTest(criterion=criterion["id"]):
                self.assertEqual("documentation", criterion["lens"])
                self.assertEqual("behavior", criterion["kind"])
                self.assertIn("cold recipient", criterion["check"]["actor"])

    def test_rich_pillar_pair_passes_the_shared_gate_with_warranted_outcomes(
        self,
    ) -> None:
        contract = pillar_contract()
        evidence = pillar_evidence()

        validate_contract_evidence(
            contract,
            evidence,
            warranted_lenses={"documentation"},
            warranted_acceptance_criteria={"documentation": PILLAR_OUTCOMES},
        )

        for result in evidence["results"]:
            with self.subTest(criterion=result["criterion_id"]):
                attestation = result["evidence"]["attestation"]
                self.assertTrue(attestation["reviewer"])
                self.assertTrue(attestation["finding"])


class HollowDocumentationTests(unittest.TestCase):
    """A hollow documentation criterion fails the same shared mechanism that
    judges every lens — never a documentation-only detector."""

    def test_hollow_exemplar_is_schema_valid_but_hollow(self) -> None:
        contract = hollow_contract()

        validate_artifact("contract", contract)
        self.assertEqual(
            [],
            detect_contract_evidence_defects(contract, hollow_evidence()),
        )

    def test_hollow_documentation_criterion_fails_the_same_warranted_check(
        self,
    ) -> None:
        warranted = {USER_OUTCOME, DEVELOPER_OUTCOME}
        defects = detect_contract_evidence_defects(
            hollow_contract(),
            hollow_evidence(),
            warranted_acceptance_criteria={"documentation": warranted},
        )

        messages = {message for _path, message in defects}
        for outcome in sorted(warranted):
            with self.subTest(outcome=outcome):
                self.assertIn(
                    f"lens 'documentation' does not declare"
                    f" warranted criterion {outcome!r}",
                    messages,
                )

        # Same detector, same message shape as every other lens: a
        # warranted miss for code-quality on the canonical pair templates to
        # the identical string once lens and criterion are substituted.
        sentinel = "Public APIs stay typed"
        sibling = detect_contract_evidence_defects(
            canonical_contract(),
            canonical_evidence(),
            warranted_acceptance_criteria={"code-quality": {sentinel}},
        )
        sibling_shape = {
            message.replace("code-quality", "<lens>").replace(
                sentinel, "<criterion>"
            )
            for _path, message in sibling
        }
        documentation_shape = {
            message.replace("documentation", "<lens>").replace(
                outcome, "<criterion>"
            )
            for _path, message in defects
            for outcome in warranted
            if outcome in message
        }
        self.assertEqual(sibling_shape, documentation_shape)


class PillarParityTests(unittest.TestCase):
    """Documentation pillars answer to the same coverage check as every
    lens."""

    def test_declared_pillar_left_unevidenced_is_flagged_identically(self) -> None:
        contract = pillar_contract()
        dropped = documentation_criteria(contract)[0]["id"]
        evidence = pillar_evidence()
        evidence["results"] = [
            result
            for result in evidence["results"]
            if result["criterion_id"] != dropped
        ]

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_contract_evidence(contract, evidence)
        self.assertIn(
            ("results", f"contract criterion {dropped!r} has no completion evidence"),
            context.exception.errors,
        )


class CanonicalExemplarTests(unittest.TestCase):
    """The canonical exemplar's documentation criterion is an audience
    outcome wired into the warranted mechanism."""

    def test_canonical_documentation_lens_inhabits_both_kinds(self) -> None:
        criteria = documentation_criteria(canonical_contract())

        self.assertEqual(2, len(criteria))
        self.assertEqual(
            CANONICAL_USER_OUTCOME, criteria[0]["acceptance_criterion"]
        )
        self.assertEqual(
            {"behavior", "meaning"}, {criterion["kind"] for criterion in criteria}
        )

    def test_canonical_pair_passes_the_shared_gate_with_its_outcome_warranted(
        self,
    ) -> None:
        validate_contract_evidence(
            canonical_contract(),
            canonical_evidence(),
            warranted_lenses={"documentation"},
            warranted_acceptance_criteria={
                "documentation": {CANONICAL_USER_OUTCOME}
            },
        )


if __name__ == "__main__":
    unittest.main()
