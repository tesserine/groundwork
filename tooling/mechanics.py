from __future__ import annotations

import json
import re
import shlex
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
    forge_tags: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class ParameterizedInvocationContractGuard:
    invocation: str

    _bare_placeholder_pattern = re.compile(r"(?<![$^])\{(?P<name>[A-Za-z_][A-Za-z0-9_]*)\}")
    _name_start_pattern = re.compile(r"[A-Za-z_]")
    _name_pattern = re.compile(r"[A-Za-z0-9_]")

    def errors_for(self, parameters: list[dict[str, Any]]) -> list[tuple[str, str]]:
        errors = [
            (
                "default_invocation",
                f"bare brace placeholder `{{{match.group('name')}}}` uses textual substitution; "
                "reference declared parameters as $name or ${name}",
            )
            for word in self._placeholder_scan_words()
            for match in self._bare_placeholder_pattern.finditer(word)
        ]
        if errors:
            return errors

        for parameter_index, parameter in enumerate(parameters):
            name = parameter["name"]
            if not self.references_shell_parameter(name):
                errors.append(
                    (
                        f"parameters/{parameter_index}/name",
                        f"parameter `{name}` is not referenced as an expandable shell reference",
                    )
                )
        return errors

    def references_shell_parameter(self, name: str) -> bool:
        return name in self._expandable_shell_reference_names()

    def _expandable_shell_reference_names(self) -> set[str]:
        names: set[str] = set()
        quote: str | None = None
        index = 0

        while index < len(self.invocation):
            char = self.invocation[index]

            if quote == "'":
                if char == "'":
                    quote = None
                index += 1
                continue

            if char == "\\":
                if quote != '"' or self._double_quote_backslash_escapes(index):
                    index += 2
                else:
                    index += 1
                continue

            if char == "'":
                if quote is None:
                    quote = "'"
                index += 1
                continue

            if char == '"':
                quote = None if quote == '"' else '"'
                index += 1
                continue

            if char != "$":
                index += 1
                continue

            name, consumed = self._shell_parameter_name_at(index + 1)
            if name is not None:
                names.add(name)
            index += consumed + 1

        return names

    def _double_quote_backslash_escapes(self, index: int) -> bool:
        next_index = index + 1
        return next_index < len(self.invocation) and self.invocation[next_index] in {'$', "`", '"', "\\", "\n"}

    def _shell_parameter_name_at(self, index: int) -> tuple[str | None, int]:
        if index >= len(self.invocation):
            return None, 0

        if self.invocation[index] == "{":
            name_start = index + 1
            if name_start >= len(self.invocation) or self._name_start_pattern.fullmatch(self.invocation[name_start]) is None:
                return None, 1

            name_end = name_start + 1
            while name_end < len(self.invocation) and self._name_pattern.fullmatch(self.invocation[name_end]) is not None:
                name_end += 1
            return self.invocation[name_start:name_end], name_end - index

        if self._name_start_pattern.fullmatch(self.invocation[index]) is None:
            return None, 0

        name_end = index + 1
        while name_end < len(self.invocation) and self._name_pattern.fullmatch(self.invocation[name_end]) is not None:
            name_end += 1
        return self.invocation[index:name_end], name_end - index

    def _placeholder_scan_words(self) -> list[str]:
        words = shlex.split(self.invocation, posix=True)
        scanned: list[str] = []
        command: str | None = None
        skip_next_python_command_string = False

        for word in words:
            if skip_next_python_command_string:
                skip_next_python_command_string = False
                continue

            if word in {"&&", "||", "|", ";"}:
                command = None
                scanned.append(word)
                continue

            if command is None:
                command = Path(word).name
            elif command.startswith("python") and word == "-c":
                skip_next_python_command_string = True

            scanned.append(word)

        return scanned


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
    return ParameterizedInvocationContractGuard(mechanic["default_invocation"]).errors_for(mechanic["parameters"])


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

    forge_tag = mechanic.get("forge_tag")
    if forge_tag is not None and forge_tag not in registry.forge_tags:
        errors.append(("forge_tag", f"forge tag `{forge_tag}` does not resolve in registry"))

    return errors
