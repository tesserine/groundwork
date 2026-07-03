import json
import re
import tempfile
import unittest
from pathlib import Path

from tooling.artifact_schemas import (
    ArtifactSchemaError,
    detect_contract_evidence_defects,
    load_artifact,
    validate_artifact,
    validate_contract_evidence,
)
from tooling.import_direction import find_violations, main as import_direction_main

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"
EMBEDDED_CORPUS = ROOT / "principles" / "PRINCIPLES.md"

# The two judgment-shaped universals the projection exemplar attests. The
# embedded corpus is the resolved corpus of a bare checkout and the consulted
# authority here: the pin below resolves each name against the corpus file,
# so the exemplar consults the corpus rather than inventing a second rulebook.
EARNS_ITS_PLACE = "Keep it as simple as the need allows"
FAIL_LOUDLY = "Fail loudly, early, and exactly once"
PROJECTED_UNIVERSALS = {EARNS_ITS_PLACE, FAIL_LOUDLY}

# The canonical exemplar's code-quality acceptance criterion — a join key
# also consumed by tests/test_artifact_schemas.py as a warranted input.
CANONICAL_CQ_CRITERION = "Validation remains centralized"


def fixture(name: str) -> Path:
    return FIXTURES / name


def canonical_contract() -> dict:
    return load_artifact("contract", fixture("valid-contract.json"))


def canonical_evidence() -> dict:
    return load_artifact(
        "completion-evidence", fixture("valid-completion-evidence.json")
    )


def projection_contract() -> dict:
    return load_artifact(
        "contract", fixture("valid-contract-code-quality-projections.json")
    )


def projection_evidence() -> dict:
    return load_artifact(
        "completion-evidence",
        fixture("valid-completion-evidence-code-quality-projections.json"),
    )


def hollow_contract() -> dict:
    return load_artifact("contract", fixture("hollow-contract-code-quality.json"))


def hollow_evidence() -> dict:
    return load_artifact(
        "completion-evidence",
        fixture("hollow-completion-evidence-code-quality.json"),
    )


def code_quality_criteria(contract: dict) -> list[dict]:
    return [
        criterion
        for criterion in contract["criteria"]
        if criterion["dimension"] == "code-quality"
    ]


def embedded_corpus_titles() -> set[str]:
    corpus = EMBEDDED_CORPUS.read_text(encoding="utf-8")
    return set(re.findall(r"^\d+\. \*\*(.+?)\.\*\*", corpus, re.MULTILINE))


