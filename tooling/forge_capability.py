from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FORGE_CAPABILITY_SCHEMA = ROOT / "schemas" / "forge-capability.schema.json"
HANDLE_REF = "#/$defs/handle"


def load_forge_capability_schema(path: Path | str = FORGE_CAPABILITY_SCHEMA) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def operation_names(schema: dict[str, Any] | None = None) -> set[str]:
    source = load_forge_capability_schema() if schema is None else schema
    names = source["$defs"]["operation-name"]["enum"]
    return {name for name in names if isinstance(name, str)}
