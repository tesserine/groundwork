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


def semantic_sentences(text: str) -> list[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", normalized(text))
        if sentence.strip()
    ]


def has_semantic_clause(text: str, *patterns: str) -> bool:
    return any(
        all(re.search(pattern, sentence, flags=re.IGNORECASE) for pattern in patterns)
        for sentence in semantic_sentences(text)
    )


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


def delivery_validation_text(body: str, artifact: str) -> str:
    block = delivery_call_block(body, artifact)
    block_end = body.index(block) + len(block)
    suffix = body[block_end:]
    end = len(suffix)
    heading = re.search(r"^(?:#{1,6} .+|\d+[.] \*\*.+)$", suffix, flags=re.MULTILINE)
    if heading is not None:
        end = heading.start()
    return suffix[:end]


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
    explanation_says_runa_injects_work_unit: bool
    explanation_says_agent_does_not_supply_work_unit: bool
    explanation_says_runa_does_not_inject_work_unit: bool
    validation_names_remaining_artifact_body: bool

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

    @property
    def explains_work_unit_injection_contract(self) -> bool:
        if self.scoped:
            return (
                self.explanation_says_runa_injects_work_unit
                and self.explanation_says_agent_does_not_supply_work_unit
            )
        return self.explanation_says_runa_does_not_inject_work_unit

    @property
    def explains_post_extraction_validation_scope(self) -> bool:
        return self.validation_names_remaining_artifact_body


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
        validation = delivery_validation_text(body, artifact)
        keys = block_keys(block)
        schema = artifact_schema(root, artifact)
        explanation_sentences = semantic_sentences(explanation)
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
                explanation_says_runa_injects_work_unit=has_semantic_clause(
                    explanation,
                    r"\bRuna\b",
                    r"\binjects?\b",
                    r"`?work_unit`?",
                    r"\bsession context\b",
                ),
                explanation_says_agent_does_not_supply_work_unit=has_semantic_clause(
                    explanation,
                    r"\bagent\b",
                    r"\bdoes not supply\b",
                    r"`?work_unit`?",
                ),
                explanation_says_runa_does_not_inject_work_unit=has_semantic_clause(
                    explanation,
                    r"\bRuna\b",
                    r"\bdoes not inject\b",
                    r"`?work_unit`?",
                ),
                validation_names_remaining_artifact_body=has_semantic_clause(
                    validation,
                    r"\bRuna\b",
                    r"\bvalidates?\b",
                    r"\bremaining\b",
                    r"\bartifact body\b",
                ),
            )
        )
    return boundaries


PROTOCOL_RUNTIME_WIRING_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        "interactive session surface handoff marker",
        r"groundwork-install:interactive-session-surface-handoff",
    ),
    ("runa go command", r"\bruna\s+go\b"),
    ("RUNA environment atom", r"\bRUNA_[A-Z0-9_]*\b"),
    ("runtime pending seam", r"\buntil the runtime\b"),
    ("separate runtime agent", r"\bspawns?\s+a\s+separate\s+agent\b"),
)


PUBLIC_DOCS_BYPASS_PATTERNS: tuple[tuple[str, str], ...] = (
    ("missing artifact store bypass", r"\bno artifact store\b"),
    ("human artifact handoff bypass", r"\bPresent that artifact body to the human\b"),
)


def managed_docs_markdown_files(root: Path) -> list[Path]:
    docs = root / "docs"
    if not docs.is_dir():
        return []
    return sorted(docs.rglob("*.md"))


def managed_public_document_paths(root: Path) -> list[Path]:
    scripts = root / "scripts"
    paths = [
        root / "README.md",
        *managed_docs_markdown_files(root),
    ]
    if scripts.is_dir():
        paths.extend(sorted(scripts.glob("*.md")))
        paths.append(scripts / "groundwork-install")

    documents: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        documents.append(path)
    return documents


def forbidden_pattern_hits(body: str, patterns: tuple[tuple[str, str], ...]) -> list[str]:
    return [
        name
        for name, pattern in patterns
        if re.search(pattern, body, flags=re.IGNORECASE)
    ]


def protocol_runtime_wiring_violations(body: str) -> list[str]:
    return forbidden_pattern_hits(body, PROTOCOL_RUNTIME_WIRING_PATTERNS)


