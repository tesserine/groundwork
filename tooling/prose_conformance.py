"""Shared conformance helpers for methodology prose gates.

The checks in this module read the substrate that owns a prose invariant:
``manifest.toml``, JSON Schemas, markdown structure, and small repository
control files. Tests should use these helpers instead of keeping local copies
of authority facts in phrase lists.
"""

from __future__ import annotations

import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

from tooling.protocol_prose import schema_property_names


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def manifest(root: Path) -> dict:
    return tomllib.loads(read(root / "manifest.toml"))


def manifest_protocols(root: Path) -> list[dict]:
    return list(manifest(root).get("protocols", []))


def artifact_schema(root: Path, artifact: str) -> dict:
    return json.loads(read(root / "schemas" / f"{artifact}.schema.json"))


def schema_def(schema: dict, ref: str) -> object:
    target: object = schema
    for part in ref.removeprefix("#/").split("/"):
        if not part:
            continue
        if not isinstance(target, dict):
            raise KeyError(ref)
        target = target[part]
    return target


def markdown_section(body: str, heading: str, level: int = 2) -> str:
    marks = "#" * level
    parent_or_sibling = rf"#{{1,{min(level, 6)}}}"
    pattern = re.compile(
        rf"^{marks} {re.escape(heading)}\n(?P<section>.*?)(?=^{parent_or_sibling} |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing section: {heading}")
    return match.group("section")


def numbered_step(body: str, number: int) -> str:
    pattern = re.compile(
        rf"^{number}\. \*\*.*?\n(?P<section>.*?)(?=^{number + 1}\. \*\*|^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing step {number}")
    return match.group("section")


def fenced_block_after(body: str, marker: str) -> str:
    pattern = re.compile(
        rf"{re.escape(marker)}.*?```(?:[A-Za-z0-9_-]+)?\n(?P<block>.*?)\n```",
        flags=re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing fenced block after: {marker}")
    return match.group("block")


def markdown_table_rows(section: str) -> list[dict[str, str]]:
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    if len(lines) < 3:
        raise AssertionError("missing markdown table")
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    rows: list[dict[str, str]] = []
    for line in lines[2:]:
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != len(header):
            raise AssertionError(f"malformed markdown table row: {line}")
        rows.append(dict(zip(header, cells)))
    return rows


def contract_dimension_rows(root: Path) -> dict[str, dict[str, str]]:
    skill = read(root / "skills" / "contract" / "SKILL.md")
    return {
        row["Dimension"]: row
        for row in markdown_table_rows(markdown_section(skill, "The dimensions"))
    }


def frontmatter(body: str) -> dict[str, object]:
    if not body.startswith("---\n"):
        raise AssertionError("missing frontmatter")
    raw = body.split("---\n", 2)[1]
    data: dict[str, object] = {}
    current_mapping: dict[str, str] | None = None
    for line in raw.splitlines():
        if not line.strip():
            continue
        if line.startswith("  ") and current_mapping is not None:
            if ":" not in line:
                continue
            key, value = line.strip().split(":", 1)
            current_mapping[key.strip()] = value.strip().strip('"')
            continue
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value:
            data[key] = value.strip('"')
            current_mapping = None
        else:
            current_mapping = {}
            data[key] = current_mapping
    return data


def delivery_call_block(body: str, artifact: str) -> str:
    pattern = re.compile(
        rf"```(?:[A-Za-z0-9_-]+)?\n(?P<block>\s*{re.escape(artifact)}\(\{{.*?\n\s*\}}\))\n\s*```",
        flags=re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing delivery call block for {artifact}")
    return match.group("block")


def delivery_explanation_text(body: str, artifact: str) -> str:
    block = delivery_call_block(body, artifact)
    block_index = body.index(block)
    prefix = body[:block_index]
    start = 0
    for match in re.finditer(
        r"^(?:#{1,6} .+|\d+[.] \*\*.+)$",
        prefix,
        flags=re.MULTILINE,
    ):
        start = match.start()
    return prefix[start:]


def block_keys(block: str) -> set[str]:
    return {
        match.group("key")
        for match in re.finditer(
            r"^\s*(?P<key>[A-Za-z_][A-Za-z0-9_-]*)\s*:",
            block,
            re.MULTILINE,
        )
    }


@dataclass(frozen=True)
class DeliveryBoundary:
    protocol: str
    artifact: str
    scoped: bool
    schema_requires_work_unit: bool
    call_has_instance_id: bool
    call_has_work_unit: bool
    instance_id_in_schema: bool
    explanation_names_instance_id: bool
    explanation_names_tool_input: bool
    explanation_distinguishes_artifact_body: bool

    @property
    def passed(self) -> bool:
        return (
            self.call_has_instance_id
            and not self.call_has_work_unit
            and not self.instance_id_in_schema
            and self.schema_requires_work_unit == self.scoped
        )

    @property
    def explains_mcp_tool_input_boundary(self) -> bool:
        return (
            self.explanation_names_instance_id
            and self.explanation_names_tool_input
            and self.explanation_distinguishes_artifact_body
        )


def delivery_boundaries(root: Path) -> list[DeliveryBoundary]:
    boundaries: list[DeliveryBoundary] = []
    for protocol in manifest_protocols(root):
        produces = list(protocol.get("produces", []))
        if not produces:
            continue
        artifact = produces[0]
        body = read(root / "protocols" / protocol["name"] / "PROTOCOL.md")
        block = delivery_call_block(body, artifact)
        explanation = delivery_explanation_text(body, artifact)
        keys = block_keys(block)
        schema = artifact_schema(root, artifact)
        explanation_sentences = re.split(
            r"(?<=[.!?])\s+|\n+",
            normalized(explanation),
        )
        boundaries.append(
            DeliveryBoundary(
                protocol=protocol["name"],
                artifact=artifact,
                scoped=protocol.get("scoped") is True,
                schema_requires_work_unit="work_unit" in schema.get("required", []),
                call_has_instance_id="instance_id" in keys,
                call_has_work_unit="work_unit" in keys,
                instance_id_in_schema="instance_id" in schema_property_names(schema),
                explanation_names_instance_id=any(
                    "instance_id" in sentence
                    for sentence in explanation_sentences
                ),
                explanation_names_tool_input=any(
                    "instance_id" in sentence
                    and re.search(r"\b(?:MCP|tool)\b", sentence, flags=re.IGNORECASE)
                    and re.search(
                        r"\b(?:input|parameter)\b",
                        sentence,
                        flags=re.IGNORECASE,
                    )
                    for sentence in explanation_sentences
                ),
                explanation_distinguishes_artifact_body=any(
                    "artifact body" in sentence
                    and re.search(
                        r"\b(?:not|must not|before validating|remaining)\b",
                        sentence,
                        flags=re.IGNORECASE,
                    )
                    for sentence in explanation_sentences
                ),
            )
        )
    return boundaries
