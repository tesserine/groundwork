from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CAPABILITY_SCHEMA = ROOT / "schemas" / "forge-capability" / "v1" / "forge-capability.schema.json"
CAPABILITY_VERSION = "1.2.0"
CAPABILITY_PROVENANCE_URL = (
    "https://raw.githubusercontent.com/tesserine/commons/"
    "b229fb1a840c27ced31d582b40d766f4f441dcf6/"
    "schemas/forge-capability/v1/forge-capability.schema.json"
)


def load_schema(root: Path | str = ROOT) -> dict[str, Any]:
    path = Path(root) / "schemas" / "forge-capability" / "v1" / "forge-capability.schema.json"
    return json.loads(path.read_text(encoding="utf-8"))


def canonical_metadata(schema: dict[str, Any] | None = None) -> dict[str, str]:
    capability = load_schema() if schema is None else schema
    return capability.get("x-tesserine-canonical", {})


def handle_schema(schema: dict[str, Any] | None = None) -> dict[str, Any]:
    capability = load_schema() if schema is None else schema
    return copy.deepcopy(capability["$defs"]["handle"])


def operation_names(schema: dict[str, Any] | None = None) -> set[str]:
    capability = load_schema() if schema is None else schema
    return set(capability["$defs"]["operation-name"]["enum"])


def tool_definitions(schema: dict[str, Any] | None = None) -> dict[str, dict[str, str]]:
    capability = load_schema() if schema is None else schema
    tools: dict[str, dict[str, str]] = {}
    for operation in operation_names(capability):
        definition = capability["$defs"][f"{operation}-tool"]
        properties = definition["allOf"][1]["properties"]
        tools[operation] = {
            "name": properties["name"]["const"],
            "input_schema": properties["input_schema"]["const"],
            "output_schema": properties["output_schema"]["const"],
        }
    return tools
