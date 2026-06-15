from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from copy import deepcopy
from pathlib import Path
from typing import Any, Mapping

from jsonschema import Draft202012Validator


def _runtime_root() -> Path:
    candidate = Path(__file__).resolve().parents[1]
    if (candidate / "schemas").exists():
        return candidate
    installed = candidate.parent
    if (installed / "schemas").exists():
        return installed
    return candidate


ROOT = _runtime_root()
FORGE_ADDRESS_SCHEMA = ROOT / "schemas" / "forge-address.schema.json"
AUTHORITY_ENV = "RUNA_FORGE_CONTRACT_ROOT"


class ForgeAddressContractError(ValueError):
    pass


def load_schema(path: Path | str = FORGE_ADDRESS_SCHEMA) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_contract_value(value: Mapping[str, Any]) -> None:
    schema = load_schema()
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda item: list(item.path))
    if errors:
        details = "; ".join(f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}" for error in errors)
        raise ForgeAddressContractError(details)


def validate_work_unit_handle(handle: Mapping[str, Any]) -> None:
    schema = load_schema()
    handle_schema = {"$ref": "forge-address.schema.json#/$defs/work_unit_handle"}
    validator = Draft202012Validator(
        handle_schema,
        registry=_schema_registry(schema),
    )
    errors = sorted(validator.iter_errors(handle), key=lambda item: list(item.path))
    if errors:
        details = "; ".join(f"{'/'.join(str(part) for part in error.path) or '<root>'}: {error.message}" for error in errors)
        raise ForgeAddressContractError(details)

    tracker_identity = handle["tracker_identity"]
    number = handle["number"]
    expected = f"{tracker_identity}#{number}"
    if handle["work_unit_identity"] != expected:
        raise ForgeAddressContractError(f"work_unit_identity must be derived as {expected}")


def assert_derived_schema_matches_authority(schema_path: Path | str = FORGE_ADDRESS_SCHEMA) -> None:
    derived = load_schema(schema_path)
    canonical = derived.get("x-tesserine-canonical")
    if not isinstance(canonical, dict):
        raise ForgeAddressContractError("forge-address schema is missing x-tesserine-canonical provenance")
    commit = canonical.get("commit")
    schema_url = canonical.get("schema_url")
    if not isinstance(commit, str) or not _is_commit_sha(commit):
        raise ForgeAddressContractError("forge-address canonical commit must be an immutable commit SHA")
    if not isinstance(schema_url, str) or commit not in schema_url:
        raise ForgeAddressContractError("forge-address canonical schema_url must include the pinned commit SHA")

    authoritative = _load_authoritative_schema(canonical)
    if _comparable_schema(derived) != _comparable_schema(authoritative):
        raise ForgeAddressContractError(
            "derived forge-address schema diverges from the pinned runa authority"
        )


def _schema_registry(schema: dict[str, Any]):
    from referencing import Registry, Resource

    return Registry().with_resource("forge-address.schema.json", Resource.from_contents(schema))


def _load_authoritative_schema(canonical: Mapping[str, Any]) -> dict[str, Any]:
    contract_root = os.environ.get(AUTHORITY_ENV)
    if contract_root:
        path = Path(contract_root) / "contracts" / "forge-address" / "forge-address.schema.json"
        if not path.exists():
            raise ForgeAddressContractError(f"{AUTHORITY_ENV} does not contain {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    schema_url = canonical["schema_url"]
    try:
        with urllib.request.urlopen(schema_url, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise ForgeAddressContractError(
            f"cannot resolve pinned runa forge-address schema {schema_url}: {error}"
        ) from error


def _comparable_schema(schema: Mapping[str, Any]) -> dict[str, Any]:
    comparable = deepcopy(dict(schema))
    comparable.pop("$id", None)
    comparable.pop("$comment", None)
    comparable.pop("x-tesserine-canonical", None)
    return comparable


def _is_commit_sha(value: str) -> bool:
    return (
        len(value) == 40
        and value != "0" * 40
        and all(character in "0123456789abcdef" for character in value)
    )
