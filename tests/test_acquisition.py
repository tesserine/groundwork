"""Acquisition: materializing a work-unit artifact from an existing connector work-unit."""

import json
import os
import subprocess
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from tooling.artifact_schemas import registry_from_manifest, validate_artifact

ROOT = Path(__file__).resolve().parents[1]
MATERIALIZE = ROOT / "skills" / "acquire" / "scripts" / "materialize.py"

TICKET_BODY = (
    "Cold-start entry from a forge work-unit reference.\n\n"
    "## Acceptance criteria\n\n"
    "- [ ] Given an existing work-unit, an artifact is materialized\n"
    "- [ ] The artifact handle identifies that work-unit\n"
)


def materialize(read_work_unit_stdout: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(MATERIALIZE)],
        input=read_work_unit_stdout,
        capture_output=True,
        text=True,
    )


def write_fake_command(path: Path, body: str) -> None:
    path.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
    path.chmod(0o755)


def append_github_forge_config(project_dir: Path, owner: str, name: str) -> None:
    config_path = project_dir / ".runa" / "config.toml"
    existing = config_path.read_text(encoding="utf-8")
    config_path.write_text(
        f'{existing}\n[forge]\ntype = "github"\nowner = "{owner}"\nname = "{name}"\n',
        encoding="utf-8",
    )


def init_groundwork_project(root: Path, runa: Path) -> Path:
    project = root / "project"
    project.mkdir()
    init = subprocess.run(
        [str(runa), "init", "--methodology", str(ROOT / "manifest.toml")],
        cwd=project,
        capture_output=True,
        text=True,
    )
    assert init.returncode == 0, f"{init.stdout}\n{init.stderr}"
    append_github_forge_config(project, "tesserine", "groundwork")
    return project


def write_workspace_artifact(project: Path, artifact_type: str, instance_id: str, body: dict) -> None:
    directory = project / ".runa" / "workspace" / artifact_type
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{instance_id}.json").write_text(json.dumps(body, indent=2), encoding="utf-8")


