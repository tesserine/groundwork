import contextlib
import io
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


class MechanicResolutionTests(unittest.TestCase):
    def resolution(self):
        try:
            from tooling import mechanic_resolution
        except ImportError:
            self.fail("tooling.mechanic_resolution must expose runtime forge-operation resolution")
        return mechanic_resolution

    def test_active_forge_defaults_to_github_when_environment_is_absent(self) -> None:
        resolution = self.resolution()

        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual("github", resolution.active_forge())

    def test_active_forge_reads_groundwork_forge_contract_symbol(self) -> None:
        resolution = self.resolution()

        with mock.patch.dict(os.environ, {resolution.GROUNDWORK_FORGE_ENV: "sourcehut"}, clear=True):
            self.assertEqual("sourcehut", resolution.active_forge())

    def test_explicit_forge_override_supplies_standalone_resolution_value(self) -> None:
        resolution = self.resolution()

        with mock.patch.dict(os.environ, {resolution.GROUNDWORK_FORGE_ENV: "github"}, clear=True):
            self.assertEqual("sourcehut", resolution.active_forge(override="sourcehut"))

    def test_forge_operation_resolves_to_exactly_one_active_forge_mechanic(self) -> None:
        resolution = self.resolution()

        mechanic = resolution.resolve_mechanic("deliver-change-proposal", forge="sourcehut", root=ROOT)

        self.assertEqual("deliver-change-proposal", mechanic["name"])
        self.assertEqual("sourcehut", mechanic["forge_tag"])
        self.assertIn("default_invocation", mechanic)

    def test_resolution_halts_when_active_forge_binding_is_missing(self) -> None:
        resolution = self.resolution()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "manifest.toml").write_text(
                """
[[forge_tags]]
name = "github"

[[forge_tags]]
name = "sourcehut"

[[mechanics]]
name = "close-out"
forge_tags = ["github", "sourcehut"]
""".lstrip(),
                encoding="utf-8",
            )
            mechanics = root / "mechanics" / "github"
            mechanics.mkdir(parents=True)
            mechanics.joinpath("close-out.toml").write_text(
                """
name = "close-out"
purpose = "Close a GitHub work unit."
forge_tag = "github"
default_invocation = "true"
parameters = []
examples = ["true"]

[outcome]
description = "Closed."
""".lstrip(),
                encoding="utf-8",
            )

            with self.assertRaises(resolution.MechanicResolutionError) as context:
                resolution.resolve_mechanic("close-out", forge="sourcehut", root=root)

        self.assertIn("close-out", str(context.exception))
        self.assertIn("sourcehut", str(context.exception))
        self.assertIn("0", str(context.exception))

    def test_invocation_uses_environment_parameters_without_textual_substitution(self) -> None:
        resolution = self.resolution()
        mechanic = {
            "name": "echo-value",
            "default_invocation": 'printf "%s\\n" "$free_text"',
            "parameters": [
                {"name": "free_text", "purpose": "Text value.", "required": True},
            ],
        }

        invocation = resolution.prepare_invocation(
            mechanic,
            {"free_text": "hello; rm -rf / spaces"},
        )

        self.assertEqual('printf "%s\\n" "$free_text"', invocation.command)
        self.assertEqual({"free_text": "hello; rm -rf / spaces"}, invocation.environment)
        self.assertNotIn("hello; rm -rf", invocation.command)

    def test_secret_parameter_values_are_absent_from_inspected_invocation(self) -> None:
        resolution = self.resolution()
        mechanic = {
            "name": "authorized",
            "default_invocation": 'curl --header "Authorization: Bearer $token" "$url"',
            "parameters": [
                {"name": "token", "purpose": "Secret token.", "required": True, "secret": True},
                {"name": "url", "purpose": "Endpoint.", "required": True},
            ],
        }

        invocation = resolution.prepare_invocation(
            mechanic,
            {"token": "super-secret-token", "url": "https://example.invalid/query"},
        )

        inspected = invocation.inspect()
        self.assertIn("$token", inspected)
        self.assertIn("$url", inspected)
        self.assertNotIn("super-secret-token", inspected)
        self.assertNotIn("https://example.invalid/query", inspected)

    def test_shell_metacharacter_parameter_reaches_mechanic_as_one_literal_value(self) -> None:
        resolution = self.resolution()
        mechanic = {
            "name": "echo-value",
            "default_invocation": 'python3 -c "import os; print(os.environ[\\"free_text\\"])"',
            "parameters": [
                {"name": "free_text", "purpose": "Text value.", "required": True},
            ],
        }
        value = "two words; $(printf injected) && false"

        invocation = resolution.prepare_invocation(mechanic, {"free_text": value})
        result = invocation.run(cwd=ROOT)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(value, result.stdout.rstrip("\n"))

    def test_cli_resolves_from_installed_session_layout(self) -> None:
        resolution = self.resolution()

        with tempfile.TemporaryDirectory() as directory:
            installed = Path(directory) / "land"
            installed.mkdir()
            for name in ["manifest.toml", "mechanics", "schemas", "tooling"]:
                source = ROOT / name
                destination = installed / name
                if source.is_dir():
                    subprocess.run(["cp", "-R", str(source), str(destination)], check=True)
                else:
                    destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")

            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                status = resolution.main(
                    [
                        "resolve",
                        "deliver-change-proposal",
                        "--forge",
                        "sourcehut",
                        "--root",
                        str(installed),
                    ]
                )

        self.assertEqual(0, status)
        self.assertEqual("mechanics/sourcehut/deliver-change-proposal.toml", stdout.getvalue().strip())


if __name__ == "__main__":
    unittest.main()