class ImportDirectionFitnessTests(unittest.TestCase):
    """The shipped reference fitness function: a structural layer edge is
    checked by a run, a seeded violation goes red, and groundwork's own
    layering answers to it."""

    def seeded_tree(self, root: Path) -> None:
        (root / "src").mkdir()
        (root / "src" / "__init__.py").write_text("", encoding="utf-8")
        (root / "src" / "service.py").write_text(
            "from tests.helpers import fake_clock\n", encoding="utf-8"
        )
        (root / "tests").mkdir()
        (root / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (root / "tests" / "helpers.py").write_text(
            "fake_clock = object()\n", encoding="utf-8"
        )

    def test_seeded_cross_layer_import_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seeded_tree(root)

            violations = find_violations(root, [("src", "tests")])

            self.assertEqual(1, len(violations))
            violation = violations[0]
            self.assertEqual(Path("src") / "service.py", violation.path)
            self.assertEqual("tests.helpers", violation.module)
            self.assertEqual("src", violation.layer)

    def test_clean_tree_reports_no_violations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seeded_tree(root)
            (root / "src" / "service.py").write_text(
                "from src import validation\n", encoding="utf-8"
            )
            (root / "src" / "validation.py").write_text("", encoding="utf-8")

            self.assertEqual([], find_violations(root, [("src", "tests")]))

    def test_cli_fails_a_violating_change_and_passes_a_clean_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.seeded_tree(root)

            self.assertEqual(
                1,
                import_direction_main(
                    ["--root", str(root), "--forbid", "src:tests"]
                ),
            )

            (root / "src" / "service.py").write_text("", encoding="utf-8")
            self.assertEqual(
                0,
                import_direction_main(
                    ["--root", str(root), "--forbid", "src:tests"]
                ),
            )

    def test_groundworks_own_layering_holds_under_the_checker(self) -> None:
        # Golden rule #16 with in-house teeth: the library layer imports
        # nothing from its test layer, verified by the same fitness function
        # the exemplar declares.
        self.assertEqual([], find_violations(ROOT, [("tooling", "tests")]))


class ProjectionExemplarTests(unittest.TestCase):
    """The projection exemplar inhabits both check kinds in the uniform
    surfaces: an executable structural projection evidenced by a run, and
    attested judgment projections evidenced by per-universal findings."""

    def test_exemplar_carries_one_executable_and_two_attested_projections(
        self,
    ) -> None:
        criteria = code_quality_criteria(projection_contract())

        self.assertEqual(
            {"executable": 1, "attested": 2},
            {
                kind: len(
                    [c for c in criteria if c["check_kind"] == kind]
                )
                for kind in ("executable", "attested")
            },
        )

    def test_attested_projections_consult_the_embedded_corpus(self) -> None:
        attested = [
            criterion
            for criterion in code_quality_criteria(projection_contract())
            if criterion["check_kind"] == "attested"
        ]

        titles = embedded_corpus_titles()
        self.assertEqual(
            PROJECTED_UNIVERSALS,
            {criterion["acceptance_criterion"] for criterion in attested},
        )
        for criterion in attested:
            with self.subTest(criterion=criterion["id"]):
                self.assertIn(criterion["acceptance_criterion"], titles)

    def test_executable_projection_is_evidenced_by_a_recorded_run(self) -> None:
        contract = projection_contract()
        evidence = projection_evidence()
        executable_ids = {
            criterion["id"]
            for criterion in code_quality_criteria(contract)
            if criterion["check_kind"] == "executable"
        }

        for result in evidence["results"]:
            if result["criterion_id"] not in executable_ids:
                continue
            with self.subTest(criterion=result["criterion_id"]):
                run = result["evidence"]["run"]
                self.assertIn("import_direction", run["command"])
                self.assertEqual("pass", run["result"])

    def test_projection_pair_passes_the_shared_gate_with_warranted_universals(
        self,
    ) -> None:
        evidence = projection_evidence()

        validate_contract_evidence(
            projection_contract(),
            evidence,
            warranted_dimensions={"code-quality"},
            warranted_acceptance_criteria={"code-quality": PROJECTED_UNIVERSALS},
        )

        attestations = [
            result["evidence"]["attestation"]
            for result in evidence["results"]
            if "attestation" in result["evidence"]
        ]
        self.assertEqual(2, len(attestations))
        for attestation in attestations:
            self.assertTrue(attestation["reviewer"])
            self.assertTrue(attestation["finding"])


class HollowCodeQualityTests(unittest.TestCase):
    """A hollow code-quality criterion fails the same shared mechanism that
    judges every dimension — never a code-quality-only detector."""

    def test_hollow_exemplar_is_schema_valid_but_hollow(self) -> None:
        contract = hollow_contract()

        validate_artifact("contract", contract)
        self.assertEqual(
            [],
            detect_contract_evidence_defects(contract, hollow_evidence()),
        )

    def test_hollow_code_quality_criterion_fails_the_same_warranted_check(
        self,
    ) -> None:
        defects = detect_contract_evidence_defects(
            hollow_contract(),
            hollow_evidence(),
            warranted_acceptance_criteria={"code-quality": {EARNS_ITS_PLACE}},
        )

        messages = {message for _path, message in defects}
        self.assertIn(
            f"dimension 'code-quality' does not declare"
            f" warranted criterion {EARNS_ITS_PLACE!r}",
            messages,
        )

        # Same detector, same message shape as the sibling dimension: a
        # warranted miss for documentation templates to the identical string
        # once dimension and criterion are substituted.
        sentinel = "A new user completes the primary task from the README alone"
        sibling = detect_contract_evidence_defects(
            hollow_contract(),
            hollow_evidence(),
            warranted_acceptance_criteria={"documentation": {sentinel}},
        )
        sibling_shape = {
            message.replace("documentation", "<dimension>").replace(
                sentinel, "<criterion>"
            )
            for _path, message in sibling
        }
        code_quality_shape = {
            message.replace("code-quality", "<dimension>").replace(
                EARNS_ITS_PLACE, "<criterion>"
            )
            for _path, message in defects
        }
        self.assertEqual(sibling_shape, code_quality_shape)


class ProjectionParityTests(unittest.TestCase):
    """Code-quality projections answer to the same coverage and
    evidence-shape checks as every dimension."""

    def test_declared_projection_left_unevidenced_is_flagged_identically(
        self,
    ) -> None:
        contract = projection_contract()
        dropped = code_quality_criteria(contract)[0]["id"]
        evidence = projection_evidence()
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

    def test_executable_projection_without_a_run_is_flagged(self) -> None:
        contract = projection_contract()
        evidence = projection_evidence()
        executable_ids = {
            criterion["id"]
            for criterion in code_quality_criteria(contract)
            if criterion["check_kind"] == "executable"
        }
        for result in evidence["results"]:
            if result["criterion_id"] in executable_ids:
                result["evidence"] = {
                    "summary": "An attestation cannot satisfy an executable projection.",
                    "attestation": {
                        "reviewer": "core",
                        "finding": "The layer edge looked absent.",
                    },
                }

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_contract_evidence(contract, evidence)
        self.assertTrue(
            any(
                "executable criterion requires run or artifact evidence" in message
                for _path, message in context.exception.errors
            )
        )


class CanonicalExemplarTests(unittest.TestCase):
    """The canonical exemplar's code-quality criterion is honestly
    executable and wired into the warranted mechanism."""

    def test_canonical_code_quality_criterion_declares_an_automated_check(
        self,
    ) -> None:
        criteria = code_quality_criteria(canonical_contract())

        self.assertEqual(1, len(criteria))
        criterion = criteria[0]
        self.assertEqual("executable", criterion["check_kind"])
        self.assertNotEqual("", criterion["check"])

    def test_canonical_code_quality_evidence_is_a_recorded_run(self) -> None:
        results = {
            result["criterion_id"]: result
            for result in canonical_evidence()["results"]
        }
        evidence = results["code-quality-single-validation-path"]["evidence"]

        self.assertIn("run", evidence)
        self.assertEqual("pass", evidence["run"]["result"])

    def test_canonical_pair_passes_the_shared_gate_with_its_criterion_warranted(
        self,
    ) -> None:
        validate_contract_evidence(
            canonical_contract(),
            canonical_evidence(),
            warranted_dimensions={"code-quality"},
            warranted_acceptance_criteria={
                "code-quality": {CANONICAL_CQ_CRITERION}
            },
        )


if __name__ == "__main__":
    unittest.main()
