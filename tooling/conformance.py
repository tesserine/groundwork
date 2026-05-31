from __future__ import annotations

import argparse
import json
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

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
CATEGORY_MANIFEST = "C-5 manifest"
CATEGORY_UNKNOWN = "unknown"

DIRECT_UNIT_DIRECTORY_NAMES = {"workflow-contracts", "mechanics", "schemas"}


@dataclass(frozen=True)
class ConformanceResult:
    path: Path
    category: str
    passed: bool
    errors: list[str]


def discover_units(root: Path | str = ROOT) -> list[Path]:
    root_path = Path(root).resolve()
    units: list[Path] = []

    manifest = root_path / "manifest.toml"
    if manifest.exists():
        units.append(manifest)

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
            units.extend(_discover_directory_argument_units(path))
        else:
            units.append(path)
    return units


def _discover_directory_argument_units(path: Path) -> list[Path]:
    if path.name in DIRECT_UNIT_DIRECTORY_NAMES:
        return _discover_direct_unit_directory(path)
    if list(path.glob("*.schema.json")):
        return sorted(path.glob("*.schema.json"))
    return discover_units(path)


def _discover_direct_unit_directory(path: Path) -> list[Path]:
    if path.name == "schemas":
        return sorted(path.glob("*.schema.json"))
    return sorted(path.rglob("*.toml"))


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
        if category == CATEGORY_MANIFEST:
            return _check_manifest(path)
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
    if path.name == "manifest.toml":
        return CATEGORY_MANIFEST
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


def _check_manifest(path: Path) -> ConformanceResult:
    try:
        manifest = tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        return ConformanceResult(
            path=path,
            category=CATEGORY_MANIFEST,
            passed=False,
            errors=[f"<toml>: {path.name} is invalid TOML: {error}"],
        )

    errors = _manifest_errors(manifest)
    return ConformanceResult(
        path=path,
        category=CATEGORY_MANIFEST,
        passed=not errors,
        errors=[f"{error_path}: {message}" for error_path, message in errors],
    )


def _manifest_errors(manifest: dict[str, Any]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    artifact_types = _named_manifest_entries(manifest, "artifact_types")
    outcome_types = _named_manifest_entries(manifest, "outcome_types")

    for outcome_index, outcome_type in enumerate(_manifest_table_array(manifest, "outcome_types")):
        name = outcome_type.get("name") if isinstance(outcome_type, dict) else None
        if not isinstance(name, str):
            errors.append((f"outcome_types/{outcome_index}/name", "outcome type must declare a string name"))
            continue
        if name not in artifact_types:
            errors.append(
                (
                    f"outcome_types/{outcome_index}/name",
                    f"outcome type `{name}` does not resolve in artifact_types",
                )
            )

    outcome_bearing_outputs: set[str] = set()
    for protocol_index, protocol in enumerate(_manifest_table_array(manifest, "protocols")):
        if not isinstance(protocol, dict):
            continue

        choices = protocol.get("required_output_choices", [])
        if not isinstance(choices, list):
            continue

        if choices:
            for output_key in ("produces", "may_produce"):
                values = protocol.get(output_key, [])
                if isinstance(values, list):
                    outcome_bearing_outputs.update(value for value in values if isinstance(value, str))

        for choice_index, choice in enumerate(choices):
            if not isinstance(choice, dict):
                errors.append(
                    (
                        f"protocols/{protocol_index}/required_output_choices/{choice_index}",
                        "required output choice must be a table",
                    )
                )
                continue

            members = choice.get("members")
            if not isinstance(members, list):
                errors.append(
                    (
                        f"protocols/{protocol_index}/required_output_choices/{choice_index}/members",
                        "required output choice members must be an array",
                    )
                )
                continue
            if len(members) < 2:
                errors.append(
                    (
                        f"protocols/{protocol_index}/required_output_choices/{choice_index}/members",
                        "required output choice must list at least two members",
                    )
                )

            seen_members: set[str] = set()
            for member_index, member in enumerate(members):
                member_path = f"protocols/{protocol_index}/required_output_choices/{choice_index}/members/{member_index}"
                if not isinstance(member, str):
                    errors.append((member_path, "required output choice member must be a string"))
                    continue
                if member in seen_members:
                    errors.append((member_path, f"required output choice repeats member `{member}`"))
                seen_members.add(member)
                if member not in artifact_types:
                    errors.append((member_path, f"required output choice member `{member}` does not resolve in artifact_types"))
                if member not in outcome_types:
                    errors.append((member_path, f"required output choice member `{member}` is not registered in outcome_types"))

    for protocol_index, protocol in enumerate(_manifest_table_array(manifest, "protocols")):
        if not isinstance(protocol, dict):
            continue
        trigger = protocol.get("trigger")
        if isinstance(trigger, dict):
            errors.extend(
                _manifest_trigger_errors(
                    trigger,
                    f"protocols/{protocol_index}/trigger",
                    outcome_types,
                    outcome_bearing_outputs,
                )
            )

    return errors


def _named_manifest_entries(manifest: dict[str, Any], key: str) -> set[str]:
    return {
        entry["name"]
        for entry in _manifest_table_array(manifest, key)
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def _manifest_table_array(manifest: dict[str, Any], key: str) -> list[Any]:
    value = manifest.get(key, [])
    return value if isinstance(value, list) else []


def _manifest_trigger_errors(
    trigger: dict[str, Any],
    path: str,
    outcome_types: set[str],
    outcome_bearing_outputs: set[str],
) -> list[tuple[str, str]]:
    trigger_type = trigger.get("type")
    trigger_name = trigger.get("name")
    errors: list[tuple[str, str]] = []

    if trigger_type in {"on_artifact", "on_change", "on_invalid"} and isinstance(trigger_name, str):
        if trigger_name in outcome_types and trigger_type != "on_artifact":
            errors.append((path, f"outcome trigger must use on_artifact for `{trigger_name}`"))
        if trigger_type == "on_artifact" and trigger_name in outcome_bearing_outputs:
            errors.append((path, f"successor routes on disposition-agnostic output `{trigger_name}`"))
        return errors

    if trigger_type in {"all_of", "any_of"}:
        conditions = trigger.get("conditions", [])
        if not isinstance(conditions, list):
            return errors
        for condition_index, condition in enumerate(conditions):
            if isinstance(condition, dict):
                errors.extend(
                    _manifest_trigger_errors(
                        condition,
                        f"{path}/conditions/{condition_index}",
                        outcome_types,
                        outcome_bearing_outputs,
                    )
                )

    return errors


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
