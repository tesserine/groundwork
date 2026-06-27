import json
import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK_UNIT_ID = "work-unit-382-task-dual-mode-groundwork-conforms-to"


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


def run(
    args: list[str],
    cwd: Path,
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def write_executable(path: Path, body: str) -> None:
    path.write_text(textwrap.dedent(body).lstrip(), encoding="utf-8")
    mode = path.stat().st_mode
    path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def append_agent_command_config(project_dir: Path, command: list[Path]) -> None:
    config_path = project_dir / ".runa" / "config.toml"
    config = config_path.read_text(encoding="utf-8")
    quoted = ", ".join(json.dumps(str(part)) for part in command)
    config_path.write_text(f"{config}\n[agent]\ncommand = [{quoted}]\n", encoding="utf-8")


def groundwork_env() -> dict[str, str]:
    env = os.environ.copy()
    return env


@unittest.skipUnless(runa_bin() is not None, "runa binary not available")
class InteractiveSessionSurfaceTests(unittest.TestCase):
    def test_go_launches_configured_agent_and_agent_drives_session_surface_tools(self) -> None:
        runa = runa_bin()
        self.assertIsNotNone(runa)
        runa_mcp = runa_mcp_bin(runa)
        if runa_mcp is None:
            self.skipTest("runa-mcp binary not available")

        with tempfile.TemporaryDirectory(prefix="groundwork-runa-go-") as tmp:
            root = Path(tmp)
            project_dir = root / "project"
            project_dir.mkdir()

            init = run([str(runa), "init", "--methodology", str(ROOT / "manifest.toml")], project_dir)
            self.assertEqual(init.returncode, 0, f"stdout:\n{init.stdout}\nstderr:\n{init.stderr}")

            workspace = project_dir / ".runa" / "workspace"
            (workspace / "work-unit").mkdir(parents=True)
            (workspace / "work-unit" / f"{WORK_UNIT_ID}.json").write_text(
                json.dumps(
                    {
                        "title": "task(dual-mode): groundwork conforms to the session surface",
                        "description": "Make interactive Groundwork sessions use runa's validated session surface.",
                        "acceptance_criteria": [
                            "Interactive sessions reach take through the runa session surface"
                        ],
                        "handle": {
                            "id": "ticket:382-session-surface",
                            "display": "382",
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            agent_path = root / "agent.sh"
            prompt_path = root / "prompt.txt"
            config_capture_path = root / "mcp-config.json"
            mcp_log_path = root / "mcp.log"
            write_executable(
                agent_path,
                f"""
                #!/bin/sh
                set -eu
                cat > "$1"
                printf '%s' "$RUNA_MCP_CONFIG" > "$2"
                {{
                    printf '%s\\n' '{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2024-11-05","capabilities":{{}},"clientInfo":{{"name":"groundwork-go-smoke","version":"1.0.0"}}}}}}'
                    printf '%s\\n' '{{"jsonrpc":"2.0","method":"notifications/initialized"}}'
                    printf '%s\\n' '{{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{{"name":"next-protocol-context","arguments":{{}}}}}}'
                    printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"behavior-contract","arguments":{{"instance_id":"contract-1","title":"Interactive sessions use the session surface","behavior_form":"scenario","scenarios":[{{"name":"records output through the session surface","criterion":"Interactive sessions reach take through the runa session surface","given":"a scoped interactive session","when":"the agent records the protocol output","then":"the artifact is validated and persisted by runa"}}]}}}}}}'
                    printf '%s\\n' '{{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{{"name":"advance","arguments":{{}}}}}}'
                    sleep 1
                }} | "$3" --session --work-unit {WORK_UNIT_ID} > "$4"
                if grep -q '"error"' "$4"; then
                    cat "$4" >&2
                    exit 23
                fi
                """,
            )
            append_agent_command_config(
                project_dir,
                [agent_path, prompt_path, config_capture_path, runa_mcp, mcp_log_path],
            )

            output = run(
                [str(runa), "go", "--work-unit", WORK_UNIT_ID],
                project_dir,
                env=groundwork_env(),
            )

            self.assertEqual(
                output.returncode,
                0,
                f"stdout:\n{output.stdout}\nstderr:\n{output.stderr}\nmcp log:\n{mcp_log_path.read_text(encoding='utf-8') if mcp_log_path.exists() else '<missing>'}",
            )
            prompt = prompt_path.read_text(encoding="utf-8")
            self.assertIn("next-protocol-context", prompt)
            self.assertIn("advance", prompt)

            mcp_config = json.loads(config_capture_path.read_text(encoding="utf-8"))
            self.assertEqual(mcp_config["args"], ["--session", "--work-unit", WORK_UNIT_ID])
            self.assertIn("runa-mcp", mcp_config["command"])

            contract = json.loads(
                (workspace / "behavior-contract" / "contract-1.json").read_text(encoding="utf-8")
            )
            self.assertEqual(contract["work_unit"], WORK_UNIT_ID)
            self.assertEqual(contract["behavior_form"], "scenario")
            self.assertEqual(
                contract["scenarios"][0]["criterion"],
                "Interactive sessions reach take through the runa session surface",
            )

    def test_session_sequences_documentation_deliverable_gate_form_behavior(self) -> None:
        runa = runa_bin()
        self.assertIsNotNone(runa)
        runa_mcp = runa_mcp_bin(runa)
        if runa_mcp is None:
            self.skipTest("runa-mcp binary not available")

        work_unit_id = "work-unit-454-runtime-gate-form-behavior"
        with tempfile.TemporaryDirectory(prefix="groundwork-runa-gate-form-") as tmp:
            root = Path(tmp)
            project_dir = root / "project"
            project_dir.mkdir()

            init = run([str(runa), "init", "--methodology", str(ROOT / "manifest.toml")], project_dir)
            self.assertEqual(init.returncode, 0, f"stdout:\n{init.stdout}\nstderr:\n{init.stderr}")

            workspace = project_dir / ".runa" / "workspace"
            (workspace / "work-unit").mkdir(parents=True)
            criterion = "A runtime-backed documentation-deliverable work-unit delivers its behavior dimension without scenarios."
            (workspace / "work-unit" / f"{work_unit_id}.json").write_text(
                json.dumps(
                    {
                        "title": "task(contract/runa): carry gate-form behavior through runtime artifacts",
                        "description": "Make a documentation-deliverable work-unit sequence on gate-form behavior.",
                        "acceptance_criteria": [criterion],
                        "handle": {
                            "id": "ticket:454-runtime-gate-form-behavior",
                            "display": "454",
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            agent_path = root / "agent.sh"
            prompt_path = root / "prompt.txt"
            config_capture_path = root / "mcp-config.json"
            mcp_log_path = root / "mcp.log"
            write_executable(
                agent_path,
                f"""
                #!/bin/sh
                set -eu
                cat > "$1"
                printf '%s' "$RUNA_MCP_CONFIG" > "$2"
                protocol="${{GROUNDWORK_GATE_PROTOCOL:?}}"
                {{
                    printf '%s\\n' '{{"jsonrpc":"2.0","id":1,"method":"initialize","params":{{"protocolVersion":"2024-11-05","capabilities":{{}},"clientInfo":{{"name":"groundwork-gate-form-smoke","version":"1.0.0"}}}}}}'
                    printf '%s\\n' '{{"jsonrpc":"2.0","method":"notifications/initialized"}}'
                    printf '%s\\n' '{{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{{"name":"next-protocol-context","arguments":{{}}}}}}'
                    case "$protocol" in
                      take)
                        printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"behavior-contract","arguments":{{"instance_id":"contract-1","title":"Gate-form behavior stays on the behavior-contract surface","behavior_form":"gate","gates":[{{"name":"gate-form behavior artifacts stay schema-valid","criterion":{json.dumps(criterion)},"category":"structural","check":"Validate gate-form artifacts through the runtime MCP tool."}}]}}}}}}'
                        ;;
                      plan)
                        printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"implementation-plan","arguments":{{"instance_id":"plan-1","behavior_form":"gate","summary":"Map gate-form behavior without scenarios.","design_decisions":[{{"decision":"Use gate-keyed mappings for documentation deliverables.","rationale":"Gate behavior is the behavior form the contract defines for documentation deliverables."}}],"affected_files":["schemas/behavior-contract.schema.json"],"behavior_mapping":[{{"name":"gate-form behavior artifacts stay schema-valid","criterion":{json.dumps(criterion)},"category":"structural","steps":["Validate the gate artifact.","Advance to implement on the produced artifact."]}}]}}}}}}'
                        ;;
                      implement)
                        printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"test-evidence","arguments":{{"instance_id":"evidence-1","behavior_form":"gate","evidence":[{{"name":"gate-form behavior artifacts stay schema-valid","criterion":{json.dumps(criterion)},"category":"structural","result":"pass","command":"python -m unittest tests.test_artifact_schemas","output_summary":"Gate-form artifact fixtures validated."}}]}}}}}}'
                        ;;
                      verify)
                        printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"completion-evidence","arguments":{{"instance_id":"completion-1","behavior_form":"gate","criterion_coverage":[{{"criterion":{json.dumps(criterion)},"status":"covered","gates":[{{"name":"gate-form behavior artifacts stay schema-valid","criterion":{json.dumps(criterion)},"category":"structural","result":"pass"}}]}}],"documentation":{{"updated":["schemas/README.md","CHANGELOG.md"],"verified_accurate":["protocols/take/PROTOCOL.md"],"follow_up_work_units":[]}}}}}}}}'
                        ;;
                      *)
                        printf 'unexpected protocol: %s\\n' "$protocol" >&2
                        exit 24
                        ;;
                    esac
                    printf '%s\\n' '{{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{{"name":"advance","arguments":{{}}}}}}'
                    sleep 1
                }} | "$3" --session --work-unit {work_unit_id} > "$4"
                if grep -q '"error"' "$4"; then
                    cat "$4" >&2
                    exit 23
                fi
                """,
            )
            append_agent_command_config(
                project_dir,
                [agent_path, prompt_path, config_capture_path, runa_mcp, mcp_log_path],
            )

            for expected_protocol in ["take", "plan", "implement", "verify"]:
                with self.subTest(protocol=expected_protocol):
                    env = groundwork_env()
                    env["GROUNDWORK_GATE_PROTOCOL"] = expected_protocol
                    output = run(
                        [str(runa), "go", "--work-unit", work_unit_id],
                        project_dir,
                        env=env,
                    )

                    self.assertEqual(
                        output.returncode,
                        0,
                        f"stdout:\n{output.stdout}\nstderr:\n{output.stderr}\nmcp log:\n{mcp_log_path.read_text(encoding='utf-8') if mcp_log_path.exists() else '<missing>'}",
                    )

            for artifact_type, instance_id in [
                ("behavior-contract", "contract-1"),
                ("implementation-plan", "plan-1"),
                ("test-evidence", "evidence-1"),
                ("completion-evidence", "completion-1"),
            ]:
                with self.subTest(artifact_type=artifact_type):
                    artifact = json.loads(
                        (workspace / artifact_type / f"{instance_id}.json").read_text(encoding="utf-8")
                    )
                    serialized = json.dumps(artifact)
                    self.assertEqual(artifact["work_unit"], work_unit_id)
                    self.assertEqual(artifact["behavior_form"], "gate")
                    self.assertNotIn('"scenarios"', serialized)
                    self.assertNotIn('"scenario"', serialized)


if __name__ == "__main__":
    unittest.main()
