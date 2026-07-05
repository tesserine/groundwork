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
    sentences: list[str] = []
    paragraphs: list[str] = []
    current: list[str] = []

    def flush_current() -> None:
        paragraph = normalized(" ".join(current))
        if paragraph:
            paragraphs.append(paragraph)
        current.clear()

    for line in text.splitlines():
        if not line.strip():
            flush_current()
            continue

        list_item = re.match(r"^\s*(?:[-*+]|\d+[.)])\s+(?P<body>.*)$", line)
        if list_item is not None:
            flush_current()
            current.append(list_item.group("body"))
            continue

        current.append(line.strip())

    flush_current()

    for paragraph in paragraphs:
        for sentence in re.split(r"(?<=[.!?])\s+", paragraph):
            sentence = normalized(sentence)
            if sentence:
                sentences.append(sentence)
    return sentences


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
    acquire_reads_work_unit_comments: bool
    acquire_surfaces_comments_as_entry_context: bool
    acquire_excludes_comments_from_artifact: bool
    define_grounds_frame_in_whole_work_unit: bool
    define_uses_newest_review_directives: bool

    @property
    def passed(self) -> bool:
        return (
            self.acquire_reads_work_unit_comments
            and self.acquire_surfaces_comments_as_entry_context
            and self.acquire_excludes_comments_from_artifact
            and self.define_grounds_frame_in_whole_work_unit
            and self.define_uses_newest_review_directives
        )


