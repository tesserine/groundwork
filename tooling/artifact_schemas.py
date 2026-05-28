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
    return MechanicRegistry(
        forge_tags={
            entry["name"]
            for entry in manifest.get("forge_tags", [])
            if isinstance(entry, dict) and isinstance(entry.get("name"), str)
        }
    )


def load_artifact(
    artifact_type: str,
    path: Path | str,
    registry: MechanicRegistry | None = None,
) -> dict[str, Any]:
    artifact_path = Path(path)
    try:
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ArtifactSchemaError([("<json>", f"{artifact_path.name} is invalid JSON: {error}")]) from error

    validate_artifact(artifact_type, artifact, registry=registry)
    return artifact


def validate_artifact(
    artifact_type: str,
    artifact: dict[str, Any],
    registry: MechanicRegistry | None = None,
) -> None:
    errors: list[tuple[str, str]] = []
    errors.extend(_schema_errors(artifact_type, artifact))
    if registry is not None and not errors:
        errors.extend(_registry_errors(artifact_type, artifact, registry))

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


def _registry_errors(
    artifact_type: str,
    artifact: dict[str, Any],
    registry: MechanicRegistry,
) -> list[tuple[str, str]]:
    if artifact_type != "change-proposal":
        return []

    forge_tag = artifact["handle"]["forge_tag"]
    if forge_tag not in registry.forge_tags:
        return [("handle/forge_tag", f"forge tag `{forge_tag}` does not resolve in registry")]
    return []
