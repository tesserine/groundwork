from __future__ import annotations

import argparse
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from jsonschema.exceptions import SchemaError

from tooling.artifact_schemas import ArtifactSchemaError, load_artifact, registry_from_manifest
from tooling.forge_address import ForgeAddressContractError, assert_derived_schema_matches_authority
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
FORGE_TOUCHING_OPERATIONS = {
    "apply-approved-change",
    "claim-work-unit",
    "close-out",
    "create-ticket",
    "deliver-change-proposal",
    "read-ticket",
    "record-progress",
    "reflect-disposition",
}
FORGE_LEAKAGE_TOKEN_PATTERNS = {
    "gh": r"(?<![A-Za-z0-9_-])gh(?![A-Za-z0-9_-])",
    "github.com": r"github[.]com",
    "git.sr.ht": r"git[.]sr[.]ht",
    "todo.sr.ht": r"todo[.]sr[.]ht",
}


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
    manifest_path = _registry_manifest_for_unit(path)
    try:
        registry = workflow_registry_from_manifest(manifest_path, root=manifest_path.parent)
    except Exception as error:
        return _registry_load_failure_result(path, CATEGORY_WORKFLOW, error)

    try:
        load_workflow_contract(path, registry=registry)
    except WorkflowContractError as error:
        return ConformanceResult(path=path, category=CATEGORY_WORKFLOW, passed=False, errors=_exception_errors(error))
    return ConformanceResult(path=path, category=CATEGORY_WORKFLOW, passed=True, errors=[])


def _check_mechanic(path: Path) -> ConformanceResult:
    try:
        registry = registry_from_manifest(_registry_manifest_for_unit(path))
    except Exception as error:
        return _registry_load_failure_result(path, CATEGORY_MECHANIC, error)

    try:
        load_mechanic(path, registry=registry)
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


def _registry_manifest_for_unit(path: Path) -> Path:
    if path.name == "manifest.toml":
        return path

    for parent in (path.parent, *path.parents):
        manifest = parent / "manifest.toml"
        if manifest.exists():
            return manifest
    return ROOT / "manifest.toml"


def _check_schema_definition(path: Path) -> ConformanceResult:
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        if path.name == "forge-address.schema.json":
            assert_derived_schema_matches_authority(path)
    except json.JSONDecodeError as error:
        return ConformanceResult(path=path, category=CATEGORY_SCHEMA, passed=False, errors=[f"<json>: {error}"])
    except SchemaError as error:
        return ConformanceResult(path=path, category=CATEGORY_SCHEMA, passed=False, errors=[error.message])
    except ForgeAddressContractError as error:
        return ConformanceResult(path=path, category=CATEGORY_SCHEMA, passed=False, errors=[str(error)])
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

    errors = _manifest_errors(manifest, path.parent)
    return ConformanceResult(
        path=path,
        category=CATEGORY_MANIFEST,
        passed=not errors,
        errors=[f"{error_path}: {message}" for error_path, message in errors],
    )


