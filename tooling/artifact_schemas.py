from __future__ import annotations

import json
import re
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from jsonschema import Draft202012Validator, FormatChecker

from tooling.mechanics import MechanicRegistry


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
MANIFEST = ROOT / "manifest.toml"
DATE_TIME_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$"
)


class ArtifactSchemaError(ValueError):
    def __init__(self, errors: list[tuple[str, str]]) -> None:
        self.errors = errors
        self.paths = [path for path, _message in errors]
        super().__init__(self._format())

    def _format(self) -> str:
        return "; ".join(f"{path}: {message}" for path, message in self.errors)


def registry_from_manifest(path: Path | str = MANIFEST) -> MechanicRegistry:
    manifest = tomllib.loads(Path(path).read_text(encoding="utf-8"))
    artifact_types = {
        entry["name"]
        for entry in manifest.get("artifact_types", [])
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    return MechanicRegistry(
        artifact_schemas=set(artifact_types),
        artifact_types=artifact_types,
    )


def load_artifact(
    artifact_type: str,
    path: Path | str,
    registry: MechanicRegistry | None = None,
    related_artifacts: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    artifact_path = Path(path)
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ArtifactSchemaError([("<json>", f"{artifact_path.name} is invalid JSON: {error}")]) from error

    validate_artifact(artifact_type, artifact, registry=registry, related_artifacts=related_artifacts)
    return artifact


def validate_artifact(
    artifact_type: str,
    artifact: dict[str, Any],
    registry: MechanicRegistry | None = None,
    related_artifacts: dict[str, dict[str, Any]] | None = None,
) -> None:
    errors: list[tuple[str, str]] = []
    errors.extend(_schema_errors(artifact_type, artifact))
    if not errors:
        errors.extend(_artifact_contract_errors(artifact_type, artifact))
    if not errors:
        errors.extend(_related_artifact_contract_errors(artifact_type, artifact, related_artifacts))
    if errors:
        raise ArtifactSchemaError(errors)


def _schema_errors(artifact_type: str, artifact: dict[str, Any]) -> list[tuple[str, str]]:
    schema_path = SCHEMAS / f"{artifact_type}.schema.json"
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ArtifactSchemaError([(str(schema_path.relative_to(ROOT)), "artifact schema does not exist")]) from error

    validator = Draft202012Validator(schema, format_checker=_format_checker())
    errors: list[tuple[str, str]] = []
    for error in sorted(validator.iter_errors(artifact), key=lambda item: list(item.path)):
        path = "/".join(str(part) for part in error.path)
        if error.validator == "required":
            missing = error.message.split("'")[1]
            path = f"{path}/{missing}" if path else missing
        errors.append((path or "<root>", error.message))
    return errors


def _format_checker() -> FormatChecker:
    checker = FormatChecker()

    if "date-time" not in checker.checkers:
        checker.checks("date-time")(_is_date_time)
    if "uri" not in checker.checkers:
        checker.checks("uri")(_is_uri)

    return checker


def _is_date_time(instance: object) -> bool:
    if not isinstance(instance, str):
        return True
    if not DATE_TIME_PATTERN.fullmatch(instance):
        return False

    timestamp = instance[:-1] + "+00:00" if instance[-1] in {"Z", "z"} else instance
    try:
        datetime.fromisoformat(timestamp)
    except ValueError:
        return False
    return True


def _is_uri(instance: object) -> bool:
    if not isinstance(instance, str):
        return True
    if any(character.isspace() for character in instance):
        return False

    parsed = urlparse(instance)
    if parsed.scheme in {"http", "https"} and not parsed.netloc:
        return False
    return bool(parsed.scheme and instance.split(":", 1)[1])


def _artifact_contract_errors(artifact_type: str, artifact: dict[str, Any]) -> list[tuple[str, str]]:
    if artifact_type == "contract":
        return _contract_artifact_errors(artifact)
    if artifact_type == "implementation-plan":
        return _implementation_plan_artifact_errors(artifact)
    if artifact_type == "completion-evidence":
        return _completion_evidence_artifact_errors(artifact)
    return []


def _related_artifact_contract_errors(
    artifact_type: str,
    artifact: dict[str, Any],
    related_artifacts: dict[str, dict[str, Any]] | None,
) -> list[tuple[str, str]]:
    if related_artifacts is None:
        return []

    contract = related_artifacts.get("contract")
    if contract is None:
        return []

    if artifact_type == "completion-evidence":
        return detect_contract_evidence_defects(contract, artifact)
    if artifact_type in {"implementation-plan", "test-evidence"}:
        return detect_contract_traceability_defects(contract, artifact_type, artifact)
    return []


def _contract_artifact_errors(artifact: dict[str, Any]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    seen: set[str] = set()
    for index, criterion in enumerate(artifact.get("criteria", [])):
        if not isinstance(criterion, dict):
            continue
        criterion_id = criterion.get("id")
        if isinstance(criterion_id, str):
            if criterion_id in seen:
                errors.append((f"criteria/{index}/id", f"duplicate criterion id {criterion_id!r}"))
            seen.add(criterion_id)
    return errors


def _implementation_plan_artifact_errors(artifact: dict[str, Any]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    seen: set[str] = set()
    for index, mapping in enumerate(artifact.get("criterion_mapping", [])):
        if not isinstance(mapping, dict):
            continue
        criterion_id = mapping.get("criterion_id")
        if isinstance(criterion_id, str):
            if criterion_id in seen:
                errors.append(
                    (
                        f"criterion_mapping/{index}/criterion_id",
                        f"duplicate criterion mapping {criterion_id!r}",
                    )
                )
            seen.add(criterion_id)
    return errors


def _completion_evidence_artifact_errors(artifact: dict[str, Any]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    seen: set[str] = set()
    for index, result in enumerate(artifact.get("results", [])):
        if not isinstance(result, dict):
            continue
        criterion_id = result.get("criterion_id")
        if isinstance(criterion_id, str):
            if criterion_id in seen:
                errors.append((f"results/{index}/criterion_id", f"duplicate criterion result {criterion_id!r}"))
            seen.add(criterion_id)
        evidence = result.get("evidence")
        if not isinstance(evidence, dict):
            continue
        run = evidence.get("run")
        if isinstance(run, dict) and run.get("result") != result.get("result"):
            errors.append((f"results/{index}/evidence/run/result", "run result must match criterion result"))
    return errors


def validate_contract_evidence(
    contract: dict[str, Any],
    completion_evidence: dict[str, Any],
    *,
    warranted_dimensions: set[str] | None = None,
    warranted_acceptance_criteria: dict[str, set[str]] | None = None,
) -> None:
    """Validate completion evidence against its contract artifact."""
    validate_artifact("contract", contract)
    validate_artifact("completion-evidence", completion_evidence, related_artifacts={"contract": contract})
    errors = detect_contract_evidence_defects(
        contract,
        completion_evidence,
        warranted_dimensions=warranted_dimensions,
        warranted_acceptance_criteria=warranted_acceptance_criteria,
    )
    if errors:
        raise ArtifactSchemaError(errors)


def detect_contract_traceability_defects(
    contract: dict[str, Any],
    artifact_type: str,
    artifact: dict[str, Any],
) -> list[tuple[str, str]]:
    """Return criterion-traceability defects joining a downstream artifact to its contract.

    The same mechanism serves every dimension: entries key off contract
    criteria by ``criterion_id``, an unknown criterion is rejected, and an
    implementation plan covers every contract criterion with a mapping.
    """
    entry_keys = {
        "implementation-plan": "criterion_mapping",
        "test-evidence": "evidence",
    }
    if artifact_type not in entry_keys:
        raise ValueError(f"no criterion traceability defined for artifact type {artifact_type!r}")
    entry_key = entry_keys[artifact_type]

    errors: list[tuple[str, str]] = []
    contract_work_unit = contract.get("work_unit")
    artifact_work_unit = artifact.get("work_unit")
    if (
        isinstance(contract_work_unit, str)
        and isinstance(artifact_work_unit, str)
        and contract_work_unit != artifact_work_unit
    ):
        errors.append(
            (
                "work_unit",
                f"{artifact_type} work_unit "
                f"{artifact_work_unit!r} does not match contract work_unit {contract_work_unit!r}",
            )
        )
        return errors

    declared_ids = {
        criterion["id"]
        for criterion in contract.get("criteria", [])
        if isinstance(criterion, dict) and isinstance(criterion.get("id"), str)
    }

    referenced_ids: set[str] = set()
    for index, entry in enumerate(artifact.get(entry_key, [])):
        if not isinstance(entry, dict):
            continue
        criterion_id = entry.get("criterion_id")
        if not isinstance(criterion_id, str):
            continue
        referenced_ids.add(criterion_id)
        if criterion_id not in declared_ids:
            errors.append(
                (
                    f"{entry_key}/{index}/criterion_id",
                    f"unknown contract criterion {criterion_id!r}",
                )
            )

    if artifact_type == "implementation-plan":
        for criterion_id in sorted(declared_ids - referenced_ids):
            errors.append(
                (entry_key, f"contract criterion {criterion_id!r} has no plan mapping")
            )

    return errors


def detect_contract_evidence_defects(
    contract: dict[str, Any],
    completion_evidence: dict[str, Any],
    *,
    warranted_dimensions: set[str] | None = None,
    warranted_acceptance_criteria: dict[str, set[str]] | None = None,
) -> list[tuple[str, str]]:
    """Return generic contract/evidence defects without dimension-specific logic."""
    errors: list[tuple[str, str]] = []
    contract_work_unit = contract.get("work_unit")
    evidence_work_unit = completion_evidence.get("work_unit")
    work_unit_mismatch = (
        isinstance(contract_work_unit, str)
        and isinstance(evidence_work_unit, str)
        and contract_work_unit != evidence_work_unit
    )
    if work_unit_mismatch:
        errors.append(
            (
                "work_unit",
                "completion evidence work_unit "
                f"{evidence_work_unit!r} does not match contract work_unit {contract_work_unit!r}",
            )
        )
    criteria = [
        criterion
        for criterion in contract.get("criteria", [])
        if isinstance(criterion, dict) and isinstance(criterion.get("id"), str)
    ]
    criteria_by_id = {criterion["id"]: criterion for criterion in criteria}
    criteria_by_dimension: dict[str, list[dict[str, Any]]] = {}
    for criterion in criteria:
        dimension = criterion.get("dimension")
        if isinstance(dimension, str):
            criteria_by_dimension.setdefault(dimension, []).append(criterion)

    for dimension in sorted(warranted_dimensions or set()):
        if dimension not in criteria_by_dimension:
            errors.append(("criteria", f"warranted dimension {dimension!r} has no contract criteria"))

    for dimension, warranted_criteria in sorted((warranted_acceptance_criteria or {}).items()):
        declared = {
            criterion.get("acceptance_criterion")
            for criterion in criteria_by_dimension.get(dimension, [])
            if isinstance(criterion.get("acceptance_criterion"), str)
        }
        for acceptance_criterion in sorted(warranted_criteria - declared):
            errors.append(
                (
                    "criteria",
                    f"dimension {dimension!r} does not declare warranted criterion {acceptance_criterion!r}",
                )
            )

    if work_unit_mismatch:
        return errors

    result_ids: set[str] = set()
    for index, result in enumerate(completion_evidence.get("results", [])):
        if not isinstance(result, dict):
            continue
        criterion_id = result.get("criterion_id")
        if not isinstance(criterion_id, str):
            continue
        result_ids.add(criterion_id)
        criterion = criteria_by_id.get(criterion_id)
        if criterion is None:
            errors.append((f"results/{index}/criterion_id", f"unknown contract criterion {criterion_id!r}"))
            continue
        evidence = result.get("evidence")
        if not isinstance(evidence, dict):
            continue
        check_kind = criterion.get("check_kind")
        has_executable_evidence = "run" in evidence or "artifact" in evidence
        has_attestation = "attestation" in evidence
        if check_kind == "executable" and not has_executable_evidence:
            errors.append((f"results/{index}/evidence", "executable criterion requires run or artifact evidence"))
        if check_kind == "attested" and not has_attestation:
            errors.append((f"results/{index}/evidence", "attested criterion requires reviewer attestation"))

    for criterion in criteria:
        criterion_id = criterion["id"]
        if criterion_id not in result_ids:
            errors.append(("results", f"contract criterion {criterion_id!r} has no completion evidence"))

    return errors
