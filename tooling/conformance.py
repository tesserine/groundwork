from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from tooling.artifact_schemas import ArtifactSchemaError, load_artifact, registry_from_manifest
from tooling.mechanics import MechanicError, load_mechanic
from tooling.workflow_contracts import WorkflowContractError, load_workflow_contract, workflow_registry_from_manifest


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"

CATEGORY_WORKFLOW = "C-2 workflow-contract"
CATEGORY_MECHANIC = "C-3 mechanic"
CATEGORY_ARTIFACT = "C-4 artifact-instance"
CATEGORY_SCHEMA = "C-4 schema-definition"
CATEGORY_UNKNOWN = "unknown"


@dataclass(frozen=True)
class ConformanceResult:
    path: Path
    category: str
    passed: bool
    errors: list[str]


def discover_units(root: Path | str = ROOT) -> list[Path]:
    root_path = Path(root).resolve()
    units: list[Path] = []

    for directory_name in ("workflow-contracts", "mechanics"):
        directory = root_path / directory_name
        if directory.exists():
            units.extend(sorted(directory.rglob("*.toml")))

    schemas = root_path / "schemas"
    if schemas.exists():
        units.extend(sorted(schemas.glob("*.schema.json")))

    return units


def run_conformance(paths: Iterable[Path | str] | None = None) -> list[ConformanceResult]:
    units = discover_units() if paths is None else _expand_paths(paths)
    return [_check_unit(path) for path in units]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Groundwork Step-1 conformance checks.")
    parser.add_argument("paths", nargs="*", help="Files or directories to check. Defaults to source-tree units.")
    args = parser.parse_args(argv)

    paths = args.paths if args.paths else None
    results = run_conformance(paths)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {result.category} {result.path}")
        for error in result.errors:
            print(f"  {error}")

    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    print(f"Summary: {passed} passed, {failed} failed")
    return 1 if failed else 0


def _expand_paths(paths: Iterable[Path | str]) -> list[Path]:
    units: list[Path] = []
    for path_like in paths:
        path = Path(path_like).resolve()
        if path.is_dir():
            units.extend(discover_units(path))
        else:
            units.append(path)
    return units


def _check_unit(path: Path) -> ConformanceResult:
    category = _classify(path)
    try:
        if category == CATEGORY_WORKFLOW:
            return _check_workflow_contract(path)
        if category == CATEGORY_MECHANIC:
            return _check_mechanic(path)
        if category == CATEGORY_SCHEMA:
            return _check_schema_definition(path)
        if category == CATEGORY_ARTIFACT:
            return _check_artifact_instance(path)
    except (OSError, UnicodeDecodeError) as error:
        return ConformanceResult(
            path=path,
            category=category,
            passed=False,
            errors=[f"cannot read conformance unit: {error}"],
        )
    return ConformanceResult(path=path, category=CATEGORY_UNKNOWN, passed=False, errors=["unsupported conformance unit"])


def _classify(path: Path) -> str:
    # C-2 and C-3 TOML units are directory-scoped in Step 1; TOML files outside
    # those directories intentionally remain unknown.
    if path.name.endswith(".schema.json"):
        return CATEGORY_SCHEMA
    if path.suffix == ".toml" and "workflow-contracts" in path.parts:
        return CATEGORY_WORKFLOW
    if path.suffix == ".toml" and "mechanics" in path.parts:
        return CATEGORY_MECHANIC
    if path.suffix == ".json" and _artifact_type_for_path(path) is not None:
        return CATEGORY_ARTIFACT
    return CATEGORY_UNKNOWN


def _check_workflow_contract(path: Path) -> ConformanceResult:
    try:
        load_workflow_contract(path, registry=workflow_registry_from_manifest())
    except WorkflowContractError as error:
        return ConformanceResult(path=path, category=CATEGORY_WORKFLOW, passed=False, errors=_exception_errors(error))
    return ConformanceResult(path=path, category=CATEGORY_WORKFLOW, passed=True, errors=[])


def _check_mechanic(path: Path) -> ConformanceResult:
    try:
        load_mechanic(path, registry=registry_from_manifest())
    except MechanicError as error:
        return ConformanceResult(path=path, category=CATEGORY_MECHANIC, passed=False, errors=_exception_errors(error))
    return ConformanceResult(path=path, category=CATEGORY_MECHANIC, passed=True, errors=[])


def _check_artifact_instance(path: Path) -> ConformanceResult:
    artifact_type = _artifact_type_for_path(path)
    if artifact_type is None:
        return ConformanceResult(
            path=path,
            category=CATEGORY_ARTIFACT,
            passed=False,
            errors=["artifact type could not be inferred from filename"],
        )

    try:
        load_artifact(artifact_type, path, registry=registry_from_manifest())
    except ArtifactSchemaError as error:
        return ConformanceResult(path=path, category=CATEGORY_ARTIFACT, passed=False, errors=_exception_errors(error))
    return ConformanceResult(path=path, category=CATEGORY_ARTIFACT, passed=True, errors=[])


def _check_schema_definition(path: Path) -> ConformanceResult:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except json.JSONDecodeError as error:
        return ConformanceResult(path=path, category=CATEGORY_SCHEMA, passed=False, errors=[f"<json>: {error}"])
    except SchemaError as error:
        return ConformanceResult(path=path, category=CATEGORY_SCHEMA, passed=False, errors=[error.message])
    return ConformanceResult(path=path, category=CATEGORY_SCHEMA, passed=True, errors=[])


def _artifact_type_for_path(path: Path) -> str | None:
    stem = path.name.removesuffix(".json")
    for prefix in ("valid-", "invalid-"):
        if stem.startswith(prefix):
            stem = stem.removeprefix(prefix)
            break

    artifact_types = sorted(
        (schema.name.removesuffix(".schema.json") for schema in SCHEMAS.glob("*.schema.json")),
        key=len,
        reverse=True,
    )
    for artifact_type in artifact_types:
        if stem == artifact_type or stem.startswith(f"{artifact_type}-"):
            return artifact_type
    return None


def _exception_errors(error: WorkflowContractError | MechanicError | ArtifactSchemaError) -> list[str]:
    return [f"{path}: {message}" for path, message in error.errors]


if __name__ == "__main__":
    raise SystemExit(main())
