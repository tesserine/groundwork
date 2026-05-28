from __future__ import annotations

import json
import tomllib
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tooling.mechanics import MechanicRegistry


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
MANIFEST = ROOT / "manifest.toml"


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

    validator = Draft202012Validator(schema)
    errors: list[tuple[str, str]] = []
    for error in sorted(validator.iter_errors(artifact), key=lambda item: list(item.path)):
        path = "/".join(str(part) for part in error.path)
        if error.validator == "required":
            missing = error.message.split("'")[1]
            path = f"{path}/{missing}" if path else missing
        errors.append((path or "<root>", error.message))
    return errors


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
