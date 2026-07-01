import json
import unittest
from pathlib import Path

from tooling.artifact_schemas import (
    ArtifactSchemaError,
    detect_contract_evidence_defects,
    detect_contract_traceability_defects,
    load_artifact,
    validate_artifact,
    validate_contract_evidence,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"
SCHEMAS = ROOT / "schemas"
DIMENSIONS = ["behavior", "documentation", "code-quality"]


def fixture(name: str) -> Path:
    return FIXTURES / name


def contract() -> dict:
    return load_artifact("contract", fixture("valid-contract.json"))


def completion_evidence() -> dict:
    return load_artifact("completion-evidence", fixture("valid-completion-evidence.json"))


def implementation_plan() -> dict:
    return load_artifact("implementation-plan", fixture("valid-implementation-plan.json"))


def test_evidence() -> dict:
    return load_artifact("test-evidence", fixture("valid-test-evidence.json"))


def criterion_for_dimension(artifact: dict, dimension: str) -> dict:
    for criterion in artifact["criteria"]:
        if criterion["dimension"] == dimension:
            return criterion
    raise AssertionError(f"no criterion declares dimension {dimension!r}")


class ContractSurfaceSymmetryTests(unittest.TestCase):
    """Every dimension is defined in the same contract surface."""

    def test_every_dimension_declares_the_identical_criterion_structure(self) -> None:
        criteria = contract()["criteria"]
        self.assertEqual(DIMENSIONS, [criterion["dimension"] for criterion in criteria])

        field_sets = {frozenset(criterion) for criterion in criteria}
        self.assertEqual(1, len(field_sets), "criterion structure varies by dimension")
        self.assertEqual(
            {
                "id",
                "dimension",
                "acceptance_criterion",
                "statement",
                "hollow_delivery",
                "check_kind",
                "check",
            },
            set(next(iter(field_sets))),
        )

    def test_downstream_schemas_key_off_contract_criteria_without_dimension_forms(self) -> None:
        for schema_name in ["implementation-plan.schema.json", "test-evidence.schema.json"]:
            with self.subTest(schema=schema_name):
                text = (SCHEMAS / schema_name).read_text(encoding="utf-8")
                schema = json.loads(text)

                self.assertIn("criterion_id", text)
                self.assertNotIn("behavior_form", text)
                self.assertNotIn("scenario-mapping", text)
                self.assertNotIn("gate-mapping", text)
                for keyword in ["if", "then", "else", "oneOf", "anyOf", "allOf", "$ref", "$defs"]:
                    self.assertNotIn(keyword, schema)


class CrossStageTraceabilitySymmetryTests(unittest.TestCase):
    """Plan and per-cycle evidence trace to contract criteria by criterion_id,
    and an unknown criterion is rejected by the same check for every dimension."""

    def test_plan_mapping_and_cycle_evidence_join_the_contract_for_every_dimension(self) -> None:
        declared = {criterion["id"] for criterion in contract()["criteria"]}

        plan_ids = {entry["criterion_id"] for entry in implementation_plan()["criterion_mapping"]}
        evidence_ids = {entry["criterion_id"] for entry in test_evidence()["evidence"]}

        self.assertEqual(declared, plan_ids)
        self.assertTrue(evidence_ids <= declared)
        self.assertEqual(
            [],
            detect_contract_traceability_defects(contract(), "implementation-plan", implementation_plan()),
        )
        self.assertEqual(
            [],
            detect_contract_traceability_defects(contract(), "test-evidence", test_evidence()),
        )

    def test_unknown_criterion_is_rejected_identically_for_every_dimension(self) -> None:
        for dimension in DIMENSIONS:
            declared = criterion_for_dimension(contract(), dimension)["id"]
            for artifact_type, artifact, key in [
                ("implementation-plan", implementation_plan(), "criterion_mapping"),
                ("test-evidence", test_evidence(), "evidence"),
            ]:
                with self.subTest(dimension=dimension, artifact_type=artifact_type):
                    mutated = json.loads(json.dumps(artifact))
                    entries = [
                        entry for entry in mutated[key] if entry["criterion_id"] == declared
                    ]
                    if not entries:
                        continue
                    entries[0]["criterion_id"] = f"unknown-{dimension}-criterion"

                    with self.assertRaises(ArtifactSchemaError) as context:
                        validate_artifact(
                            artifact_type,
                            mutated,
                            related_artifacts={"contract": contract()},
                        )
                    self.assertTrue(
                        any("unknown contract criterion" in message for _path, message in context.exception.errors)
                    )

    def test_plan_records_one_mapping_per_contract_criterion(self) -> None:
        duplicated = json.loads(json.dumps(implementation_plan()))
        duplicated["criterion_mapping"].append(duplicated["criterion_mapping"][0])

        with self.assertRaises(ArtifactSchemaError) as context:
            validate_artifact("implementation-plan", duplicated)
        self.assertTrue(any("duplicate" in message for _path, message in context.exception.errors))

        uncovered = json.loads(json.dumps(implementation_plan()))
        uncovered["criterion_mapping"] = uncovered["criterion_mapping"][:-1]
        defects = detect_contract_traceability_defects(contract(), "implementation-plan", uncovered)
        self.assertTrue(any("has no plan mapping" in message for _path, message in defects))


class EvidenceCoverageSymmetryTests(unittest.TestCase):
    """A delivery that leaves any declared dimension unevidenced fails the same
    check, behavior included."""

    def test_unevidenced_dimension_fails_the_same_check_for_every_dimension(self) -> None:
        failures = {}
        for dimension in DIMENSIONS:
            declared = criterion_for_dimension(contract(), dimension)["id"]
            evidence = completion_evidence()
            evidence["results"] = [
                result for result in evidence["results"] if result["criterion_id"] != declared
            ]

            with self.subTest(dimension=dimension):
                with self.assertRaises(ArtifactSchemaError) as context:
                    validate_contract_evidence(contract(), evidence)
                matching = [
                    (path, message)
                    for path, message in context.exception.errors
                    if declared in message
                ]
                self.assertTrue(matching)
                failures[dimension] = matching[0]

        paths = {path for path, _message in failures.values()}
        self.assertEqual({"results"}, paths, "dimensions fail through different checks")
        message_shapes = {
            message.replace(criterion_for_dimension(contract(), dimension)["id"], "<id>")
            for dimension, (_path, message) in failures.items()
        }
        self.assertEqual(1, len(message_shapes), "dimensions fail with different mechanisms")

    def test_seeded_delivery_underevidencing_non_behavior_dimensions_fails(self) -> None:
        evidence = completion_evidence()
        behavior_id = criterion_for_dimension(contract(), "behavior")["id"]
        evidence["results"] = [
            result for result in evidence["results"] if result["criterion_id"] == behavior_id
        ]

        defects = detect_contract_evidence_defects(contract(), evidence)
        messages = " ".join(message for _path, message in defects)
        for dimension in ["documentation", "code-quality"]:
            with self.subTest(dimension=dimension):
                self.assertIn(criterion_for_dimension(contract(), dimension)["id"], messages)

    def test_warranted_dimension_without_criteria_fails_symmetrically(self) -> None:
        for dimension in DIMENSIONS:
            with self.subTest(dimension=dimension):
                stripped = contract()
                stripped["criteria"] = [
                    criterion
                    for criterion in stripped["criteria"]
                    if criterion["dimension"] != dimension
                ]
                evidence = completion_evidence()
                dropped = criterion_for_dimension(contract(), dimension)["id"]
                evidence["results"] = [
                    result for result in evidence["results"] if result["criterion_id"] != dropped
                ]

                defects = detect_contract_evidence_defects(
                    stripped,
                    evidence,
                    warranted_dimensions=set(DIMENSIONS),
                )
                self.assertTrue(
                    any(
                        f"warranted dimension {dimension!r} has no contract criteria" == message
                        for _path, message in defects
                    )
                )


if __name__ == "__main__":
    unittest.main()