def _manifest_errors(manifest: dict[str, Any], root: Path) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    artifact_type_entries = _manifest_table_entries(manifest, "artifact_types", "artifact type", errors)
    outcome_type_entries = _manifest_table_entries(manifest, "outcome_types", "outcome type", errors)
    protocol_entries = _manifest_table_entries(manifest, "protocols", "protocol", errors)
    mechanic_entries = _manifest_table_entries(manifest, "mechanics", "mechanic", errors)
    artifact_types = _named_manifest_entries(artifact_type_entries, "artifact_types", "artifact type", errors)
    outcome_types = _named_manifest_entries(outcome_type_entries, "outcome_types", "outcome type", errors)
    forge_tag_entries = _manifest_table_entries(manifest, "forge_tags", "forge tag", errors)
    forge_tags = _named_manifest_entries(forge_tag_entries, "forge_tags", "forge tag", errors)

    for outcome_index, outcome_type in outcome_type_entries:
        name = outcome_type.get("name")
        if not isinstance(name, str):
            continue
        if name not in artifact_types:
            errors.append(
                (
                    f"outcome_types/{outcome_index}/name",
                    f"outcome type `{name}` does not resolve in artifact_types",
                )
            )

    outcome_bearing_outputs: set[str] = set()
    for protocol_index, protocol in protocol_entries:
        choices = protocol.get("required_output_choices", [])
        if not isinstance(choices, list):
            if "required_output_choices" in protocol:
                errors.append(
                    (
                        f"protocols/{protocol_index}/required_output_choices",
                        "required output choices must be an array of tables",
                    )
                )
            continue

        if choices:
            for output_key in ("produces", "may_produce"):
                values = protocol.get(output_key, [])
                if not isinstance(values, list):
                    if output_key in protocol:
                        errors.append((f"protocols/{protocol_index}/{output_key}", f"{output_key} must be an array"))
                    continue
                for value_index, value in enumerate(values):
                    if not isinstance(value, str):
                        errors.append((f"protocols/{protocol_index}/{output_key}/{value_index}", f"{output_key} member must be a string"))
                        continue
                    outcome_bearing_outputs.add(value)

        for choice_index, choice in enumerate(choices):
            if not isinstance(choice, dict):
                errors.append(
                    (
                        f"protocols/{protocol_index}/required_output_choices/{choice_index}",
                        "required output choice must be a table",
                    )
                )
                continue

            choice_name = choice.get("name")
            if not isinstance(choice_name, str):
                errors.append(
                    (
                        f"protocols/{protocol_index}/required_output_choices/{choice_index}/name",
                        "required output choice must declare a string name",
                    )
                )

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

    for protocol_index, protocol in protocol_entries:
        trigger = protocol.get("trigger")
        if "trigger" in protocol and not isinstance(trigger, dict):
            errors.append((f"protocols/{protocol_index}/trigger", "trigger must be a table"))
            continue
        if trigger is not None:
            errors.extend(
                _manifest_trigger_errors(
                    trigger,
                    f"protocols/{protocol_index}/trigger",
                    outcome_types,
                    outcome_bearing_outputs,
                )
            )

    errors.extend(_manifest_mechanic_binding_errors(mechanic_entries, forge_tags, root))
    errors.extend(_manifest_forge_matrix_errors(mechanic_entries, forge_tags))
    errors.extend(_manifest_protocol_leakage_errors(protocol_entries, root))

    return errors


def _manifest_forge_matrix_errors(
    mechanic_entries: list[tuple[int, dict[str, Any]]],
    forge_tags: set[str],
) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    if not forge_tags:
        return errors
    mechanic_by_name = {
        mechanic.get("name"): (mechanic_index, mechanic)
        for mechanic_index, mechanic in mechanic_entries
        if isinstance(mechanic.get("name"), str)
    }
    for operation in sorted(FORGE_TOUCHING_OPERATIONS):
        if operation not in mechanic_by_name:
            errors.append(
                (
                    "mechanics",
                    f"forge-touching operation `{operation}` must be declared in mechanics",
                )
            )
            continue
        mechanic_index, mechanic = mechanic_by_name[operation]
        declared = mechanic.get("forge_tags")
        if not isinstance(declared, list) or set(declared) != forge_tags:
            errors.append(
                (
                    f"mechanics/{mechanic_index}/forge_tags",
                    f"forge-touching operation `{operation}` must declare forge_tags for every registered forge",
                )
            )
    return errors


def _manifest_protocol_leakage_errors(
    protocol_entries: list[tuple[int, dict[str, Any]]],
    root: Path,
) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for protocol_index, protocol in protocol_entries:
        name = protocol.get("name")
        if not isinstance(name, str):
            continue
        protocol_body = root / "protocols" / name / "PROTOCOL.md"
        if not protocol_body.exists():
            continue
        try:
            body = protocol_body.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            errors.append((f"protocols/{protocol_index}", f"cannot read protocol body for forge leakage scan: {error}"))
            continue
        for token, pattern in FORGE_LEAKAGE_TOKEN_PATTERNS.items():
            if re.search(pattern, body):
                errors.append(
                    (
                        f"protocols/{protocol_index}",
                        f"protocol `{name}` leaks forge-specific token `{token}`",
                    )
                )
    return errors


