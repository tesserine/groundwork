"""Acquisition: materializing a work-unit artifact from an existing forge ticket.

Two layers, mirroring the repo's two-forge test standard:

- Materialization (always runs): the real `read-ticket` mechanic on each forge,
  driven against a fake `gh`/`curl`, piped through `materialize.py`, yields a
  schema-valid work-unit whose handle identifies the ticket — and the forge is
  only read, never mutated (ticket count unchanged).
- Live end-to-end (skipped without runa): a materialized work-unit delivered
  through `runa-mcp --protocol decompose` (the surface that serves the
  `work-unit` tool) persists into the store, and the cascade then computes
  `take` as the next READY station for that work-unit — entry from an existing
  ticket, end to end.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tooling.artifact_schemas import registry_from_manifest, validate_artifact
from tooling.forge_operations import RUNA_FORGE_ADDRESSES, resolve_operation, run_invocation
from tests.test_forge_operations import forge_payload

ROOT = Path(__file__).resolve().parents[1]
MATERIALIZE = ROOT / "skills" / "acquire" / "scripts" / "materialize.py"

GITHUB_TICKET_BODY = (
    "Cold-start entry from a forge ticket reference.\n\n"
    "## Acceptance criteria\n\n"
    "- [ ] Given an existing ticket, an artifact is materialized\n"
    "- [ ] The artifact handle identifies that ticket\n"
)
SOURCEHUT_TICKET_BODY = (
    "Cold-start entry from a forge ticket reference.\n\n"
    "## Acceptance criteria\n\n"
    "- [ ] Materialize the work-unit from the ticket\n"
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
    def test_github_ticket_materializes_to_schema_valid_adopted_work_unit(self) -> None:
        mechanic = resolve_operation(
            ROOT,
            "read-ticket",
            repository="github",
            environment={RUNA_FORGE_ADDRESSES: forge_payload()},
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            call_log = root / "gh-calls.log"
            issue = {
                "html_url": "https://github.com/tesserine/runa/issues/188",
                "number": 188,
                "title": "task(entry): cold-start scoped entry from a forge ticket",
                "body": GITHUB_TICKET_BODY,
                "state": "open",
            }
            write_fake_command(
                bin_dir / "gh",
                f'printf "%s\\n" "gh $*" >> "{call_log}"\n'
                f"cat <<'JSON'\n{json.dumps(issue)}\nJSON",
            )
            with mock.patch.dict(
                os.environ,
                {
                    "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                    RUNA_FORGE_ADDRESSES: forge_payload(),
                },
            ):
                read = run_invocation(mechanic, {"ticket_number": "188"}, cwd=root)

            self.assertEqual(0, read.returncode, read.stderr)
            result = materialize(read.stdout)
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)

            validate_artifact(
                "work-unit", payload["artifact"], registry=registry_from_manifest()
            )
            self.assertEqual(
                {
                    "forge_tag": "github",
                    "url": issue["html_url"],
                    "number": 188,
                    "tracker_identity": "github@github.com/tracker/tesserine/groundwork",
                    "work_unit_identity": "github@github.com/tracker/tesserine/groundwork#188",
                },
                payload["artifact"]["handle"],
            )
            self.assertEqual(
                "work-unit-188-task-entry-cold-start-scoped-entry-from",
                payload["instance_id"],
            )
            self.assertEqual(
                [
                    "Given an existing ticket, an artifact is materialized",
                    "The artifact handle identifies that ticket",
                ],
                payload["artifact"]["acceptance_criteria"],
            )

            # The forge was only read — no create/edit/mutation: ticket count
            # on the forge is unchanged.
            gh_calls = call_log.read_text(encoding="utf-8")
            self.assertIn("api --hostname github.com repos/tesserine/groundwork/issues/188", gh_calls)
            for mutating in ("issue create", "--method POST", "--method PATCH", "-X POST"):
                self.assertNotIn(mutating, gh_calls)

    def test_sourcehut_ticket_materializes_to_schema_valid_adopted_work_unit(self) -> None:
        mechanic = resolve_operation(
            ROOT,
            "read-ticket",
            tracker="sourcehut",
            environment={RUNA_FORGE_ADDRESSES: forge_payload()},
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            payload_file = root / "graphql-payload.json"
            graphql_response = {
                "data": {
                    "user": {
                        "tracker": {
                            "id": 4,
                            "ticket": {
                                "id": 188,
                                "ref": "todo/188",
                                "subject": "cold-start scoped entry from a forge ticket",
                                "body": SOURCEHUT_TICKET_BODY,
                                "status": "REPORTED",
                                "resolution": None,
                            },
                        }
                    }
                }
            }
            write_fake_command(
                bin_dir / "curl",
                f'for arg in "$@"; do case "$arg" in @*) cp "${{arg#@}}" "{payload_file}" ;; esac; done\n'
                f"cat <<'JSON'\n{json.dumps(graphql_response)}\nJSON",
            )
            with mock.patch.dict(
                os.environ,
                {
                    "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                    RUNA_FORGE_ADDRESSES: forge_payload(),
                },
            ):
                read = run_invocation(
                    mechanic, {"ticket_number": "188", "token": "secret-token"}, cwd=root
                )

            self.assertEqual(0, read.returncode, read.stderr)
            result = materialize(read.stdout)
            self.assertEqual(0, result.returncode, result.stderr)
            payload = json.loads(result.stdout)

            validate_artifact(
                "work-unit", payload["artifact"], registry=registry_from_manifest()
            )
            self.assertEqual(
                {
                    "forge_tag": "sourcehut",
                    "tracker_id": 4,
                    "number": 188,
                    "tracker_identity": "sourcehut@git=git.weforge.build,tracker=todo.weforge.build/tracker/operator/weforge/4",
                    "work_unit_identity": "sourcehut@git=git.weforge.build,tracker=todo.weforge.build/tracker/operator/weforge/4#188",
                },
                payload["artifact"]["handle"],
            )
            self.assertTrue(payload["instance_id"].startswith("work-unit-188-"))
            self.assertEqual(
                ["Materialize the work-unit from the ticket"],
                payload["artifact"]["acceptance_criteria"],
            )

            # Read path only — a GraphQL query, never a mutation.
            graphql = json.loads(payload_file.read_text(encoding="utf-8"))
            self.assertIn("query readTicket", graphql["query"])
            self.assertNotIn("mutation", graphql["query"])

    def test_materializer_routes_quality_gaps_to_refinement(self) -> None:
        base_handle = {
            "forge_tag": "github",
            "url": "https://github.com/o/r/issues/3",
            "number": 3,
            "tracker_identity": "github@github.com/tracker/o/r",
            "work_unit_identity": "github@github.com/tracker/o/r#3",
        }

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

        # Materialize from a faked existing GitHub ticket (no runtime needed).
        issue = {
            "html_url": "https://github.com/tesserine/runa/issues/188",
            "number": 188,
            "title": "cold-start entry",
            "body": GITHUB_TICKET_BODY,
            "state": "open",
        }
        mechanic = resolve_operation(
            ROOT,
            "read-ticket",
            repository="github",
            environment={RUNA_FORGE_ADDRESSES: forge_payload()},
        )

        with tempfile.TemporaryDirectory(prefix="groundwork-acquire-") as tmp:
            root = Path(tmp)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            write_fake_command(bin_dir / "gh", f"cat <<'JSON'\n{json.dumps(issue)}\nJSON")
            project = root / "project"
            project.mkdir()

            init = subprocess.run(
                [str(runa), "init", "--methodology", str(ROOT / "manifest.toml")],
                cwd=project, capture_output=True, text=True,
            )
            self.assertEqual(init.returncode, 0, f"{init.stdout}\n{init.stderr}")
            (project / ".runa" / "project.toml").write_text("schema_version = 1\n", encoding="utf-8")

            forge_env = {
                **os.environ,
                "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                RUNA_FORGE_ADDRESSES: forge_payload(),
            }
            with mock.patch.dict(
                os.environ,
                {
                    "PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}",
                    RUNA_FORGE_ADDRESSES: forge_payload(),
                },
            ):
                read = run_invocation(mechanic, {"ticket_number": "188"}, cwd=root)
            self.assertEqual(0, read.returncode, read.stderr)
            payload = json.loads(materialize(read.stdout).stdout)
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
                env={**forge_env, "RUNA_WORKING_DIR": str(project)},
            )
            self.assertNotIn('"error"', delivery.stdout,
                             f"stdout:\n{delivery.stdout}\nstderr:\n{delivery.stderr}")

            recorded = project / ".runa" / "workspace" / "work-unit" / f"{instance_id}.json"
            self.assertTrue(
                recorded.is_file(),
                f"artifact not persisted:\nstdout:\n{delivery.stdout}\nstderr:\n{delivery.stderr}",
            )
            body = json.loads(recorded.read_text(encoding="utf-8"))
            self.assertEqual(188, body["handle"]["number"])
            self.assertEqual("github", body["handle"]["forge_tag"])

            # The cascade now computes take as the next READY station for the
            # acquired work-unit — entry from an existing ticket reached take.
            state = subprocess.run(
                [str(runa), "state", "--work-unit", instance_id],
                cwd=project, capture_output=True, text=True, env=forge_env,
            )
            self.assertEqual(state.returncode, 0, f"{state.stdout}\n{state.stderr}")
            ready_block = state.stdout.split("BLOCKED")[0]
            self.assertIn("take", ready_block,
                          f"take not READY after acquisition:\n{state.stdout}")


if __name__ == "__main__":
    unittest.main()
