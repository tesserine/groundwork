#!/usr/bin/env python3
"""Derive a work-unit artifact body from an existing connector ticket.

Input (stdin or path): the JSON a `read-ticket` connector operation emits —
``{"handle": {...}, "title": str, "body": str|null, "state": str}``.

Output (stdout, on success): ``{"instance_id": str, "artifact": {...}}`` where
``artifact`` is a work-unit body ready for the `work-unit` MCP tool — its
``handle`` is the ticket's opaque connector handle, carried through verbatim
(one-way derivation; the ticket is the planning home, the artifact its
execution-scoped snapshot).

Derivation is deterministic and never invents content. Where the ticket does
not map cleanly onto the required schema fields — no extractable acceptance
criteria, an empty body, or a ticket that is not open — the script exits
non-zero with a named work-unit-quality defect, routing the gap to
decompose's refinement discipline (fix the ticket at its planning home, then
re-acquire) rather than fabricating fields.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

# Ticket states that mean the ticket is not open for work. GitHub reports
# "open"/"closed"; SourceHut reports a status string whose closed terminal is
# "resolved". Compared case-insensitively so either forge's casing matches.
CLOSED_STATES = {"closed", "resolved"}

ACCEPTANCE_HEADING = re.compile(
    r"^\s{0,3}#{1,6}\s+acceptance\s+criteria\s*:?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
ANY_HEADING = re.compile(r"^\s{0,3}#{1,6}\s+\S", re.MULTILINE)
# A list item: bullet (-, *, +) or ordered (1.), optionally a [ ]/[x] checkbox.
LIST_ITEM = re.compile(
    r"^\s*(?:[-*+]|\d+\.)\s+(?:\[[ xX]\]\s+)?(?P<text>\S.*?)\s*$",
    re.MULTILINE,
)


class MaterializeError(Exception):
    """A work-unit-quality defect in the source ticket."""


def list_items(block: str) -> list[str]:
    return [match.group("text").strip() for match in LIST_ITEM.finditer(block)]


def extract_acceptance_criteria(body: str) -> list[str]:
    """Prefer items under an Acceptance Criteria heading; else any checklist."""
    heading = ACCEPTANCE_HEADING.search(body)
    if heading is not None:
        start = heading.end()
        nxt = ANY_HEADING.search(body, start)
        section = body[start : nxt.start() if nxt else len(body)]
        items = list_items(section)
        if items:
            return items
    # No usable heading section — fall back to markdown checkboxes anywhere.
    checkbox = re.compile(r"^\s*[-*+]\s+\[[ xX]\]\s+(?P<text>\S.*?)\s*$", re.MULTILINE)
    return [match.group("text").strip() for match in checkbox.finditer(body)]


def materialize(ticket: dict) -> dict:
    handle = ticket.get("handle")
    if (
        not isinstance(handle, dict)
        or set(handle) != {"id", "display"}
        or not isinstance(handle.get("id"), str)
        or not handle["id"]
        or not isinstance(handle.get("display"), str)
        or not handle["display"]
    ):
        raise MaterializeError(
            "ticket payload is missing a connector handle; read-ticket must emit "
            "handle.id and handle.display"
        )
    identity = handle["id"]

    title = ticket.get("title")
    if not isinstance(title, str) or not title.strip():
        raise MaterializeError(f"ticket {identity!r} has no title to derive the work-unit from")

    state = ticket.get("state")
    if isinstance(state, str) and state.strip().lower() in CLOSED_STATES:
        raise MaterializeError(
            f"ticket {identity!r} is {state!r}, not open; acquire materializes open "
            "tickets — reopen it or pick another"
        )

    body = ticket.get("body")
    if not isinstance(body, str) or not body.strip():
        raise MaterializeError(
            f"ticket {identity!r} has an empty body; it carries no description or "
            "acceptance criteria — route it to decompose's refine-work-unit "
            "discipline to fill the ticket, then re-acquire"
        )

    criteria = extract_acceptance_criteria(body)
    if not criteria:
        raise MaterializeError(
            f"ticket {identity!r} has no extractable acceptance criteria "
            "(no checklist items, no Acceptance Criteria section); route it to "
            "decompose's refine-work-unit discipline rather than inventing them"
        )

    artifact = {
        "title": title.strip(),
        "description": body.strip(),
        "acceptance_criteria": criteria,
        "handle": handle,
    }
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return {"instance_id": f"work-unit-{digest}", "artifact": artifact}


def load_ticket(path: str | None) -> dict:
    raw = sys.stdin.read() if path in (None, "-") else Path(path).read_text(encoding="utf-8")
    try:
        ticket = json.loads(raw)
    except json.JSONDecodeError as error:
        raise MaterializeError(f"read-ticket output is not valid JSON: {error}") from error
    if not isinstance(ticket, dict):
        raise MaterializeError("read-ticket output must be a JSON object")
    return ticket


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive a work-unit artifact body from an existing forge ticket."
    )
    parser.add_argument(
        "path", nargs="?", help="read-ticket output path, or '-'/omit for stdin"
    )
    args = parser.parse_args()

    try:
        result = materialize(load_ticket(args.path))
    except MaterializeError as error:
        print(f"work-unit-quality defect: {error}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