def _manifest_mechanic_binding_errors(
    mechanic_entries: list[tuple[int, dict[str, Any]]],
    forge_tags: set[str],
    root: Path,
) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    c3_bindings = _c3_mechanic_bindings(root / "mechanics")

    for mechanic_index, mechanic in mechanic_entries:
        name = mechanic.get("name")
        declared_forge_tags = mechanic.get("forge_tags")
        if declared_forge_tags is None:
            continue
        if not isinstance(declared_forge_tags, list):
            errors.append((f"mechanics/{mechanic_index}/forge_tags", "forge_tags must be an array"))
            continue

        for forge_tag_index, forge_tag in enumerate(declared_forge_tags):
            forge_tag_path = f"mechanics/{mechanic_index}/forge_tags/{forge_tag_index}"
            if not isinstance(forge_tag, str):
                errors.append((forge_tag_path, "forge_tags member must be a string"))
                continue
            if forge_tag not in forge_tags:
                errors.append((forge_tag_path, f"forge tag `{forge_tag}` does not resolve in forge_tags"))
                continue
            if not isinstance(name, str):
                continue

            match_count = c3_bindings.count((name, forge_tag))
            if match_count != 1:
                errors.append(
                    (
                        forge_tag_path,
                        f"mechanic binding `{name}` for forge tag `{forge_tag}` resolves to "
                        f"{match_count} C-3 mechanics; expected exactly 1",
                    )
                )

    return errors


def _c3_mechanic_bindings(directory: Path) -> list[tuple[str, str]]:
    if not directory.exists():
        return []

    bindings: list[tuple[str, str]] = []
    for path in directory.rglob("*.toml"):
        try:
            mechanic = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
            continue
        name = mechanic.get("name")
        forge_tag = mechanic.get("forge_tag")
        if isinstance(name, str) and isinstance(forge_tag, str):
            bindings.append((name, forge_tag))
    return bindings


def _named_manifest_entries(
    entries: list[tuple[int, dict[str, Any]]],
    key: str,
    entry_label: str,
    errors: list[tuple[str, str]],
) -> set[str]:
    names: set[str] = set()
    for entry_index, entry in entries:
        name = entry.get("name")
        if not isinstance(name, str):
            errors.append((f"{key}/{entry_index}/name", f"{entry_label} must declare a string name"))
            continue
        names.add(name)
    return names


def _manifest_table_entries(
    manifest: dict[str, Any],
    key: str,
    entry_label: str,
    errors: list[tuple[str, str]],
) -> list[tuple[int, dict[str, Any]]]:
    if key not in manifest:
        return []

    value = manifest[key]
    if not isinstance(value, list):
        errors.append((key, f"{key} must be an array of tables"))
        return []

    entries: list[tuple[int, dict[str, Any]]] = []
    for entry_index, entry in enumerate(value):
        if not isinstance(entry, dict):
            errors.append((f"{key}/{entry_index}", f"{entry_label} must be a table"))
            continue
        entries.append((entry_index, entry))
    return entries


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
        if trigger_name in outcome_bearing_outputs:
            errors.append((path, f"successor routes on disposition-agnostic output `{trigger_name}`"))
        return errors

    if trigger_type in {"all_of", "any_of"}:
        conditions = trigger.get("conditions", [])
        if not isinstance(conditions, list):
            if "conditions" in trigger:
                errors.append((f"{path}/conditions", "conditions must be an array of tables"))
            return errors
        for condition_index, condition in enumerate(conditions):
            if not isinstance(condition, dict):
                errors.append((f"{path}/conditions/{condition_index}", "condition must be a table"))
                continue
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


def _registry_load_failure_result(path: Path, category: str, error: Exception) -> ConformanceResult:
    return ConformanceResult(
        path=path,
        category=category,
        passed=False,
        errors=[_registry_load_error_message(error)],
    )


def _registry_load_error_message(error: Exception) -> str:
    if isinstance(error, tomllib.TOMLDecodeError):
        return f"manifest registry could not be loaded: invalid TOML: {error}"
    if isinstance(error, UnicodeDecodeError):
        return f"manifest registry could not be loaded: cannot decode local registry input: {error}"
    if isinstance(error, OSError):
        return f"manifest registry could not be loaded: cannot read local registry input: {error}"
    return f"manifest registry could not be loaded: malformed manifest registry shape: {error}"


if __name__ == "__main__":
    raise SystemExit(main())
