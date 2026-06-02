import contextlib
import io
import tempfile
import unittest
from pathlib import Path


class ForgeResolutionTests(unittest.TestCase):
    def test_active_forge_defaults_to_github_when_env_is_absent(self) -> None:
        from tooling.forge_resolution import active_forge

        self.assertEqual("github", active_forge(environ={}))

    def test_active_forge_reads_groundwork_forge_and_allows_explicit_override(self) -> None:
        from tooling.forge_resolution import active_forge

        self.assertEqual("sourcehut", active_forge(environ={"GROUNDWORK_FORGE": "sourcehut"}))
        self.assertEqual("github", active_forge("github", environ={"GROUNDWORK_FORGE": "sourcehut"}))

    def test_resolves_active_forge_mechanic_from_manifest_matrix(self) -> None:
        from tooling.forge_resolution import resolve_mechanic

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "mechanics" / "github").mkdir(parents=True)
            (root / "mechanics" / "sourcehut").mkdir(parents=True)
            (root / "manifest.toml").write_text(
                """
[[forge_tags]]
name = "github"

[[forge_tags]]
name = "sourcehut"

[[mechanics]]
name = "deliver-change-proposal"
forge_tags = ["github", "sourcehut"]
""".lstrip(),
                encoding="utf-8",
            )
            (root / "mechanics" / "github" / "deliver-change-proposal.toml").write_text(
                """
name = "deliver-change-proposal"
purpose = "github delivery"
forge_tag = "github"
default_invocation = "printf github"
examples = ["printf github"]

[outcome]
description = "delivered"
""".lstrip(),
                encoding="utf-8",
            )
            (root / "mechanics" / "sourcehut" / "deliver-change-proposal.toml").write_text(
                """
name = "deliver-change-proposal"
purpose = "sourcehut delivery"
forge_tag = "sourcehut"
default_invocation = "printf sourcehut"
examples = ["printf sourcehut"]

[outcome]
description = "delivered"
""".lstrip(),
                encoding="utf-8",
            )

            resolved = resolve_mechanic(
                "deliver-change-proposal",
                root=root,
                environ={"GROUNDWORK_FORGE": "sourcehut"},
            )

        self.assertEqual("sourcehut", resolved.forge_tag)
        self.assertEqual("printf sourcehut", resolved.mechanic["default_invocation"])
        self.assertEqual(Path("mechanics/sourcehut/deliver-change-proposal.toml"), resolved.path.relative_to(root))

    def test_resolution_halts_with_operation_and_forge_when_match_count_is_not_one(self) -> None:
        from tooling.forge_resolution import ForgeResolutionError, resolve_mechanic

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "mechanics").mkdir()
            (root / "manifest.toml").write_text(
                """
[[forge_tags]]
name = "github"

[[mechanics]]
name = "close-out"
forge_tags = ["github"]
""".lstrip(),
                encoding="utf-8",
            )

            with self.assertRaises(ForgeResolutionError) as context:
                resolve_mechanic("close-out", root=root, environ={"GROUNDWORK_FORGE": "github"})

        self.assertIn("close-out", str(context.exception))
        self.assertIn("github", str(context.exception))
        self.assertIn("expected exactly 1", str(context.exception))

    def test_cli_resolution_error_exits_nonzero_and_names_operation_and_forge(self) -> None:
        from tooling.forge_resolution import main

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "mechanics").mkdir()
            (root / "manifest.toml").write_text(
                """
[[forge_tags]]
name = "github"

[[mechanics]]
name = "close-out"
forge_tags = ["github"]
""".lstrip(),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                exit_code = main(["resolve", "close-out", "--root", str(root)])

        self.assertEqual(1, exit_code)
        self.assertIn("close-out", stdout.getvalue())
        self.assertIn("github", stdout.getvalue())

    def test_invokes_resolved_mechanic_for_each_active_forge(self) -> None:
        from tooling.forge_resolution import invoke_operation

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "mechanics" / "github").mkdir(parents=True)
            (root / "mechanics" / "sourcehut").mkdir(parents=True)
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
            for forge_tag in ("github", "sourcehut"):
                (root / "mechanics" / forge_tag / "close-out.toml").write_text(
                    f"""
name = "close-out"
purpose = "{forge_tag} close-out"
forge_tag = "{forge_tag}"
default_invocation = "printf {forge_tag} > {{marker}}"
examples = ["printf {forge_tag} > /tmp/marker"]

[outcome]
description = "closed"
""".lstrip(),
                    encoding="utf-8",
                )

            for forge_tag in ("github", "sourcehut"):
                with self.subTest(forge_tag=forge_tag):
                    marker = root / f"{forge_tag}.txt"
                    result = invoke_operation(
                        "close-out",
                        {"marker": str(marker)},
                        root=root,
                        environ={"GROUNDWORK_FORGE": forge_tag},
                    )

                    self.assertEqual(0, result.returncode, result.stderr)
                    self.assertEqual(forge_tag, marker.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
