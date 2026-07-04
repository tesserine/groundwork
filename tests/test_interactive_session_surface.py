import json
import os
import stat
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"
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
                            "Interactive sessions reach define through the runa session surface"
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
                    printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"contract","arguments":{{"instance_id":"contract-1","title":"Interactive sessions use the session surface","criteria":[{{"id":"session-surface-records-output","dimension":"behavior","acceptance_criterion":"Interactive sessions reach define through the runa session surface","statement":"The scoped session records the produced contract artifact through the MCP session surface.","hollow_delivery":"The agent prints a contract but no validated artifact is persisted.","check_kind":"executable","check":"Run the interactive session smoke test."}}]}}}}}}'
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
                (workspace / "contract" / "contract-1.json").read_text(encoding="utf-8")
            )
            self.assertEqual(contract["work_unit"], WORK_UNIT_ID)
            self.assertEqual(
                contract["criteria"][0]["acceptance_criterion"],
                "Interactive sessions reach define through the runa session surface",
            )

    def test_completion_evidence_persist_rejects_contract_mismatches(self) -> None:
        runa = runa_bin()
        self.assertIsNotNone(runa)
        runa_mcp = runa_mcp_bin(runa)
        if runa_mcp is None:
            self.skipTest("runa-mcp binary not available")

        work_unit_id = "work-unit-492-contract-machine"
        with tempfile.TemporaryDirectory(prefix="groundwork-runa-contract-evidence-") as tmp:
            root = Path(tmp)
            project_dir = root / "project"
            project_dir.mkdir()

            init = run([str(runa), "init", "--methodology", str(ROOT / "manifest.toml")], project_dir)
            self.assertEqual(init.returncode, 0, f"stdout:\n{init.stdout}\nstderr:\n{init.stderr}")

            workspace = project_dir / ".runa" / "workspace"
            (workspace / "work-unit").mkdir(parents=True)
            (workspace / "work-unit" / f"{work_unit_id}.json").write_text(
                json.dumps(
                    {
                        "title": "task(contract): reject mismatched completion evidence",
                        "description": "Completion evidence must cover the declared contract criteria.",
                        "acceptance_criteria": [
                            "Completion evidence names only declared contract criteria",
                        ],
                        "handle": {
                            "id": "ticket:492-contract-machine",
                            "display": "492",
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            (workspace / "contract").mkdir()
            contract = json.loads((ARTIFACT_FIXTURES / "valid-contract.json").read_text(encoding="utf-8"))
            (workspace / "contract" / "contract-1.json").write_text(
                json.dumps(contract, indent=2),
                encoding="utf-8",
            )

            valid_evidence = json.loads(
                (ARTIFACT_FIXTURES / "valid-completion-evidence.json").read_text(encoding="utf-8")
            )

            def unknown_criterion(evidence: dict) -> None:
                evidence["results"][0]["criterion_id"] = "unknown-contract-criterion"

            def missing_criterion(evidence: dict) -> None:
                evidence["results"].pop()

            cases = [
                ("completion-unknown", "unknown contract criterion", unknown_criterion),
                ("completion-missing", "has no completion evidence", missing_criterion),
            ]
            for instance_id, expected, mutate in cases:
                with self.subTest(instance_id=instance_id):
                    evidence = json.loads(json.dumps(valid_evidence))
                    mutate(evidence)
                    rpc = "\n".join(
                        json.dumps(message)
                        for message in [
                            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
                             "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                                        "clientInfo": {"name": "contract-evidence-persist-smoke", "version": "1.0.0"}}},
                            {"jsonrpc": "2.0", "method": "notifications/initialized"},
                            {"jsonrpc": "2.0", "id": 2, "method": "tools/call",
                             "params": {"name": "completion-evidence",
                                        "arguments": {"instance_id": instance_id, **evidence}}},
                        ]
                    ) + "\n"

                    delivery = subprocess.run(
                        [str(runa_mcp), "--protocol", "verify", "--work-unit", work_unit_id],
                        cwd=project_dir,
                        input=rpc,
                        capture_output=True,
                        text=True,
                    )

                    self.assertEqual(
                        delivery.returncode,
                        0,
                        f"stdout:\n{delivery.stdout}\nstderr:\n{delivery.stderr}",
                    )
                    self.assertIn(expected, delivery.stdout)
                    self.assertFalse(
                        (workspace / "completion-evidence" / f"{instance_id}.json").exists(),
                        f"invalid completion evidence was persisted:\n{delivery.stdout}",
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
                      define)
                        printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"contract","arguments":{{"instance_id":"contract-1","title":"Dimension criteria stay on the contract surface","criteria":[{{"id":"gate-form-behavior-artifacts","dimension":"behavior","acceptance_criterion":{json.dumps(criterion)},"statement":"Gate-form behavior artifacts stay schema-valid through the runtime MCP tool.","hollow_delivery":"The artifact validates only by fabricating a scenario-shaped contract.","check_kind":"executable","check":"Validate runtime artifacts through the MCP tool."}}]}}}}}}'
                        ;;
                      plan)
                        printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"implementation-plan","arguments":{{"instance_id":"plan-1","summary":"Map gate-checked behavior through the uniform criterion mapping.","design_decisions":[{{"decision":"Key the mapping by contract criterion id.","rationale":"The contract criterion is the single cross-stage traceability key for every dimension."}}],"affected_files":["schemas/contract.schema.json"],"criterion_mapping":[{{"criterion_id":"gate-form-behavior-artifacts","steps":["Validate the gate artifact.","Advance to implement on the produced artifact."]}}]}}}}}}'
                        ;;
                      implement)
                        printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"test-evidence","arguments":{{"instance_id":"evidence-1","evidence":[{{"criterion_id":"gate-form-behavior-artifacts","result":"pass","command":"python -m unittest tests.test_artifact_schemas","output_summary":"Gate-checked artifact fixtures validated."}}]}}}}}}'
                        ;;
                      verify)
                        printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"completion-evidence","arguments":{{"instance_id":"completion-1","results":[{{"criterion_id":"gate-form-behavior-artifacts","result":"pass","evidence":{{"summary":"Gate-form runtime artifacts validated.","run":{{"command":"python -m unittest tests.test_artifact_schemas","result":"pass","output_summary":"Artifact fixtures validated."}}}}}}],"documentation":{{"updated":["schemas/README.md","CHANGELOG.md"],"verified_accurate":["protocols/define/PROTOCOL.md"],"follow_up_work_units":[]}}}}}}}}'
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

            for expected_protocol in ["define", "plan", "implement", "verify"]:
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
                ("contract", "contract-1"),
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
                    self.assertNotIn("behavior_form", artifact)
                    if artifact_type in {"implementation-plan", "test-evidence"}:
                        self.assertIn('"criterion_id"', serialized)
                    self.assertNotIn('"scenarios"', serialized)


if __name__ == "__main__":
    unittest.main()
