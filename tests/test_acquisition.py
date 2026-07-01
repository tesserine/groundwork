"""Acquisition: materializing a work-unit artifact from an existing connector ticket."""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tooling.artifact_schemas import registry_from_manifest, validate_artifact

ROOT = Path(__file__).resolve().parents[1]
MATERIALIZE = ROOT / "skills" / "acquire" / "scripts" / "materialize.py"

TICKET_BODY = (
    "Cold-start entry from a forge ticket reference.\n\n"
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


def write_fake_command(path: Path, body: str) -> None:
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


class MaterializeTicketTests(unittest.TestCase):
    def test_opaque_connector_ticket_materializes_to_schema_valid_adopted_work_unit(self) -> None:
        ticket = {
            "handle": {"id": "ticket:opaque-alpha", "display": "TRACK-ALPHA"},
            "title": "task(entry): cold-start scoped entry from a connector ticket",
            "body": TICKET_BODY,
            "state": "open",
        }

        result = materialize(json.dumps(ticket))
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)

        validate_artifact("work-unit", payload["artifact"], registry=registry_from_manifest())
        self.assertEqual(ticket["handle"], payload["artifact"]["handle"])
        self.assertEqual(
            [
                "Given an existing ticket, an artifact is materialized",
                "The artifact handle identifies that ticket",
            ],
            payload["artifact"]["acceptance_criteria"],
        )
        self.assertRegex(payload["instance_id"], r"^work-unit-[0-9a-f]{64}$")

    def test_materializer_identity_uses_handle_id_not_display(self) -> None:
        first = {
            "handle": {"id": "ticket:stable-identity", "display": "First display"},
            "title": "First title",
            "body": TICKET_BODY,
            "state": "open",
        }
        second = {
            **first,
            "handle": {"id": "ticket:stable-identity", "display": "Second display"},
            "title": "Second title",
        }

        first_result = materialize(json.dumps(first))
        second_result = materialize(json.dumps(second))

        self.assertEqual(0, first_result.returncode, first_result.stderr)
        self.assertEqual(0, second_result.returncode, second_result.stderr)
        self.assertEqual(
            json.loads(first_result.stdout)["instance_id"],
            json.loads(second_result.stdout)["instance_id"],
        )

    def test_materializer_preserves_wrapped_acceptance_criteria(self) -> None:
        ticket = {
            "handle": {"id": "ticket:wrapped-criteria", "display": "WRAPPED"},
            "title": "Wrapped criteria",
            "body": (
                "A ticket with wrapped markdown list items.\n\n"
                "## Acceptance criteria\n\n"
                "1. A single contract surface admits criteria for any dimension. Each criterion\n"
                "   declares dimension, acceptance criterion, statement, hollow delivery, and\n"
                "   check descriptor.\n"
                "2. The performed evidence surface records every criterion result in one\n"
                "   shape.\n"
            ),
            "state": "open",
        }

        result = materialize(json.dumps(ticket))

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [
                (
                    "A single contract surface admits criteria for any dimension. Each criterion "
                    "declares dimension, acceptance criterion, statement, hollow delivery, and "
                    "check descriptor."
                ),
                "The performed evidence surface records every criterion result in one shape.",
            ],
            payload["artifact"]["acceptance_criteria"],
        )

    def test_materializer_accepts_valid_titles_that_do_not_slugify(self) -> None:
        ticket = {
            "handle": {"id": "ticket:stable-non-ascii-title", "display": "TRACK-I18N"},
            "title": "修正",
            "body": TICKET_BODY,
            "state": "open",
        }

        result = materialize(json.dumps(ticket))

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(ticket["title"], payload["artifact"]["title"])
        self.assertRegex(payload["instance_id"], r"^work-unit-[0-9a-f]{64}$")

    def test_materializer_routes_quality_gaps_to_refinement(self) -> None:
        base_handle = {"id": "ticket:quality-gap", "display": "QUALITY-GAP"}

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


def runa_bin() -> Path | None:
    configured = os.environ.get("GROUNDWORK_RUNA_BIN")
    if configured:
        path = Path(configured)
        return path if path.is_file() else None
    sibling = ROOT.parent / "runa" / "target" / "debug" / "runa"
    return sibling if sibling.is_file() else None


def runa_mcp_bin(runa: Path) -> Path | None:
    configured = os.environ.get("GROUNDWORK_RUNA_MCP_BIN")
    if configured:
        path = Path(configured)
        return path if path.is_file() else None
    sibling = runa.with_name("runa-mcp")
    return sibling if sibling.is_file() else None


@unittest.skipUnless(runa_bin() is not None, "runa binary not available")
class AcquisitionEntryEndToEndTests(unittest.TestCase):
    def test_acquired_work_unit_makes_take_the_next_ready_station(self) -> None:
        runa = runa_bin()
        runa_mcp = runa_mcp_bin(runa)
        if runa_mcp is None:
            self.skipTest("runa-mcp binary not available")

        ticket = {
            "handle": {"id": "ticket:e2e-188", "display": "188"},
            "title": "cold-start entry",
            "body": TICKET_BODY,
            "state": "open",
        }
        with tempfile.TemporaryDirectory(prefix="groundwork-acquire-") as tmp:
            root = Path(tmp)
            project = root / "project"
            project.mkdir()

            init = subprocess.run(
                [str(runa), "init", "--methodology", str(ROOT / "manifest.toml")],
                cwd=project, capture_output=True, text=True,
            )
            self.assertEqual(init.returncode, 0, f"{init.stdout}\n{init.stderr}")

            payload = json.loads(materialize(json.dumps(ticket)).stdout)
            instance_id = payload["instance_id"]
            artifact = payload["artifact"]

            # Deliver through runa-mcp --protocol decompose: the surface that
            # serves the work-unit output tool. The test acts as the MCP client.
            rpc = "\n".join(
                json.dumps(message)
                for message in [
                    {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                     "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                "clientInfo": {"name": "acquire-smoke", "version": "1.0.0"}}},
                    {"jsonrpc": "2.0", "method": "notifications/initialized"},
                    {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                     "params": {"name": "work-unit",
                                "arguments": {"instance_id": instance_id, **artifact}}},
                ]
            ) + "\n"
            delivery = subprocess.run(
                [str(runa_mcp), "--protocol", "decompose"],
                cwd=project, input=rpc, capture_output=True, text=True,
            )
            self.assertNotIn('"error"', delivery.stdout,
                             f"stdout:\n{delivery.stdout}\nstderr:\n{delivery.stderr}")

            recorded = project / ".runa" / "workspace" / "work-unit" / f"{instance_id}.json"
            self.assertTrue(recorded.is_file(), f"artifact not persisted:\n{delivery.stdout}")
            body = json.loads(recorded.read_text(encoding="utf-8"))
            self.assertEqual(ticket["handle"], body["handle"])

            # The cascade now computes take as the next READY station for the
            # acquired work-unit — entry from an existing ticket reached take.
            state = subprocess.run(
                [str(runa), "state", "--work-unit", instance_id],
                cwd=project, capture_output=True, text=True,
            )
            self.assertEqual(state.returncode, 0, f"{state.stdout}\n{state.stderr}")
            ready_block = state.stdout.split("BLOCKED")[0]
            self.assertIn("take", ready_block,
                          f"take not READY after acquisition:\n{state.stdout}")


if __name__ == "__main__":
    unittest.main()
