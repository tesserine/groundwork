import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tooling.forge_resolution import (
    ForgeResolutionError,
    active_forge,
    invoke_mechanic,
    render_invocation,
    resolve_operation,
)


class ForgeResolutionTests(unittest.TestCase):
    def write(self, root: Path, relative: str, contents: str) -> Path:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")
        return path

    def write_valid_matrix(self, root: Path) -> None:
        self.write(
            root,
            "manifest.toml",
            """
            [[forge_tags]]
            name = "github"

            [[forge_tags]]
            name = "sourcehut"

            [[mechanics]]
            name = "deliver-change-proposal"
            forge_tags = ["github", "sourcehut"]
            """,
        )
        for forge in ["github", "sourcehut"]:
            self.write(
                root,
                f"mechanics/{forge}/deliver-change-proposal.toml",
                f"""
                name = "deliver-change-proposal"
                purpose = "Deliver through {forge}."
                forge_tag = "{forge}"
                default_invocation = "printf '%s\\n' {{{forge}_value}}"
                examples = ["printf '%s\\n' example"]

                [[parameters]]
                name = "{forge}_value"
                purpose = "Value to print."
                required = true

                [outcome]
                description = "Value printed."
                """,
            )

    def test_active_forge_defaults_to_github_when_environment_is_absent(self) -> None:
        self.assertEqual("github", active_forge(env={}))

    def test_active_forge_reads_groundwork_forge_and_allows_explicit_override(self) -> None:
        self.assertEqual("sourcehut", active_forge(env={"GROUNDWORK_FORGE": "sourcehut"}))
        self.assertEqual("github", active_forge(env={"GROUNDWORK_FORGE": "sourcehut"}, override="github"))

    def test_operation_resolves_to_exactly_one_mechanic_for_active_forge(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_valid_matrix(root)

            mechanic = resolve_operation(
                "deliver-change-proposal",
                root=root,
                active_forge_override="sourcehut",
            )

        self.assertEqual("deliver-change-proposal", mechanic["name"])
        self.assertEqual("sourcehut", mechanic["forge_tag"])

    def test_resolution_errors_name_operation_and_forge_for_missing_cell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "manifest.toml",
                """
                [[forge_tags]]
                name = "github"

                [[forge_tags]]
                name = "sourcehut"

                [[mechanics]]
                name = "close-out"
                forge_tags = ["github", "sourcehut"]
                """,
            )
            self.write(
                root,
                "mechanics/github/close-out.toml",
                """
                name = "close-out"
                purpose = "Close GitHub work."
                forge_tag = "github"
                default_invocation = "true"
                examples = ["true"]

                [outcome]
                description = "Closed."
                """,
            )

            with self.assertRaises(ForgeResolutionError) as context:
                resolve_operation("close-out", root=root, active_forge_override="sourcehut")

        self.assertIn("close-out", str(context.exception))
        self.assertIn("sourcehut", str(context.exception))

    def test_resolution_errors_name_operation_and_forge_for_duplicate_cell(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write(
                root,
                "manifest.toml",
                """
                [[forge_tags]]
                name = "github"

                [[mechanics]]
                name = "close-out"
                forge_tags = ["github"]
                """,
            )
            mechanic = """
                name = "close-out"
                purpose = "Close GitHub work."
                forge_tag = "github"
                default_invocation = "true"
                examples = ["true"]

                [outcome]
                description = "Closed."
                """
            self.write(root, "mechanics/github/one.toml", mechanic)
            self.write(root, "mechanics/github/two.toml", mechanic)

            with self.assertRaises(ForgeResolutionError) as context:
                resolve_operation("close-out", root=root, active_forge_override="github")

        self.assertIn("close-out", str(context.exception))
        self.assertIn("github", str(context.exception))
        self.assertIn("2", str(context.exception))

    def test_render_invocation_quotes_unquoted_parameter_values_for_shell_pipeline(self) -> None:
        rendered = render_invocation(
            "printf '<%s>\\n' {value} && printf done",
            {"value": "one two; echo injected $(uname)"},
        )

        result = subprocess.run(
            rendered,
            shell=True,
            executable="/bin/sh",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("<one two; echo injected $(uname)>\ndone", result.stdout.strip())

    def test_render_invocation_escapes_parameter_values_inside_double_quotes(self) -> None:
        rendered = render_invocation(
            'printf "<%s>\\n" "{value}"',
            {"value": 'one two"; echo injected; printf "'},
        )

        result = subprocess.run(
            rendered,
            shell=True,
            executable="/bin/sh",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('<one two"; echo injected; printf ">', result.stdout.strip())

    def test_invoke_mechanic_preserves_existing_shell_pipelines_with_literal_parameters(self) -> None:
        mechanic = {
            "name": "deliver-change-proposal",
            "default_invocation": "printf '<%s>\\n' {value} && printf 'pipeline-ran\\n'",
        }

        result = invoke_mechanic(
            mechanic,
            {"value": "literal value; echo injected"},
            cwd=Path.cwd(),
            env=os.environ.copy(),
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("<literal value; echo injected>\npipeline-ran\n", result.stdout)