class MaterializeTicketTests(unittest.TestCase):
    def test_opaque_connector_ticket_materializes_to_schema_valid_adopted_work_unit(self) -> None:
        ticket = {
            "handle": {"id": "ticket:opaque-alpha", "display": "TRACK-ALPHA"},
            "title": "task(entry): cold-start scoped entry from a connector work-unit",
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
                "Given an existing work-unit, an artifact is materialized",
                "The artifact handle identifies that work-unit",
            ],
            payload["artifact"]["acceptance_criteria"],
        )
        self.assertRegex(payload["instance_id"], r"^work-unit-[0-9a-f]{64}$")

    def test_comment_log_leaves_the_materialized_artifact_unchanged(self) -> None:
        bare = {
            "handle": {"id": "ticket:log-bearing", "display": "TRACK-LOG"},
            "title": "task(entry): resume a unit carrying a live review record",
            "body": TICKET_BODY,
            "state": "open",
        }
        with_log = {
            **bare,
            "comments": [
                {"body": "**Freshen pass — 2026-07-02** grounded at head; freshen-in-place."},
                {
                    "body": "Review round 2: required correction — rename the gate before resume.",
                    "author": "operator",
                    "created_at": "2026-07-02T10:53:26Z",
                },
            ],
        }

        bare_result = materialize(json.dumps(bare))
        log_result = materialize(json.dumps(with_log))

        self.assertEqual(0, bare_result.returncode, bare_result.stderr)
        self.assertEqual(0, log_result.returncode, log_result.stderr)
        self.assertEqual(bare_result.stdout, log_result.stdout)
        self.assertNotIn("comments", json.loads(log_result.stdout)["artifact"])

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
                "A work-unit with wrapped markdown list items.\n\n"
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

    def test_materializer_excludes_trailing_prose_after_acceptance_list(self) -> None:
        ticket = {
            "handle": {"id": "ticket:criteria-prose", "display": "CRITERIA-PROSE"},
            "title": "Trailing prose after criteria",
            "body": (
                "A work-unit with prose after the criteria list.\n\n"
                "## Acceptance criteria\n\n"
                "- [ ] The contract payload uses criteria\n"
                "- [ ] The workflow surfaces name the contract artifact\n"
                "\n"
                "This note explains migration context and is not a criterion.\n\n"
                "## Notes\n\n"
                "Operators should follow the current contract surface.\n"
            ),
            "state": "open",
        }

        result = materialize(json.dumps(ticket))

        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            [
                "The contract payload uses criteria",
                "The workflow surfaces name the contract artifact",
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
    candidates: list[Path] = []
    configured = os.environ.get("GROUNDWORK_RUNA_BIN")
    if configured:
        candidates.append(Path(configured))
    discovered = shutil.which("runa")
    if discovered:
        candidates.append(Path(discovered))
    candidates.append(ROOT.parent / "runa" / "target" / "debug" / "runa")

    for path in candidates:
        if not path.is_file():
            continue
        help_result = subprocess.run(
            [str(path), "run", "--help"],
            capture_output=True,
            text=True,
        )
        if "--work-unit" in help_result.stdout:
            return path
    return None


def runa_mcp_bin(runa: Path) -> Path | None:
    configured = os.environ.get("GROUNDWORK_RUNA_MCP_BIN")
    if configured:
        path = Path(configured)
        return path if path.is_file() else None
    sibling = runa.with_name("runa-mcp")
    return sibling if sibling.is_file() else None


@unittest.skipUnless(runa_bin() is not None, "runa binary not available")
class AcquisitionEntryEndToEndTests(unittest.TestCase):
    def test_intent_target_entry_dry_run_reaches_acquisition_and_projects_define(self) -> None:
        # Cold-start reference entry is the intent.target route: runa retired
        # the flag-based reference entry (runa#222/#224), and `--work-unit`
        # takes a canonical instance id, never a forge reference.
        runa = runa_bin()
        self.assertIsNotNone(runa)

        with tempfile.TemporaryDirectory(prefix="groundwork-acquire-entry-") as tmp:
            project = init_groundwork_project(Path(tmp), runa)
            write_workspace_artifact(
                project,
                "intent",
                "intent-entry",
                {
                    "statement": "Enter on the referenced work-unit.",
                    "source": "operator",
                    "target": "tesserine/groundwork#499",
                },
            )

            output = subprocess.run(
                [str(runa), "run", "--dry-run", "--json"],
                cwd=project,
                capture_output=True,
                text=True,
            )

            self.assertEqual(output.returncode, 0, f"stdout:\n{output.stdout}\nstderr:\n{output.stderr}")
            payload = json.loads(output.stdout)
            self.assertEqual(payload["entry"]["acquisition_protocol"], "decompose")
            self.assertGreater(len(payload["execution_plan"]), 0, payload)
            self.assertEqual(payload["execution_plan"][0]["protocol"], "decompose")
            self.assertEqual(payload["execution_plan"][0]["projection"], "current")
            projected = [
                entry for entry in payload["execution_plan"]
                if entry["protocol"] == "define" and entry["projection"] == "projected"
            ]
            self.assertEqual(1, len(projected), payload["execution_plan"])
            self.assertEqual("work-unit-499", projected[0]["work_unit"])

    def test_untargeted_intent_waits_for_requirements_before_decompose(self) -> None:
        runa = runa_bin()
        self.assertIsNotNone(runa)

        with tempfile.TemporaryDirectory(prefix="groundwork-acquire-planning-") as tmp:
            project = init_groundwork_project(Path(tmp), runa)
            write_workspace_artifact(
                project,
                "intent",
                "intent-untargeted",
                {
                    "statement": "Plan ordinary work before decomposition.",
                    "source": "operator",
                },
            )

            intent_only = subprocess.run(
                [str(runa), "state", "--json"],
                cwd=project,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                intent_only.returncode,
                0,
                f"stdout:\n{intent_only.stdout}\nstderr:\n{intent_only.stderr}",
            )
            intent_state = {
                protocol["name"]: protocol
                for protocol in json.loads(intent_only.stdout)["protocols"]
            }
            self.assertEqual("ready", intent_state["survey"]["status"], intent_state)
            self.assertEqual("waiting", intent_state["decompose"]["status"], intent_state)

            write_workspace_artifact(
                project,
                "requirements",
                "requirements-from-survey",
                {
                    "scope": "Ordinary planning route.",
                    "functional_requirements": ["Requirements precede decomposition."],
                },
            )

            with_requirements = subprocess.run(
                [str(runa), "state", "--json"],
                cwd=project,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                with_requirements.returncode,
                0,
                f"stdout:\n{with_requirements.stdout}\nstderr:\n{with_requirements.stderr}",
            )
            requirements_state = {
                protocol["name"]: protocol
                for protocol in json.loads(with_requirements.stdout)["protocols"]
            }
            self.assertEqual("ready", requirements_state["decompose"]["status"], requirements_state)

    def test_acquired_work_unit_makes_define_the_next_ready_station(self) -> None:
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

            # The cascade now computes define as the next READY station for the
            # acquired work-unit — entry from an existing work-unit reached define.
            state = subprocess.run(
                [str(runa), "state", "--work-unit", instance_id],
                cwd=project, capture_output=True, text=True,
            )
            self.assertEqual(state.returncode, 0, f"{state.stdout}\n{state.stderr}")
            ready_block = state.stdout.split("BLOCKED")[0]
            self.assertIn("define", ready_block,
                          f"define not READY after acquisition:\n{state.stdout}")


if __name__ == "__main__":
    unittest.main()
