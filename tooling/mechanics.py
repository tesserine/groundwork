from __future__ import annotations

import json
import re
import subprocess
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
MECHANIC_SCHEMA = ROOT / "schemas" / "mechanic.schema.json"


class MechanicError(ValueError):
    def __init__(self, errors: list[tuple[str, str]]) -> None:
        self.errors = errors
        self.paths = [path for path, _message in errors]
        super().__init__(self._format())

    def _format(self) -> str:
        return "; ".join(f"{path}: {message}" for path, message in self.errors)


@dataclass(frozen=True)
class MechanicRegistry:
    artifact_schemas: set[str] = field(default_factory=set)
    artifact_types: set[str] = field(default_factory=set)


def load_mechanic(path: Path | str, registry: MechanicRegistry | None = None) -> dict[str, Any]:
    mechanic_path = Path(path)
    try:
        mechanic = tomllib.loads(mechanic_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise MechanicError([("<toml>", f"{mechanic_path.name} is invalid TOML: {error}")]) from error

    validate_mechanic(mechanic, registry=registry)
    return mechanic


def validate_mechanic(mechanic: dict[str, Any], registry: MechanicRegistry | None = None) -> None:
    errors: list[tuple[str, str]] = []
    errors.extend(_schema_errors(mechanic))
    if not errors:
        errors.extend(_invocation_errors(mechanic))
    if registry is not None and not errors:
        errors.extend(_registry_errors(mechanic, registry))

    if errors:
        raise MechanicError(errors)


def _schema_errors(mechanic: dict[str, Any]) -> list[tuple[str, str]]:
    schema = json.loads(MECHANIC_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors: list[tuple[str, str]] = []

    for error in sorted(validator.iter_errors(mechanic), key=lambda item: list(item.path)):
        path = "/".join(str(part) for part in error.path)
        if error.validator == "required":
            missing = error.message.split("'")[1]
            path = f"{path}/{missing}" if path else missing
        errors.append((path or "<root>", error.message))

    return errors


def _invocation_errors(mechanic: dict[str, Any]) -> list[tuple[str, str]]:
    body = mechanic["default_invocation"]
    errors: list[tuple[str, str]] = []

    if _shell_has_bare_placeholder(body):
        errors.append(("default_invocation", "bare placeholder references are not allowed; use shell environment references"))

    shell_check = subprocess.run(
        ["/bin/sh", "-n", "-c", body],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if shell_check.returncode != 0:
        errors.append(("default_invocation", f"default_invocation must parse as valid /bin/sh: {shell_check.stderr.strip()}"))

    for parameter_index, parameter in enumerate(mechanic["parameters"]):
        parameter_name = parameter["name"]
        if not _shell_expands_parameter(body, parameter_name):
            errors.append(
                (
                    f"parameters/{parameter_index}/name",
                    f"parameter `{parameter_name}` is not expanded by /bin/sh in default_invocation",
                )
            )

    return errors


def _shell_has_bare_placeholder(body: str) -> bool:
    in_single_quote = False
    in_double_quote = False
    escaped = False
    index = 0
    while index < len(body):
        char = body[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if char == "\\":
            escaped = True
            index += 1
            continue
        if char == "'" and not in_double_quote:
            in_single_quote = not in_single_quote
            index += 1
            continue
        if char == '"' and not in_single_quote:
            in_double_quote = not in_double_quote
            index += 1
            continue
        if not in_single_quote and not in_double_quote and char == "{":
            match = re.match(r"\{[A-Za-z_][A-Za-z0-9_.-]*\}", body[index:])
            previous = body[index - 1 : index]
            if match and (not previous or not re.match(r"[$A-Za-z0-9_^]", previous)):
                return True
        index += 1
    return False


def _shell_expands_parameter(body: str, parameter_name: str) -> bool:
    in_single_quote = False
    escaped = False
    index = 0
    while index < len(body):
        char = body[index]
        if escaped:
            escaped = False
            index += 1
            continue
        if char == "\\":
            escaped = True
            index += 1
            continue
        if char == "'":
            in_single_quote = not in_single_quote
            index += 1
            continue
        if not in_single_quote and char == "$":
            braced = f"${{{parameter_name}}}"
            unbraced = f"${parameter_name}"
            if body.startswith(braced, index):
                return True
            if body.startswith(unbraced, index):
                following = body[index + len(unbraced) : index + len(unbraced) + 1]
                if not following or not re.match(r"[A-Za-z0-9_]", following):
                    return True
        index += 1
    return False


def _registry_errors(mechanic: dict[str, Any], registry: MechanicRegistry) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for parameter_index, parameter in enumerate(mechanic["parameters"]):
        schema_ref = parameter.get("schema_ref")
        if schema_ref is not None and schema_ref not in registry.artifact_schemas:
            errors.append(
                (
                    f"parameters/{parameter_index}/schema_ref",
                    f"artifact schema `{schema_ref}` does not resolve in registry",
                )
            )

    artifact_type = mechanic["outcome"].get("artifact_type")
    if artifact_type is not None and artifact_type not in registry.artifact_types:
        errors.append(
            (
                "outcome/artifact_type",
                f"artifact type `{artifact_type}` does not resolve in registry",
            )
        )

    return errors