def entry_surface_coherence(root: Path) -> EntrySurfaceCoherence:
    acquire = read(root / "skills" / "acquire" / "SKILL.md")
    define = read(root / "protocols" / "define" / "PROTOCOL.md")
    return EntrySurfaceCoherence(
        acquire_reads_work_unit_comments=(
            "`comments`" in acquire
            and has_semantic_clause(
                acquire,
                r"\bread-work-unit\b",
                r"`?comments`?",
                r"\blog\b",
            )
        ),
        acquire_surfaces_comments_as_entry_context=has_semantic_clause(
            acquire,
            r"\bSurface\b",
            r"\blog\b",
            r"\bentry context\b",
            r"\bwhole work-unit\b",
        ),
        acquire_excludes_comments_from_artifact=has_semantic_clause(
            acquire,
            r"\bcomment log\b",
            r"\bentry context\b",
            r"\bnever persisted\b",
            r"\bartifact\b",
        ),
        define_grounds_frame_in_whole_work_unit=(
            has_semantic_clause(define, r"\bGround\b", r"\bwhole work-unit\b")
            and has_semantic_clause(
                define,
                r"\bcomment log\b",
                r"\brunning record\b",
            )
        ),
        define_uses_newest_review_directives=has_semantic_clause(
            define,
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


# --- Freshen-on-acquire coherence (groundwork#465) ----------------------------
#
# These helpers gate the freshen-on-acquire built-in's methodology surface
# (skills/acquire/SKILL.md) against the authorities that own its invariants:
# the freshen-record schema (the disposition set, the required record elements,
# the six graph facets), and the manifest (the protocol whose trigger admits an
# acquired work-unit). No assertion enumerates forbidden prose; the surface's
# own renderings are checked against their schema/manifest homes, and positive
# coherence clauses are checked where the surface is the single home of its own
# rule.

FRESHEN_ACQUISITION_TRIGGER_ARTIFACT = "work-unit"


def freshen_record_disposition_set(root: Path) -> list[str]:
    schema = artifact_schema(root, "freshen-record")
    return list(schema_def(schema, "#/properties/disposition/enum"))


def freshen_record_graph_facets(root: Path) -> list[str]:
    schema = artifact_schema(root, "freshen-record")
    return list(schema_def(schema, "#/properties/graph_finding/required"))


def freshen_record_required_elements(root: Path) -> list[str]:
    schema = artifact_schema(root, "freshen-record")
    return [name for name in schema.get("required", []) if name != "work_unit"]


def acquisition_admitted_destination(root: Path) -> str | None:
    """The protocol that admits an acquired work-unit into the scoped pipeline:
    the one whose trigger fires on_artifact work-unit. Derived from the
    manifest, never hard-coded, so manifest drift that re-homes the trigger is
    caught by every gate built on this."""
    for protocol in manifest_protocols(root):
        trigger = protocol.get("trigger") or {}
        if (
            trigger.get("type") == "on_artifact"
            and trigger.get("name") == FRESHEN_ACQUISITION_TRIGGER_ARTIFACT
        ):
            name = protocol.get("name")
            return name if isinstance(name, str) else None
    return None


def _cell(value: str) -> str:
    return value.strip().strip("`").strip().lower()


def _column(rows: list[dict[str, str]], header_substring: str) -> list[str]:
    if not rows:
        return []
    header = next(
        (key for key in rows[0] if header_substring.lower() in key.lower()),
        None,
    )
    if header is None:
        return []
    return [row[header] for row in rows]


@dataclass(frozen=True)
class FreshenOnAcquireCoherence:
    freshen_step_present: bool
    freshen_precedes_delivery: bool
    disposition_set_matches_schema: bool
    only_proceed_admits_to_pipeline: bool
    record_contract_covers_required_elements: bool
    graph_finding_covers_schema_facets: bool
    withhold_conditioning_present: bool
    record_is_log_entry_not_body: bool
    composes_refine_work_unit: bool
    resolve_escalation_present: bool
    mode_parity_single_boundary: bool

    @property
    def passed(self) -> bool:
        return (
            self.freshen_step_present
            and self.freshen_precedes_delivery
            and self.disposition_set_matches_schema
            and self.only_proceed_admits_to_pipeline
            and self.record_contract_covers_required_elements
            and self.graph_finding_covers_schema_facets
            and self.withhold_conditioning_present
            and self.record_is_log_entry_not_body
            and self.composes_refine_work_unit
            and self.resolve_escalation_present
            and self.mode_parity_single_boundary
        )


def _step_title_index(steps: str, title_pattern: str) -> int | None:
    match = re.search(
        rf"^\d+\. \*\*[^*]*{title_pattern}[^*]*\*\*",
        steps,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    return match.start() if match else None


def freshen_on_acquire_coherence(root: Path) -> FreshenOnAcquireCoherence:
    acquire = read(root / "skills" / "acquire" / "SKILL.md")
    disposition_set = set(freshen_record_disposition_set(root))
    facets = freshen_record_graph_facets(root)
    required_elements = freshen_record_required_elements(root)
    destination = acquisition_admitted_destination(root)

    steps = markdown_section(acquire, "Steps")
    freshen_index = _step_title_index(steps, r"Freshen")
    deliver_index = _step_title_index(steps, r"Deliver")
    freshen_step_present = freshen_index is not None
    freshen_precedes_delivery = (
        freshen_index is not None
        and deliver_index is not None
        and freshen_index < deliver_index
    )

    try:
        freshening = markdown_section(acquire, "Freshening")
        rows = markdown_table_rows(freshening)
    except AssertionError:
        rows = []

    disposition_cells = {_cell(value) for value in _column(rows, "disposition")}
    disposition_set_matches_schema = bool(rows) and disposition_cells == disposition_set

    only_proceed_admits = False
    if rows and destination is not None:
        admit_column = _column(rows, destination)
        disposition_column = _column(rows, "disposition")
        if admit_column and len(admit_column) == len(disposition_column):
            proceed_admits: list[bool] = []
            nonproceed_admits: list[bool] = []
            for disposition_value, admit_value in zip(disposition_column, admit_column):
                admits = _cell(admit_value) in {"yes", "y", "true"}
                if _cell(disposition_value) == "proceed-as-freshened":
                    proceed_admits.append(admits)
                else:
                    nonproceed_admits.append(admits)
            only_proceed_admits = (
                len(proceed_admits) == 1
                and all(proceed_admits)
                and not any(nonproceed_admits)
            )

    record_contract_covers_required_elements = all(
        f"`{element}`" in acquire for element in required_elements
    )
    graph_finding_covers_schema_facets = all(
        f"`{facet}`" in acquire for facet in facets
    )

    withhold_conditioning_present = has_semantic_clause(
        acquire,
        r"\bonly\b",
        r"\bproceed-as-freshened\b",
        r"\bdeliver",
    )
    record_is_log_entry_not_body = has_semantic_clause(
        acquire,
        r"\bfreshen record\b",
        r"\bcomment\b",
        r"\bnot\b",
        r"\bbody\b",
    )
    composes_refine_work_unit = has_semantic_clause(
        acquire,
        r"\brefine-work-unit\b",
        r"\bre-craft",
    )
    resolve_escalation_present = has_semantic_clause(
        acquire,
        r"\bresolve\b",
        r"\bsubstrate\b",
        r"\bescalat",
    )
    mode_parity_single_boundary = (
        has_semantic_clause(
            acquire,
            r"\bADR-0015\b",
            r"\bmode is a property of the session\b",
        )
        and len(re.findall(r"^\d+\. \*\*[^*]*Freshen[^*]*\*\*", steps, flags=re.MULTILINE))
        == 1
    )

    return FreshenOnAcquireCoherence(
        freshen_step_present=freshen_step_present,
        freshen_precedes_delivery=freshen_precedes_delivery,
        disposition_set_matches_schema=disposition_set_matches_schema,
        only_proceed_admits_to_pipeline=only_proceed_admits,
        record_contract_covers_required_elements=record_contract_covers_required_elements,
        graph_finding_covers_schema_facets=graph_finding_covers_schema_facets,
        withhold_conditioning_present=withhold_conditioning_present,
        record_is_log_entry_not_body=record_is_log_entry_not_body,
        composes_refine_work_unit=composes_refine_work_unit,
        resolve_escalation_present=resolve_escalation_present,
        mode_parity_single_boundary=mode_parity_single_boundary,
    )
