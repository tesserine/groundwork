"""Conformance gate: protocol artifact prose agrees with the owning schema.

Every field a ``PROTOCOL.md`` attributes to an artifact must exist in that
artifact type's schema. The gate consults the live schema files — it holds
no field list of its own, so a schema rename flips the result without this
module being edited.

Two prose surfaces carry field attributions, and the gate reads both:

- **Fenced delivery-call blocks** — ``artifact-type({ ... })`` inside a
  fenced code block. Every key the block names, at any nesting depth, must
  be a property name somewhere in the named type's schema, modulo the
  documented tool-parameter/injection envelope (``instance_id`` is a tool
  parameter extracted before body validation; ``work_unit`` is
  runtime-injected on scoped artifacts — both boundaries are stated in each
  producer's delivery paragraph and pinned by
  ``tests/test_protocol_artifact_delivery_docs.py``).
- **Backticked ``###`` headings** — the protocol-document convention for
  presenting an artifact field as a §-level subject (survey's
  §Requirements Structure is the form's home). Each such token must be a
  property of one of the protocol's produced artifact types. A protocol
  that produces nothing has no field vocabulary, so any backticked ``###``
  heading there is unattributable by construction.

Structural nesting, types, and required-ness stay the runtime validator's
job (runa validates delivered instances against the same schemas); this
gate closes exactly the prose class: a protocol describing a field no
schema grants.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path


ENVELOPE = frozenset({"instance_id", "work_unit"})

_CALL_OPEN = re.compile(r"^(?P<name>[a-z][a-z0-9-]*)\(\{\s*$")
_BLOCK_KEY = re.compile(r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_-]*)\s*:")
_FIELD_HEADING = re.compile(r"^###\s+`(?P<token>[^`]+)`\s*$")
_FENCE = re.compile(r"^\s*```")

_SUBSCHEMA_LIST_KEYS = ("oneOf", "anyOf", "allOf", "prefixItems")
_SUBSCHEMA_DICT_KEYS = (
    "items",
    "additionalProperties",
    "propertyNames",
    "if",
    "then",
    "else",
    "not",
    "contains",
)


@dataclass(frozen=True)
class Violation:
    """One field attributed in prose that the owning schema rejects."""

    protocol: str
    path: Path
    lineno: int
    surface: str  # "delivery-block" | "field-heading"
    artifact: str
    token: str
    schema_path: Path

    def render(self) -> str:
        return (
            f"{self.path}:{self.lineno}: protocol `{self.protocol}` "
            f"{self.surface} names `{self.token}` on artifact "
            f"`{self.artifact}`, but {self.schema_path} grants no such "
            f"property"
        )


@dataclass
class Report:
    """What the gate read and what it found."""

    protocols: list[str]
    violations: list[Violation]
    delivery_blocks: dict[str, int] = field(default_factory=dict)
    headings: dict[str, int] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.violations


def schema_property_names(schema: object) -> set[str]:
    """Every property name granted anywhere in a schema document.

    Collected by walking the schema itself — ``properties`` maps,
    ``patternProperties`` values, ``$defs``, combinators, and array item
    schemas — so the vocabulary is the schema's, never this module's.
    """

    names: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            props = node.get("properties")
            if isinstance(props, dict):
                for key, sub in props.items():
                    names.add(key)
                    walk(sub)
            for map_key in ("$defs", "definitions", "patternProperties"):
                mapping = node.get(map_key)
                if isinstance(mapping, dict):
                    for sub in mapping.values():
                        walk(sub)
            for list_key in _SUBSCHEMA_LIST_KEYS:
                subs = node.get(list_key)
                if isinstance(subs, list):
                    for sub in subs:
                        walk(sub)
            for dict_key in _SUBSCHEMA_DICT_KEYS:
                sub = node.get(dict_key)
                if isinstance(sub, dict):
                    walk(sub)
        elif isinstance(node, list):
            for sub in node:
                walk(sub)

    walk(schema)
    return names


def _manifest_protocols(manifest_path: Path) -> list[dict]:
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    return list(manifest.get("protocols", []))


def _manifest_artifact_types(manifest_path: Path) -> set[str]:
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    return {entry["name"] for entry in manifest.get("artifact_types", [])}


def _delivery_block_keys(
    lines: list[str], start: int
) -> tuple[list[tuple[int, str]], int]:
    """Keys named inside one call block, from its opening line.

    Returns ``(keys, next_index)`` where ``keys`` pairs each key with its
    line number and ``next_index`` is the first line after the block.
    Depth is tracked over braces and brackets so nested keys are read at
    every level; the block ends when depth returns to zero or the fence
    closes.
    """

    keys: list[tuple[int, str]] = []
    depth = lines[start].count("{") + lines[start].count("[")
    depth -= lines[start].count("}") + lines[start].count("]")
    index = start + 1
    while index < len(lines) and depth > 0:
        line = lines[index]
        if _FENCE.match(line):
            break
        match = _BLOCK_KEY.match(line)
        if match:
            keys.append((index + 1, match.group("key")))
        depth += line.count("{") + line.count("[")
        depth -= line.count("}") + line.count("]")
        index += 1
    return keys, index


def check_tree(root: Path | str, schemas_dir: Path | str | None = None) -> Report:
    """Run the gate over a groundwork tree.

    ``root`` must hold ``manifest.toml`` and ``protocols/<name>/PROTOCOL.md``
    for each manifest protocol. ``schemas_dir`` defaults to
    ``root / "schemas"``; passing it lets a fixture tree consult the live
    schemas rather than keep a second editable copy.
    """

    root_path = Path(root).resolve()
    schemas_path = (
        Path(schemas_dir).resolve() if schemas_dir is not None else root_path / "schemas"
    )
    manifest_path = root_path / "manifest.toml"
    protocols = _manifest_protocols(manifest_path)
    artifact_types = _manifest_artifact_types(manifest_path)

    vocab_cache: dict[str, tuple[Path, set[str]]] = {}

    def vocabulary(artifact: str) -> tuple[Path, set[str]]:
        if artifact not in vocab_cache:
            schema_path = schemas_path / f"{artifact}.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            vocab_cache[artifact] = (schema_path, schema_property_names(schema))
        return vocab_cache[artifact]

    report = Report(
        protocols=[entry["name"] for entry in protocols], violations=[]
    )

    for entry in protocols:
        name = entry["name"]
        produces = list(entry.get("produces", []))
        doc_path = root_path / "protocols" / name / "PROTOCOL.md"
        lines = doc_path.read_text(encoding="utf-8").splitlines()
        report.delivery_blocks[name] = 0
        report.headings[name] = 0

        index = 0
        while index < len(lines):
            line = lines[index]

            call = _CALL_OPEN.match(line.strip())
            if call and call.group("name") in artifact_types:
                artifact = call.group("name")
                report.delivery_blocks[name] += 1
                keys, index = _delivery_block_keys(lines, index)
                schema_path, granted = vocabulary(artifact)
                for lineno, key in keys:
                    if key in granted or key in ENVELOPE:
                        continue
                    report.violations.append(
                        Violation(
                            protocol=name,
                            path=doc_path,
                            lineno=lineno,
                            surface="delivery-block",
                            artifact=artifact,
                            token=key,
                            schema_path=schema_path,
                        )
                    )
                continue

            heading = _FIELD_HEADING.match(line)
            if heading:
                token = heading.group("token")
                report.headings[name] += 1
                attributed = False
                nearest_schema: Path | None = None
                for artifact in produces:
                    schema_path, granted = vocabulary(artifact)
                    nearest_schema = schema_path
                    if token in granted or token in ENVELOPE:
                        attributed = True
                        break
                if not attributed:
                    report.violations.append(
                        Violation(
                            protocol=name,
                            path=doc_path,
                            lineno=index + 1,
                            surface="field-heading",
                            artifact=" | ".join(produces) or "(produces nothing)",
                            token=token,
                            schema_path=nearest_schema
                            or schemas_path / "(no produced type)",
                        )
                    )

            index += 1

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check every protocol's artifact prose against the owning "
            "artifact schemas."
        )
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=str(Path(__file__).resolve().parents[1]),
        help="Groundwork tree root (defaults to this repository).",
    )
    args = parser.parse_args(argv)

    report = check_tree(Path(args.root))
    for violation in report.violations:
        print(violation.render())
    if report.passed:
        checked = sum(report.delivery_blocks.values())
        print(
            f"protocol prose conforms to the owning schemas "
            f"({len(report.protocols)} protocols, {checked} delivery blocks)."
        )
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