def public_docs_interactive_adapter_bypass_violations(root: Path) -> dict[str, list[str]]:
    return {
        str(path.relative_to(root)): hits
        for path in managed_public_document_paths(root)
        if (hits := forbidden_pattern_hits(read(path), PUBLIC_DOCS_BYPASS_PATTERNS))
    }


@dataclass(frozen=True)
class EntrySurfaceCoherence:
    acquire_reads_ticket_comments: bool
    acquire_surfaces_comments_as_entry_context: bool
    acquire_excludes_comments_from_artifact: bool
    take_grounds_frame_in_whole_ticket: bool
    take_uses_newest_review_directives: bool

    @property
    def passed(self) -> bool:
        return (
            self.acquire_reads_ticket_comments
            and self.acquire_surfaces_comments_as_entry_context
            and self.acquire_excludes_comments_from_artifact
            and self.take_grounds_frame_in_whole_ticket
            and self.take_uses_newest_review_directives
        )


def entry_surface_coherence(root: Path) -> EntrySurfaceCoherence:
    acquire = read(root / "skills" / "acquire" / "SKILL.md")
    take = read(root / "protocols" / "take" / "PROTOCOL.md")
    return EntrySurfaceCoherence(
        acquire_reads_ticket_comments=(
            "`comments`" in acquire
            and has_semantic_clause(
                acquire,
                r"\bread-ticket\b",
                r"`?comments`?",
                r"\blog\b",
            )
        ),
        acquire_surfaces_comments_as_entry_context=has_semantic_clause(
            acquire,
            r"\bSurface\b",
            r"\blog\b",
            r"\bentry context\b",
            r"\bwhole ticket\b",
        ),
        acquire_excludes_comments_from_artifact=has_semantic_clause(
            acquire,
            r"\bcomment log\b",
            r"\bentry context\b",
            r"\bnever persisted\b",
            r"\bartifact\b",
        ),
        take_grounds_frame_in_whole_ticket=(
            has_semantic_clause(take, r"\bGround\b", r"\bwhole ticket\b")
            and has_semantic_clause(
                take,
                r"\bcomment log\b",
                r"\brunning record\b",
            )
        ),
        take_uses_newest_review_directives=has_semantic_clause(
            take,
            r"\bnewest\b",
            r"\breview directives\b",
            r"\bsubmitted head\b",
            r"\bgovern\b",
        ),
    )


@dataclass(frozen=True)
class SessionSurfaceHandoffCommitments:
    has_single_marker_pair: bool
    commands_through_runa_session_surface: bool
    records_current_output_tool: bool
    validates_artifacts_by_runa: bool
    prohibits_direct_workspace_json: bool
    prohibits_separate_human_approval_gate: bool
    bypass_violations: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return (
            self.has_single_marker_pair
            and self.commands_through_runa_session_surface
            and self.records_current_output_tool
            and self.validates_artifacts_by_runa
            and self.prohibits_direct_workspace_json
            and self.prohibits_separate_human_approval_gate
            and not self.bypass_violations
        )


def session_surface_handoff_commitments(
    body: str,
    *,
    begin_marker: str,
    end_marker: str,
) -> SessionSurfaceHandoffCommitments:
    return SessionSurfaceHandoffCommitments(
        has_single_marker_pair=(
            body.count(begin_marker) == 1
            and body.count(end_marker) == 1
            and body.index(begin_marker) < body.index(end_marker)
        ),
        commands_through_runa_session_surface=(
            re.search(
                r"`runa go --work-unit\s+<canonical-work-unit-id>`",
                normalized(body),
            )
            is not None
            and "`next-protocol-context`" in body
            and "`advance`" in body
        ),
        records_current_output_tool=(
            "current output tool" in normalized(body)
            and has_semantic_clause(
                body,
                r"\brecords?\b",
                r"\bcurrent output tool\b",
            )
        ),
        validates_artifacts_by_runa=has_semantic_clause(
            body,
            r"\bArtifacts\b",
            r"\bvalidated by runa\b",
        ),
        prohibits_direct_workspace_json=has_semantic_clause(
            body,
            r"\bDo not\b",
            r"\bwrite\b",
            r"\bworkspace JSON files directly\b",
        ),
        prohibits_separate_human_approval_gate=has_semantic_clause(
            body,
            r"\bDo not\b",
            r"\bseparate human approval gate\b",
            r"\btyped disposition\b",
        ),
        bypass_violations=tuple(
            forbidden_pattern_hits(body, PUBLIC_DOCS_BYPASS_PATTERNS)
        ),
    )
