import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from tooling.forge_operations import (
    ForgeOperationError,
    active_forge_type,
    inspect_invocation,
    render_shell_invocation,
    resolve_operation,
    run_invocation,
)

ROOT = Path(__file__).resolve().parents[1]


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

    def test_active_forge_type_defaults_to_github_when_no_env_or_override_exists(self) -> None:
        self.assertEqual("github", active_forge_type({}, None))

    def test_active_forge_type_uses_explicit_override_before_environment(self) -> None:
        self.assertEqual("sourcehut", active_forge_type({"GROUNDWORK_FORGE_TYPE": "github"}, "sourcehut"))

    def test_active_forge_type_uses_groundwork_forge_type_environment(self) -> None:
        self.assertEqual("sourcehut", active_forge_type({"GROUNDWORK_FORGE_TYPE": "sourcehut"}, None))

    def test_resolve_operation_returns_exact_active_forge_mechanic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_methodology(root)

            mechanic = resolve_operation(root, "close-out", forge_type="sourcehut")

        self.assertEqual("close-out", mechanic["name"])
        self.assertEqual("sourcehut", mechanic["forge_tag"])

    def test_cli_resolve_accepts_forge_type_override(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_methodology(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "forge_operations.py"),
                    "--root",
                    str(root),
                    "--forge-type",
                    "sourcehut",
                    "resolve",
                    "close-out",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("close-out[sourcehut]\n", result.stdout)

    def test_resolve_operation_rejects_duplicate_active_forge_mechanics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_methodology(root, duplicate=True)

            with self.assertRaises(ForgeOperationError) as context:
                resolve_operation(root, "close-out", forge_type="github")

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

    def test_cli_rejects_secret_parameter_value_in_argv_binding(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_secret_probe_methodology(root, 'printf "%s\\n" "$token"')

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "forge_operations.py"),
                    "--root",
                    str(root),
                    "run",
                    "probe",
                    "token=super-secret",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("secret parameter `token`", result.stderr)
        self.assertNotIn("super-secret", result.stderr)

    def test_cli_passes_secret_environment_binding_without_secret_in_child_argv(self) -> None:
        secret = "super-secret-value"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_secret_probe_methodology(
                root,
                (
                    "python3 -c 'import os; "
                    'data=open("/proc/%s/cmdline" % os.getpid(), "rb").read().decode("latin1"); '
                    "print(data); print(os.environ[\"token\"])'"
                ),
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "forge_operations.py"),
                    "--root",
                    str(root),
                    "run",
                    "probe",
                    "--secret-env",
                    "token=GROUNDWORK_TEST_TOKEN",
                ],
                env={**os.environ, "GROUNDWORK_TEST_TOKEN": secret},
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        child_argv, exposed_secret = result.stdout.splitlines()
        self.assertNotIn(secret, child_argv)
        self.assertEqual(secret, exposed_secret)

    def test_cli_resolves_declared_deployment_value_without_parameter_name_knowledge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_deployment_probe_methodology(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "forge_operations.py"),
                    "--root",
                    str(root),
                    "--forge-type",
                    "sourcehut",
                    "run",
                    "probe",
                ],
                env={
                    **os.environ,
                    "GROUNDWORK_FORGE_ENDPOINT": "weforge.build",
                    "GROUNDWORK_FORGE_OWNER": "operator",
                    "GROUNDWORK_FORGE_NAME": "weforge",
                    "GROUNDWORK_FORGE_TRACKER_ID": "4",
                    "GROUNDWORK_FORGE_REPO_ID": "42",
                },
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("42\n", result.stdout)

    def test_cli_resolves_sourcehut_deployment_values_from_groundwork_atoms(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_sourcehut_deployment_probe_methodology(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "forge_operations.py"),
                    "--root",
                    str(root),
                    "--forge-type",
                    "sourcehut",
                    "run",
                    "probe",
                ],
                env={
                    **os.environ,
                    "GROUNDWORK_FORGE_ENDPOINT": "weforge.build",
                    "GROUNDWORK_FORGE_OWNER": "operator",
                    "GROUNDWORK_FORGE_NAME": "weforge",
                    "GROUNDWORK_FORGE_TRACKER_ID": "4",
                    "GROUNDWORK_FORGE_REPO_ID": "42",
                },
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            [
                "https://todo.weforge.build/query",
                "https://git.weforge.build/query",
                "git@git.weforge.build:~operator/weforge",
                "4",
                "42",
            ],
            result.stdout.strip().splitlines(),
        )

    def test_cli_resolves_only_declared_sourcehut_deployment_values(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_sourcehut_tracker_probe_methodology(root)
            environment = {
                **os.environ,
                "GROUNDWORK_FORGE_TYPE": "sourcehut",
                "GROUNDWORK_FORGE_ENDPOINT": "weforge.build",
                "GROUNDWORK_FORGE_OWNER": "operator",
                "GROUNDWORK_FORGE_NAME": "weforge",
                "GROUNDWORK_FORGE_TRACKER_ID": "4",
            }
            environment.pop("GROUNDWORK_FORGE_REPO_ID", None)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "forge_operations.py"),
                    "--root",
                    str(root),
                    "run",
                    "probe",
                ],
                env=environment,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(["https://todo.weforge.build/query", "4"], result.stdout.strip().splitlines())

    def test_cli_names_missing_sourcehut_deployment_atom(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_sourcehut_deployment_probe_methodology(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "forge_operations.py"),
                    "--root",
                    str(root),
                    "--forge-type",
                    "sourcehut",
                    "run",
                    "probe",
                ],
                env={
                    **os.environ,
                    "GROUNDWORK_FORGE_ENDPOINT": "weforge.build",
                    "GROUNDWORK_FORGE_OWNER": "operator",
                    "GROUNDWORK_FORGE_NAME": "weforge",
                    "GROUNDWORK_FORGE_REPO_ID": "42",
                },
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("GROUNDWORK_FORGE_TRACKER_ID", result.stderr)

    def test_cli_resolves_github_repository_from_groundwork_atoms_with_default_forge_type(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_github_deployment_probe_methodology(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "forge_operations.py"),
                    "--root",
                    str(root),
                    "run",
                    "probe",
                ],
                env={
                    **os.environ,
                    "GROUNDWORK_FORGE_OWNER": "tesserine",
                    "GROUNDWORK_FORGE_NAME": "groundwork",
                },
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("tesserine/groundwork\n", result.stdout)

    def test_cli_rejects_caller_supplied_deployment_value(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_github_deployment_probe_methodology(root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "tooling" / "forge_operations.py"),
                    "--root",
                    str(root),
                    "run",
                    "probe",
                    "repository=attacker/repo",
                ],
                env={
                    **os.environ,
                    "GROUNDWORK_FORGE_OWNER": "tesserine",
                    "GROUNDWORK_FORGE_NAME": "groundwork",
                },
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("deployment-resolved parameter(s)", result.stderr)
        self.assertIn("repository", result.stderr)

    def write_secret_probe_methodology(self, root: Path, invocation: str) -> None:
        (root / "manifest.toml").write_text(
            textwrap.dedent(
                """
                [[forge_tags]]
                name = "github"

                [[mechanics]]
                name = "probe"
                forge_tags = ["github"]
                """
            ).lstrip(),
            encoding="utf-8",
        )
        (root / "mechanics" / "github").mkdir(parents=True, exist_ok=True)
        (root / "mechanics" / "github" / "probe.toml").write_text(
            textwrap.dedent(
                f"""
                name = "probe"
                purpose = "Probe secret argv handling."
                forge_tag = "github"
                default_invocation = {json.dumps(invocation)}
                examples = [{json.dumps(invocation)}]

                [[parameters]]
                name = "token"
                purpose = "Secret token."
                required = true
                secret = true

                [outcome]
                description = "Printed."
                """
            ).lstrip(),
            encoding="utf-8",
        )

    def write_deployment_probe_methodology(self, root: Path) -> None:
        (root / "manifest.toml").write_text(
            textwrap.dedent(
                """
                [[forge_tags]]
                name = "github"

                [[forge_tags]]
                name = "sourcehut"

                [[mechanics]]
                name = "probe"
                forge_tags = ["sourcehut"]
                """
            ).lstrip(),
            encoding="utf-8",
        )
        (root / "mechanics" / "sourcehut").mkdir(parents=True, exist_ok=True)
        (root / "mechanics" / "sourcehut" / "probe.toml").write_text(
            textwrap.dedent(
                """
                name = "probe"
                purpose = "Probe deployment-value resolution."
                forge_tag = "sourcehut"
                default_invocation = 'printf "%s\\n" "$upload_repo_number"'
                examples = ['printf "%s\\n" "$upload_repo_number"']

                [[parameters]]
                name = "upload_repo_number"
                purpose = "Repo ID under a deliberately non-canonical parameter name."
                required = true
                deployment_value = "repo_id"

                [outcome]
                description = "Printed."
                """
            ).lstrip(),
            encoding="utf-8",
        )

    def write_sourcehut_deployment_probe_methodology(self, root: Path) -> None:
        (root / "manifest.toml").write_text(
            textwrap.dedent(
                """
                [[forge_tags]]
                name = "github"

                [[forge_tags]]
                name = "sourcehut"

                [[mechanics]]
                name = "probe"
                forge_tags = ["sourcehut"]
                """
            ).lstrip(),
            encoding="utf-8",
        )
        (root / "mechanics" / "sourcehut").mkdir(parents=True, exist_ok=True)
        (root / "mechanics" / "sourcehut" / "probe.toml").write_text(
            textwrap.dedent(
                """
                name = "probe"
                purpose = "Probe SourceHut deployment-value resolution."
                forge_tag = "sourcehut"
                default_invocation = 'printf "%s\\n%s\\n%s\\n%s\\n%s\\n" "$todo_url" "$git_url" "$remote" "$tracker" "$repo"'
                examples = ['printf "%s\\n" "$remote"']

                [[parameters]]
                name = "todo_url"
                purpose = "Todo query URL."
                required = true
                deployment_value = "todo_query_url"

                [[parameters]]
                name = "git_url"
                purpose = "Git query URL."
                required = true
                deployment_value = "git_query_url"

                [[parameters]]
                name = "remote"
                purpose = "Git SSH remote."
                required = true
                deployment_value = "ssh_remote"

                [[parameters]]
                name = "tracker"
                purpose = "Tracker ID."
                required = true
                deployment_value = "tracker_id"

                [[parameters]]
                name = "repo"
                purpose = "Repo ID."
                required = true
                deployment_value = "repo_id"

                [outcome]
                description = "Printed."
                """
            ).lstrip(),
            encoding="utf-8",
        )

    def write_sourcehut_tracker_probe_methodology(self, root: Path) -> None:
        (root / "manifest.toml").write_text(
            textwrap.dedent(
                """
                [[forge_tags]]
                name = "sourcehut"

                [[mechanics]]
                name = "probe"
                forge_tags = ["sourcehut"]
                """
            ).lstrip(),
            encoding="utf-8",
        )
        (root / "mechanics" / "sourcehut").mkdir(parents=True, exist_ok=True)
        (root / "mechanics" / "sourcehut" / "probe.toml").write_text(
            textwrap.dedent(
                """
                name = "probe"
                purpose = "Probe tracker-only SourceHut deployment-value resolution."
                forge_tag = "sourcehut"
                default_invocation = 'printf "%s\\n%s\\n" "$todo_url" "$tracker"'
                examples = ['printf "%s\\n" "$tracker"']

                [[parameters]]
                name = "todo_url"
                purpose = "Todo query URL."
                required = true
                deployment_value = "todo_query_url"

                [[parameters]]
                name = "tracker"
                purpose = "Tracker ID."
                required = true
                deployment_value = "tracker_id"

                [outcome]
                description = "Printed."
                """
            ).lstrip(),
            encoding="utf-8",
        )

    def write_github_deployment_probe_methodology(self, root: Path) -> None:
        (root / "manifest.toml").write_text(
            textwrap.dedent(
                """
                [[forge_tags]]
                name = "github"

                [[mechanics]]
                name = "probe"
                forge_tags = ["github"]
                """
            ).lstrip(),
            encoding="utf-8",
        )
        (root / "mechanics" / "github").mkdir(parents=True, exist_ok=True)
        (root / "mechanics" / "github" / "probe.toml").write_text(
            textwrap.dedent(
                """
                name = "probe"
                purpose = "Probe GitHub deployment-value resolution."
                forge_tag = "github"
                default_invocation = 'printf "%s\\n" "$repository"'
                examples = ['printf "%s\\n" "$repository"']

                [[parameters]]
                name = "repository"
                purpose = "GitHub repository."
                required = true
                deployment_value = "repository"

                [outcome]
                description = "Printed."
                """
            ).lstrip(),
            encoding="utf-8",
        )


if __name__ == "__main__":
    unittest.main()
