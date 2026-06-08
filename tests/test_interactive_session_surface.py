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
    env.pop("GROUNDWORK_FORGE_TYPE", None)
    env.pop("GROUNDWORK_FORGE_TRACKER_ID", None)
    env["GROUNDWORK_FORGE_OWNER"] = "tesserine"
    env["GROUNDWORK_FORGE_NAME"] = "groundwork"
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
                            "forge_tag": "github",
                            "url": "https://github.com/tesserine/groundwork/issues/382",
                            "number": 382,
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
                    printf '%s\\n' '{{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{{"name":"claim","arguments":{{"instance_id":"claim-1","scope":"claim the session-surface conformance work"}}}}}}'
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

            claim = json.loads((workspace / "claim" / "claim-1.json").read_text(encoding="utf-8"))
            self.assertEqual(claim["work_unit"], WORK_UNIT_ID)
            self.assertEqual(claim["scope"], "claim the session-surface conformance work")


if __name__ == "__main__":
    unittest.main()
