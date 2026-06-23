"""Acquisition: materializing a work-unit artifact from a connector ticket.

The forge read effect is supplied by the selected connector's `read-ticket`
MCP tool. This module tests Groundwork's side of the seam: it consumes the
connector ticket snapshot without parsing provider grammar from the handle.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

from tooling.artifact_schemas import registry_from_manifest, validate_artifact


ROOT = Path(__file__).resolve().parents[1]
MATERIALIZE = ROOT / "skills" / "acquire" / "scripts" / "materialize.py"

TICKET_BODY = (
    "Cold-start entry from a connector ticket snapshot.\n\n"
    "## Acceptance criteria\n\n"
    "- [ ] Given an existing ticket, an artifact is materialized\n"
    "- [ ] The artifact handle identifies that ticket\n"
)


def materialize(read_ticket_stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MATERIALIZE)],
        input=read_ticket_stdout,
        capture_output=True,
        text=True,
    )


class MaterializeTicketTests(unittest.TestCase):
    def test_connector_ticket_materializes_to_schema_valid_adopted_work_unit(self) -> None:
        snapshot = {
            "handle": {
                "id": "tenant-alpha:tracker-main:ticket-blue",
                "display": "GW-blue",
            },
            "title": "task(entry): cold-start scoped entry from a forge ticket",
            "body": TICKET_BODY,
            "state": "open",
        }

        result = materialize(json.dumps(snapshot))
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)

        validate_artifact("work-unit", payload["artifact"], registry=registry_from_manifest())
        self.assertEqual(snapshot["handle"], payload["artifact"]["handle"])
        self.assertRegex(
            payload["instance_id"],
            r"^work-unit-[0-9a-f]{12}-task-entry-cold-start-scoped-entry-from$",
        )
        self.assertEqual(
            [
                "Given an existing ticket, an artifact is materialized",
                "The artifact handle identifies that ticket",
            ],
            payload["artifact"]["acceptance_criteria"],
        )

    def test_materializer_routes_quality_gaps_to_refinement(self) -> None:
        base_handle = {"id": "tenant-alpha:tracker-main:ticket-blue", "display": "GW-blue"}

        no_criteria = json.dumps(
            {"handle": base_handle, "title": "T", "body": "A description, no list.", "state": "open"}
        )
        result = materialize(no_criteria)
        self.assertEqual(1, result.returncode)
        self.assertIn("no extractable acceptance criteria", result.stderr)
        self.assertIn("refine-work-unit", result.stderr)

        closed = json.dumps(
            {"handle": base_handle, "title": "T", "body": "## Acceptance criteria\n- [ ] x\n", "state": "closed"}
        )
        result = materialize(closed)
        self.assertEqual(1, result.returncode)
        self.assertIn("not open", result.stderr)

        empty_body = json.dumps({"handle": base_handle, "title": "T", "body": "", "state": "open"})
        result = materialize(empty_body)
        self.assertEqual(1, result.returncode)
        self.assertIn("empty body", result.stderr)

    def test_materializer_rejects_provider_shaped_handles(self) -> None:
        provider_snapshot = {
            "handle": {
                "forge_tag": "github",
                "url": "https://github.com/tesserine/groundwork/issues/440",
                "number": 440,
            },
            "title": "T",
            "body": "## Acceptance criteria\n- [ ] x\n",
            "state": "open",
        }

        result = materialize(json.dumps(provider_snapshot))

        self.assertEqual(1, result.returncode)
        self.assertIn("handle.id and handle.display", result.stderr)


if __name__ == "__main__":
    unittest.main()
