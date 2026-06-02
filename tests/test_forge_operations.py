import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run_forge_operation(*args: str, cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    if env:
        environment.update(env)
    return subprocess.run(
        [sys.executable, "-m", "tooling.forge_operations", *args],
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


class ForgeOperationTests(unittest.TestCase):
    def test_resolve_defaults_absent_active_forge_to_github(self) -> None:
        env = os.environ.copy()
        env.pop("GROUNDWORK_FORGE", None)

        result = run_forge_operation("resolve", "deliver-change-proposal", env=env)

        self.assertEqual(0, result.returncode, result.stderr)
        resolved = json.loads(result.stdout)
        self.assertEqual("github", resolved["forge_tag"])
        self.assertEqual("deliver-change-proposal", resolved["name"])

    def test_resolve_reads_active_forge_from_environment(self) -> None:
        result = run_forge_operation("resolve", "deliver-change-proposal", env={"GROUNDWORK_FORGE": "sourcehut"})

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("sourcehut", json.loads(result.stdout)["forge_tag"])

    def test_resolve_explicit_forge_overrides_environment(self) -> None:
        result = run_forge_operation(
            "resolve",
            "deliver-change-proposal",
            "--forge",
            "github",
            env={"GROUNDWORK_FORGE": "sourcehut"},
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("github", json.loads(result.stdout)["forge_tag"])

    def test_render_substitutes_double_brace_placeholders_and_keeps_literal_braces(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text(
                textwrap.dedent(
                    """
                    [[forge_tags]]
                    name = "github"

                    [[mechanics]]
                    name = "emit-json"
                    forge_tags = ["github"]
                    """
                ).lstrip(),
                encoding="utf-8",
            )
            mechanics = root / "mechanics" / "github"
            mechanics.mkdir(parents=True)
            (mechanics / "emit-json.toml").write_text(
                textwrap.dedent(
                    """
                    name = "emit-json"
                    purpose = "Emit JSON with one substituted value."
                    forge_tag = "github"
                    default_invocation = '''printf '%s\\n' '{"literal": "{kept}", "value": {{value}}}' '''
                    examples = ["printf"]

                    [[parameters]]
                    name = "value"
                    purpose = "Value to substitute."
                    required = true

                    [outcome]
                    description = "JSON text is emitted."
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            result = run_forge_operation(
                "render",
                "emit-json",
                "--root",
                str(root),
                "--param",
                "value=alpha beta",
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn('{"literal": "{kept}", "value":', result.stdout)
        self.assertNotIn("{{value}}", result.stdout)
        self.assertIn("alpha beta", result.stdout)

    def test_invoke_passes_shell_metacharacter_parameter_as_one_literal_argument(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            touched = root / "pwned"
            (root / "manifest.toml").write_text(
                textwrap.dedent(
                    """
                    [[forge_tags]]
                    name = "github"

                    [[mechanics]]
                    name = "inspect-argv"
                    forge_tags = ["github"]
                    """
                ).lstrip(),
                encoding="utf-8",
            )
            mechanics = root / "mechanics" / "github"
            mechanics.mkdir(parents=True)
            (mechanics / "inspect-argv.toml").write_text(
                textwrap.dedent(
                    """
                    name = "inspect-argv"
                    purpose = "Print argv."
                    forge_tag = "github"
                    default_invocation = "python3 -c 'import json, sys; print(json.dumps(sys.argv[1:]))' {{value}}"
                    examples = ["python3 -c"]

                    [[parameters]]
                    name = "value"
                    purpose = "Value to pass as one argv item."
                    required = true

                    [outcome]
                    description = "The argv is printed."
                    """
                ).lstrip(),
                encoding="utf-8",
            )

            result = run_forge_operation(
                "invoke",
                "inspect-argv",
                "--root",
                str(root),
                "--param",
                f"value=alpha beta; touch {touched}",
            )

            self.assertFalse(touched.exists())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([f"alpha beta; touch {touched}"], json.loads(result.stdout))


if __name__ == "__main__":
    unittest.main()
