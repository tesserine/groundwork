import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tooling.forge_operations import (
    ForgeOperationError,
    active_forge,
    inspect_invocation,
    render_shell_invocation,
    resolve_operation,
    run_invocation,
)


class ForgeOperationTests(unittest.TestCase):
    def write_methodology(self, root: Path, *, duplicate: bool = False) -> None:
        (root / "manifest.toml").write_text(
            textwrap.dedent(
                """
                [[forge_tags]]
                name = "github"

                [[forge_tags]]
                name = "sourcehut"

                [[mechanics]]
                name = "close-out"
                forge_tags = ["github", "sourcehut"]
                """
            ).lstrip(),
            encoding="utf-8",
        )
        for forge in ["github", "sourcehut"]:
            directory = root / "mechanics" / forge
            directory.mkdir(parents=True, exist_ok=True)
            (directory / "close-out.toml").write_text(
                textwrap.dedent(
                    f"""
                    name = "close-out"
                    purpose = "Close out on {forge}."
                    forge_tag = "{forge}"
                    default_invocation = "printf '%s\\n' \\"${{message}}\\""
                    examples = ["printf '%s\\n' \\"done\\""]

                    [[parameters]]
                    name = "message"
                    purpose = "Completion message."
                    required = true

                    [outcome]
                    description = "The work unit is closed."
                    """
                ).lstrip(),
                encoding="utf-8",
            )
        if duplicate:
            (root / "mechanics" / "github" / "duplicate.toml").write_text(
                (root / "mechanics" / "github" / "close-out.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )

    def test_active_forge_defaults_to_github_when_no_env_or_override_exists(self) -> None:
        self.assertEqual("github", active_forge({}, None))

    def test_active_forge_uses_explicit_override_before_environment(self) -> None:
        self.assertEqual("sourcehut", active_forge({"GROUNDWORK_FORGE": "github"}, "sourcehut"))

    def test_resolve_operation_returns_exact_active_forge_mechanic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_methodology(root)

            mechanic = resolve_operation(root, "close-out", forge="sourcehut")

        self.assertEqual("close-out", mechanic["name"])
        self.assertEqual("sourcehut", mechanic["forge_tag"])

    def test_resolve_operation_rejects_duplicate_active_forge_mechanics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_methodology(root, duplicate=True)

            with self.assertRaises(ForgeOperationError) as context:
                resolve_operation(root, "close-out", forge="github")

        self.assertIn("close-out", str(context.exception))
        self.assertIn("github", str(context.exception))
        self.assertIn("resolves to 2", str(context.exception))

    def test_inspect_invocation_never_renders_secret_values(self) -> None:
        mechanic = {
            "name": "deliver-change-proposal",
            "forge_tag": "sourcehut",
            "default_invocation": 'curl --header "Authorization: Bearer ${token}" "${url}"',
            "parameters": [
                {"name": "token", "purpose": "API token.", "required": True, "secret": True},
                {"name": "url", "purpose": "Endpoint URL.", "required": True},
            ],
            "outcome": {"description": "Delivered."},
        }

        inspected = inspect_invocation(mechanic, {"token": "super-secret", "url": "https://example.invalid"})

        self.assertIn("${token}", inspected)
        self.assertIn("${url}", inspected)
        self.assertNotIn("super-secret", inspected)
        self.assertNotIn("example.invalid", inspected)

    def test_inspect_invocation_does_not_require_parameter_values(self) -> None:
        mechanic = {
            "name": "close-out",
            "default_invocation": 'printf "%s\\n" "$message"',
            "parameters": [{"name": "message", "purpose": "Message.", "required": True}],
            "outcome": {"description": "Printed."},
        }

        self.assertEqual('printf "%s\\n" "$message"', inspect_invocation(mechanic, {}))

    def test_run_invocation_passes_shell_metacharacters_as_one_literal_value(self) -> None:
        mechanic = {
            "name": "probe",
            "default_invocation": 'python3 -c "import os, sys; print(sys.argv[1]); print(os.environ[\\\"secret\\\"])" "$message"',
            "parameters": [
                {"name": "message", "purpose": "Free text.", "required": True},
                {"name": "secret", "purpose": "Secret.", "required": True, "secret": True},
            ],
            "outcome": {"description": "Printed."},
        }
        message = "hello; printf injected | $(false)"

        result = run_invocation(mechanic, {"message": message, "secret": "kept literal"}, cwd=Path.cwd())

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([message, "kept literal"], result.stdout.strip().splitlines())

    def test_render_shell_invocation_rejects_missing_required_parameter(self) -> None:
        mechanic = {
            "name": "probe",
            "default_invocation": 'printf "%s\\n" "$message"',
            "parameters": [{"name": "message", "purpose": "Message.", "required": True}],
            "outcome": {"description": "Printed."},
        }

        with self.assertRaises(ForgeOperationError) as context:
            render_shell_invocation(mechanic, {})

        self.assertIn("message", str(context.exception))


if __name__ == "__main__":
    unittest.main()
