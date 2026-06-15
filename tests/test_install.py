"""Behavior coverage for `scripts/install` — the methodology self-install
for runtime-driven deployments (#416).

The installer owns exactly three surfaces: skills verbatim, the methodology
runtime bundle, and principles-corpus recording + materialization. It never
delivers protocol content — that is the runtime's channel.
"""

import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from tooling.principles_config import PrinciplesCorpusConfig, load_principles_config
from tooling.forge_operations import RUNA_FORGE_ADDRESSES
from tests.test_forge_operations import forge_payload


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install"
MARKER_NAME = ".groundwork-managed"
LEGACY_MARKER_NAME = ".groundwork-install"


def run(
    args: list[str],
    cwd: Path,
    *,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(args)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def assert_success(test: unittest.TestCase, result: subprocess.CompletedProcess[str]) -> None:
    test.assertEqual(result.returncode, 0, f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")


def assert_failure_contains(
    test: unittest.TestCase,
    result: subprocess.CompletedProcess[str],
    expected: str,
) -> None:
    test.assertNotEqual(result.returncode, 0, "command unexpectedly succeeded")
    test.assertIn(expected, result.stderr)


def tree_payload(directory: Path, *, exclude: frozenset[str] = frozenset({MARKER_NAME})) -> dict[str, bytes]:
    """Relative path → bytes for every file under ``directory``."""
    payload = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.name not in exclude:
            payload[str(path.relative_to(directory))] = path.read_bytes()
    return payload


class MethodologyFixture:
    """A temp methodology checkout carrying the full self-install surface:
    skills, protocols (present to prove non-projection), the runtime
    surface, and an embedded principles corpus."""

    def __init__(self, name: str) -> None:
        self.root = Path(tempfile.mkdtemp(prefix=f"groundwork-self-install-source-{name}-"))
        self.write_initial_surface()
        self.init_git()

    def write(self, relative: str, contents: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")

    def remove(self, relative: str) -> None:
        path = self.root / relative
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def write_initial_surface(self) -> None:
        self.write("skills/orient/SKILL.md", "---\nname: orient\n---\n# Orient\n")
        self.write("skills/reckon/SKILL.md", "---\nname: reckon\n---\n# Reckon\n")
        self.write("skills/reckon/references/example.md", "reckon reference\n")
        self.write("protocols/take/PROTOCOL.md", "---\nname: take\n---\n# Take\n")
        self.write("principles/PRINCIPLES.md", "# Principles\n\n1. Understand.\n")
        self.write(
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
        for forge in ["github", "sourcehut"]:
            self.write(
                f"mechanics/{forge}/close-out.toml",
                f"""
                name = "close-out"
                purpose = "Close out on {forge}."
                forge_tag = "{forge}"
                default_invocation = 'printf "%s\\n" "$message"'
                examples = ['printf "%s\\n" "$message"']

                [[parameters]]
                name = "message"
                purpose = "Completion message."
                required = true

                [outcome]
                description = "Closed."
                """,
            )
        self.write(
            "tooling/forge_operations.py",
            (ROOT / "tooling" / "forge_operations.py").read_text(encoding="utf-8"),
        )

    def init_git(self) -> None:
        run(["git", "init", "-q"], self.root, check=True)
        run(["git", "config", "user.name", "installer test"], self.root, check=True)
        run(["git", "config", "user.email", "installer-test@example.invalid"], self.root, check=True)
        run(["git", "config", "commit.gpgsign", "false"], self.root, check=True)
        run(["git", "config", "tag.gpgsign", "false"], self.root, check=True)
        run(["git", "checkout", "-q", "-b", "main"], self.root, check=True)
        run(["git", "add", "."], self.root, check=True)
        run(["git", "commit", "-q", "-m", "test: seed methodology"], self.root, check=True)

    def commit(self, message: str) -> None:
        run(["git", "add", "-A"], self.root, check=True)
        run(["git", "commit", "-q", "-m", f"test: {message}"], self.root, check=True)

    def head_sha(self) -> str:
        return run(["git", "rev-parse", "HEAD"], self.root, check=True).stdout.strip()

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class InstallRun:
    """Invokes the installer with an isolated home, state dir, and config dir."""

    def __init__(self, test: unittest.TestCase, source: Path) -> None:
        self.test = test
        self.source = source
        self.home = Path(tempfile.mkdtemp(prefix="groundwork-self-install-home-"))
        self.state = Path(tempfile.mkdtemp(prefix="groundwork-self-install-state-"))
        test.addCleanup(lambda: shutil.rmtree(self.home, ignore_errors=True))
        test.addCleanup(lambda: shutil.rmtree(self.state, ignore_errors=True))

    def run_installer(
        self,
        *args: str,
        include_state_dir: bool = True,
        env: dict[str, str | None] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        self.test.assertTrue(INSTALLER.is_file(), f"installer missing at {INSTALLER}")
        command = [
            str(INSTALLER),
            *args,
            "--source",
            str(self.source),
            "--home",
            str(self.home),
        ]
        if include_state_dir:
            command.extend(["--state-dir", str(self.state)])
        run_env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
        }
        if env:
            for key, value in env.items():
                if value is None:
                    run_env.pop(key, None)
                else:
                    run_env[key] = value
        return run(command, self.source, env=run_env)

    def target(self, root: str, name: str) -> Path:
        return self.home / root / "skills" / name

    def state_file(self) -> Path:
        return self.state / "install.tsv"

    def runtime_root(self) -> Path:
        return self.home / ".groundwork"

    def config_file(self) -> Path:
        return self.home / ".config" / "groundwork" / "principles.toml"


class SelfInstallTests(unittest.TestCase):
    def add_fixture(self, name: str) -> MethodologyFixture:
        fixture = MethodologyFixture(name)
        self.addCleanup(fixture.cleanup)
        return fixture

    def test_install_places_skills_byte_identical_in_both_discovery_roots(self) -> None:
        fixture = self.add_fixture("skills-verbatim")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            skills_dir = install.home / root / "skills"
            self.assertEqual(
                {path.name for path in skills_dir.iterdir()},
                {"orient", "reckon"},
                f"unexpected inventory under {skills_dir}",
            )
            for name in ["orient", "reckon"]:
                self.assertEqual(
                    tree_payload(install.target(root, name)),
                    tree_payload(fixture.root / "skills" / name),
                    f"{root}/{name} is not byte-identical to the tree",
                )


    def test_install_projects_runtime_bundle_and_resolver_executes(self) -> None:
        fixture = self.add_fixture("runtime-bundle")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertEqual(
            (install.runtime_root() / "manifest.toml").read_bytes(),
            (fixture.root / "manifest.toml").read_bytes(),
        )
        self.assertEqual(
            tree_payload(install.runtime_root() / "mechanics"),
            tree_payload(fixture.root / "mechanics"),
        )
        resolver = install.runtime_root() / "bin" / "groundwork-mechanic"
        self.assertTrue(resolver.is_file())
        resolved = run(
            [str(resolver), "--tracker", "sourcehut", "resolve", "close-out"],
            install.runtime_root(),
            env={"PATH": "/usr/bin:/bin", RUNA_FORGE_ADDRESSES: forge_payload()},
        )
        assert_success(self, resolved)
        self.assertEqual("close-out[sourcehut]\n", resolved.stdout)


    def test_absent_input_and_config_resolves_embedded_default(self) -> None:
        fixture = self.add_fixture("zero-config-corpus")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertEqual(
            tree_payload(install.runtime_root() / "principles"),
            tree_payload(fixture.root / "principles"),
        )
        self.assertFalse(install.config_file().exists(), "zero-config run must not write a config file")


    def make_corpus_repository(self, name: str) -> Path:
        """A local git repository carrying an external corpus."""
        corpus = Path(tempfile.mkdtemp(prefix=f"groundwork-self-install-corpus-{name}-"))
        self.addCleanup(lambda: shutil.rmtree(corpus, ignore_errors=True))
        (corpus / "PRINCIPLES.md").write_text("# External Principles\n", encoding="utf-8")
        run(["git", "init", "-q"], corpus, check=True)
        run(["git", "config", "user.name", "corpus test"], corpus, check=True)
        run(["git", "config", "user.email", "corpus-test@example.invalid"], corpus, check=True)
        run(["git", "config", "commit.gpgsign", "false"], corpus, check=True)
        run(["git", "add", "."], corpus, check=True)
        run(["git", "commit", "-q", "-m", "test: seed corpus"], corpus, check=True)
        return corpus

    def test_operator_git_corpus_input_is_recorded_and_materialized(self) -> None:
        fixture = self.add_fixture("operator-git-corpus")
        corpus = self.make_corpus_repository("recorded")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install", "--corpus-git", f"file://{corpus}")

        assert_success(self, result)
        self.assertEqual(
            install.config_file().read_text(encoding="utf-8"),
            f'[corpus]\nsource = "git"\nurl = "file://{corpus}"\n',
        )
        self.assertEqual(
            (install.runtime_root() / "principles" / "PRINCIPLES.md").read_text(encoding="utf-8"),
            "# External Principles\n",
        )
        self.assertFalse((install.runtime_root() / "principles" / ".git").exists())

    def test_home_option_supplies_derived_paths_over_ambient_environment(self) -> None:
        fixture = self.add_fixture("home-derived-paths")
        corpus = self.make_corpus_repository("home-derived")
        install = InstallRun(self, fixture.root)
        ambient_home = Path(tempfile.mkdtemp(prefix="groundwork-self-install-ambient-home-"))
        ambient_state = Path(tempfile.mkdtemp(prefix="groundwork-self-install-ambient-state-"))
        self.addCleanup(lambda: shutil.rmtree(ambient_home, ignore_errors=True))
        self.addCleanup(lambda: shutil.rmtree(ambient_state, ignore_errors=True))

        result = install.run_installer(
            "install",
            "--corpus-git",
            f"file://{corpus}",
            include_state_dir=False,
            env={
                "HOME": str(ambient_home),
                "XDG_CONFIG_HOME": None,
                "XDG_STATE_HOME": str(ambient_state),
            },
        )

        assert_success(self, result)
        self.assertTrue(install.config_file().is_file())
        self.assertEqual(
            load_principles_config(install.config_file()),
            PrinciplesCorpusConfig(source="git", url=f"file://{corpus}"),
        )
        self.assertFalse(
            (ambient_home / ".config" / "groundwork").exists(),
            "ambient HOME config tree must be untouched",
        )
        self.assertTrue(
            (install.home / ".local" / "state" / "groundwork" / "install.tsv").is_file()
        )
        self.assertFalse(
            (ambient_state / "groundwork").exists(),
            "ambient XDG_STATE_HOME must not receive derived state",
        )


    def test_absent_input_honors_existing_config(self) -> None:
        fixture = self.add_fixture("existing-config")
        install = InstallRun(self, fixture.root)
        external = Path(tempfile.mkdtemp(prefix="groundwork-self-install-external-corpus-"))
        self.addCleanup(lambda: shutil.rmtree(external, ignore_errors=True))
        (external / "PRINCIPLES.md").write_text("# Operator Corpus\n", encoding="utf-8")
        operator_written = f'# operator comment\n[corpus]\nsource = "path"\npath = "{external}"\n'
        install.config_file().parent.mkdir(parents=True)
        install.config_file().write_text(operator_written, encoding="utf-8")

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertEqual(install.config_file().read_text(encoding="utf-8"), operator_written)
        self.assertEqual(
            (install.runtime_root() / "principles" / "PRINCIPLES.md").read_text(encoding="utf-8"),
            "# Operator Corpus\n",
        )

    def test_rerecording_identical_corpus_input_does_not_rewrite_config(self) -> None:
        fixture = self.add_fixture("idempotent-recording")
        corpus = self.make_corpus_repository("rerecorded")
        install = InstallRun(self, fixture.root)
        url = f"file://{corpus}"
        assert_success(self, install.run_installer("install", "--corpus-git", url))
        before = install.config_file().stat()

        result = install.run_installer("install", "--corpus-git", url)

        assert_success(self, result)
        after = install.config_file().stat()
        self.assertEqual((before.st_ino, before.st_mtime_ns), (after.st_ino, after.st_mtime_ns))

    def test_explicit_corpus_input_replaces_invalid_existing_config(self) -> None:
        fixture = self.add_fixture("explicit-input-replaces-invalid-config")
        corpus = self.make_corpus_repository("recovery")
        install = InstallRun(self, fixture.root)
        url = f"file://{corpus}"
        install.config_file().parent.mkdir(parents=True)
        install.config_file().write_text("[corpus\n", encoding="utf-8")

        result = install.run_installer("install", "--corpus-git", url)

        assert_success(self, result)
        self.assertEqual(
            load_principles_config(install.config_file()),
            PrinciplesCorpusConfig(source="git", url=url),
        )


    def stat_snapshot(self, *directories: Path) -> dict[str, tuple[int, int]]:
        """inode + mtime for every path under the given directories."""
        snapshot = {}
        for directory in directories:
            for path in sorted(directory.rglob("*")):
                stat = path.stat()
                snapshot[str(path)] = (stat.st_ino, stat.st_mtime_ns)
        return snapshot

    def test_second_run_exits_zero_with_no_state_change(self) -> None:
        fixture = self.add_fixture("idempotent-rerun")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        before = self.stat_snapshot(install.home, install.state)

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertEqual(self.stat_snapshot(install.home, install.state), before)


    def test_skill_removed_from_tree_is_removed_on_rerun(self) -> None:
        fixture = self.add_fixture("stale-skill")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        fixture.remove("skills/reckon")
        fixture.commit("drop reckon")

        result = install.run_installer("install")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            self.assertFalse(install.target(root, "reckon").exists())
            self.assertTrue(install.target(root, "orient").is_dir())


    def test_unmanaged_preexisting_entry_fails_loudly_with_named_path(self) -> None:
        fixture = self.add_fixture("unmanaged-conflict")
        install = InstallRun(self, fixture.root)
        conflicting = install.target(".claude", "orient")
        conflicting.mkdir(parents=True)
        (conflicting / "SKILL.md").write_text("operator content\n", encoding="utf-8")

        result = install.run_installer("install")

        assert_failure_contains(self, result, str(conflicting))
        self.assertEqual(
            (conflicting / "SKILL.md").read_text(encoding="utf-8"),
            "operator content\n",
            "conflicting content must not be touched",
        )
        self.assertFalse((install.home / ".agents").exists(), "preflight must halt before any install")
        self.assertFalse(install.runtime_root().exists(), "preflight must halt before any install")

    def test_state_listed_skill_missing_marker_fails_loudly_and_preserves_drift(self) -> None:
        fixture = self.add_fixture("state-listed-missing-marker")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        target = install.target(".agents", "orient")
        (target / MARKER_NAME).unlink()
        (target / "SKILL.md").write_text("operator rewrite\n", encoding="utf-8")
        local_only = target / "operator-note.md"
        local_only.write_text("operator note\n", encoding="utf-8")

        result = install.run_installer("install")

        assert_failure_contains(self, result, "unmanaged conflict")
        assert_failure_contains(self, result, str(target))
        self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), "operator rewrite\n")
        self.assertEqual(local_only.read_text(encoding="utf-8"), "operator note\n")

    def test_state_listed_skill_replaced_without_marker_fails_loudly(self) -> None:
        fixture = self.add_fixture("state-listed-replaced")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        target = install.target(".agents", "reckon")
        shutil.rmtree(target)
        target.mkdir()
        replacement = target / "SKILL.md"
        replacement.write_text("operator replacement\n", encoding="utf-8")

        result = install.run_installer("install")

        assert_failure_contains(self, result, "unmanaged conflict")
        assert_failure_contains(self, result, str(target))
        self.assertEqual(replacement.read_text(encoding="utf-8"), "operator replacement\n")
        self.assertFalse((target / MARKER_NAME).exists())

    def test_state_listed_skill_with_valid_marker_updates_normally(self) -> None:
        fixture = self.add_fixture("state-listed-valid-marker")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        body = "---\nname: orient\n---\n# Orient v2\n"
        fixture.write("skills/orient/SKILL.md", body)
        fixture.commit("update orient")
        sha = fixture.head_sha()

        result = install.run_installer("install")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            target = install.target(root, "orient")
            self.assertEqual((target / "SKILL.md").read_text(encoding="utf-8"), body)
            self.assertIn(
                f"source-sha={sha}\n",
                (target / MARKER_NAME).read_text(encoding="utf-8"),
            )


    def test_legacy_installed_entry_is_a_named_conflict_directing_to_legacy_uninstall(self) -> None:
        fixture = self.add_fixture("legacy-conflict")
        install = InstallRun(self, fixture.root)
        legacy_entry = install.target(".claude", "orient")
        legacy_entry.mkdir(parents=True)
        (legacy_entry / "SKILL.md").write_text("legacy projection\n", encoding="utf-8")
        (legacy_entry / LEGACY_MARKER_NAME).write_text(
            "managed-by=groundwork-install\n", encoding="utf-8"
        )

        result = install.run_installer("install")

        assert_failure_contains(self, result, str(legacy_entry))
        assert_failure_contains(self, result, "groundwork-install uninstall")
        self.assertTrue((legacy_entry / "SKILL.md").is_file(), "legacy content must not be touched")


    def test_dirty_source_checkout_is_rejected(self) -> None:
        fixture = self.add_fixture("dirty-source")
        fixture.write("skills/orient/SKILL.md", "---\nname: orient\n---\n# Drifted\n")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_failure_contains(self, result, "dirty")
        self.assertFalse((install.home / ".claude").exists())

    def test_source_outside_a_checkout_root_is_rejected(self) -> None:
        fixture = self.add_fixture("nested-source")
        install = InstallRun(self, fixture.root / "skills")

        result = install.run_installer("install")

        assert_failure_contains(self, result, "checkout root")


    def test_uninstall_removes_only_owned_entries_and_preserves_config_file(self) -> None:
        fixture = self.add_fixture("uninstall")
        corpus = self.make_corpus_repository("uninstalled")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install", "--corpus-git", f"file://{corpus}"))
        operator_skill = install.home / ".claude" / "skills" / "operator-own"
        operator_skill.mkdir()
        (operator_skill / "SKILL.md").write_text("not ours\n", encoding="utf-8")

        result = install.run_installer("uninstall")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            for name in ["orient", "reckon"]:
                self.assertFalse(install.target(root, name).exists())
        self.assertFalse(install.runtime_root().exists())
        self.assertFalse(install.state_file().exists())
        self.assertTrue((operator_skill / "SKILL.md").is_file(), "unmanaged content must survive")
        self.assertTrue(install.config_file().is_file(), "deployment-owned config must survive")


    def test_install_never_projects_protocols_into_discovery_roots(self) -> None:
        fixture = self.add_fixture("no-projection")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            skills_dir = install.home / root / "skills"
            self.assertEqual({path.name for path in skills_dir.iterdir()}, {"orient", "reckon"})
        installed_bodies = [
            path.read_text(encoding="utf-8")
            for path in install.home.rglob("*.md")
        ]
        for body in installed_bodies:
            self.assertNotIn("session-surface-handoff", body)

    def test_installed_skill_referencing_mechanic_is_not_rewritten(self) -> None:
        fixture = self.add_fixture("no-rewriting")
        body = "---\nname: orient\n---\n# Orient\n\nRun `groundwork-mechanic resolve close-out`.\n"
        fixture.write("skills/orient/SKILL.md", body)
        fixture.commit("mechanic reference")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            self.assertEqual(
                (install.target(root, "orient") / "SKILL.md").read_text(encoding="utf-8"),
                body,
            )

    def test_skill_set_is_enumerated_from_tree(self) -> None:
        fixture = self.add_fixture("enumerated")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        fixture.write("skills/survey/SKILL.md", "---\nname: survey\n---\n# Survey\n")
        fixture.write("skills/not-a-skill/notes.md", "no SKILL.md here\n")
        fixture.commit("add survey and a non-skill directory")

        result = install.run_installer("install")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            skills_dir = install.home / root / "skills"
            self.assertEqual(
                {path.name for path in skills_dir.iterdir()},
                {"orient", "reckon", "survey"},
            )

    def test_marker_records_managed_by_and_source_commit(self) -> None:
        fixture = self.add_fixture("traceable")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        sha = fixture.head_sha()
        for managed in [install.target(".claude", "orient"), install.runtime_root()]:
            marker = (managed / MARKER_NAME).read_text(encoding="utf-8")
            self.assertIn("managed-by=groundwork scripts/install\n", marker)
            self.assertIn(f"source-sha={sha}\n", marker)

    def test_invalid_corpus_config_halts_before_touching_targets(self) -> None:
        fixture = self.add_fixture("invalid-config")
        install = InstallRun(self, fixture.root)
        install.config_file().parent.mkdir(parents=True)
        install.config_file().write_text('[corpus]\nsource = "carrier-pigeon"\n', encoding="utf-8")

        result = install.run_installer("install")

        assert_failure_contains(self, result, "corpus")
        for surface in [".claude", ".agents", ".groundwork"]:
            self.assertFalse((install.home / surface).exists(), f"{surface} must be untouched")

    def test_unreachable_corpus_git_source_fails_loudly_without_target_mutation(self) -> None:
        fixture = self.add_fixture("unreachable-corpus")
        install = InstallRun(self, fixture.root)
        unreachable = self.make_corpus_repository("unreachable")
        url = f"file://{unreachable}"
        shutil.rmtree(unreachable)

        result = install.run_installer("install", "--corpus-git", url)

        assert_failure_contains(self, result, "cannot fetch corpus repository")
        for surface in [".claude", ".agents", ".groundwork"]:
            self.assertFalse((install.home / surface).exists(), f"{surface} must be untouched")
        self.assertEqual(
            list(install.home.glob(".groundwork.corpus.*")),
            [],
            "failed materialization must remove corpus staging directories",
        )

    def test_no_shell_startup_file_created_or_modified(self) -> None:
        fixture = self.add_fixture("no-startup-files")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertEqual(
            {path.name for path in install.home.iterdir()},
            {".claude", ".agents", ".groundwork"},
        )

    def test_marker_owned_entry_with_stale_state_sha_is_not_a_conflict(self) -> None:
        fixture = self.add_fixture("partial-failure-recovery")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        # Simulate a later run that updated the skill marker to a new
        # source-sha but failed before rewriting install.tsv: the marker and
        # the state row now disagree on the sha, though both are this
        # installer's own records.
        marker = install.target(".claude", "orient") / ".groundwork-managed"
        marker.write_text(
            marker.read_text(encoding="utf-8").replace(
                f"source-sha={fixture.head_sha()}", "source-sha=0" * 1
            ),
            encoding="utf-8",
        )
        stale = marker.read_text(encoding="utf-8")
        self.assertIn("source-sha=0\n", stale)

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertIn(
            f"source-sha={fixture.head_sha()}",
            (install.target(".claude", "orient") / ".groundwork-managed").read_text(encoding="utf-8"),
        )

    def test_rerun_restores_resolver_executable_bit(self) -> None:
        fixture = self.add_fixture("resolver-mode-drift")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        resolver = install.runtime_root() / "bin" / "groundwork-mechanic"
        resolver.chmod(0o644)
        self.assertFalse(os.access(resolver, os.X_OK))

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertTrue(os.access(resolver, os.X_OK), "rerun must restore the resolver executable bit")

    def test_state_lives_under_self_install_namespace_distinct_from_legacy(self) -> None:
        fixture = self.add_fixture("state-namespace")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install", include_state_dir=False)

        assert_success(self, result)
        self.assertTrue(
            (install.home / ".local" / "state" / "groundwork" / "install.tsv").is_file()
        )
        self.assertFalse((install.home / ".local" / "state" / "groundwork-install").exists())


if __name__ == "__main__":
    unittest.main()
