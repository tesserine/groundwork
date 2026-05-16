import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMAND = ROOT / "scripts" / "groundwork-sync"


def run(
    args: list[str],
    cwd: Path,
    *,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(
        args,
        cwd=cwd,
        env=merged_env,
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
    test.assertEqual(
        result.returncode,
        0,
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
    )


def assert_failure_contains(
    test: unittest.TestCase,
    result: subprocess.CompletedProcess[str],
    expected: str,
) -> None:
    test.assertNotEqual(result.returncode, 0, f"command unexpectedly succeeded\n{result.stdout}")
    test.assertIn(expected, result.stderr)


class GroundworkFixture:
    def __init__(self, name: str) -> None:
        self.root = Path(tempfile.mkdtemp(prefix=f"groundwork-sync-source-{name}-"))
        self.home = Path(tempfile.mkdtemp(prefix=f"groundwork-sync-home-{name}-"))
        self.state = Path(tempfile.mkdtemp(prefix=f"groundwork-sync-state-{name}-"))
        self.write("skills/orient/SKILL.md", "# Orient\n")
        self.write("skills/debug/SKILL.md", "# Debug\n")
        self.write("protocols/take/PROTOCOL.md", "# Take\n")
        self.write("protocols/plan/PROTOCOL.md", "# Plan\n")
        self.init_git()

    def write(self, relative: str, contents: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")

    def init_git(self) -> None:
        run(["git", "init", "-q"], self.root, check=True)
        run(["git", "config", "user.name", "sync test"], self.root, check=True)
        run(["git", "config", "user.email", "sync-test@example.invalid"], self.root, check=True)
        run(["git", "checkout", "-q", "-b", "main"], self.root, check=True)
        run(["git", "add", "."], self.root, check=True)
        run(["git", "commit", "-q", "-m", "test: seed methodology"], self.root, check=True)
        sha = run(["git", "rev-parse", "HEAD"], self.root, check=True).stdout.strip()
        run(["git", "checkout", "-q", "--detach", sha], self.root, check=True)

    def commit_detached(self, message: str) -> str:
        run(["git", "add", "."], self.root, check=True)
        run(["git", "commit", "-q", "-m", message], self.root, check=True)
        return run(["git", "rev-parse", "HEAD"], self.root, check=True).stdout.strip()

    def current_commit(self) -> str:
        return run(["git", "rev-parse", "HEAD"], self.root, check=True).stdout.strip()

    def remove(self, relative: str) -> None:
        path = self.root / relative
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def install(self) -> subprocess.CompletedProcess[str]:
        return run(
            [
                str(COMMAND),
                "install",
                "--source",
                str(self.root),
                "--home",
                str(self.home),
                "--state-dir",
                str(self.state),
            ],
            self.root,
        )

    def uninstall(self) -> subprocess.CompletedProcess[str]:
        return run(
            [
                str(COMMAND),
                "uninstall",
                "--home",
                str(self.home),
                "--state-dir",
                str(self.state),
            ],
            self.root,
        )

    def target_snapshot(self) -> dict[str, str]:
        snapshot = {}
        for root in [self.home / ".claude" / "skills", self.home / ".agents" / "skills"]:
            if not root.exists():
                continue
            for entry in sorted(root.iterdir()):
                relative = entry.relative_to(self.home).as_posix()
                snapshot[relative] = os.readlink(entry) if entry.is_symlink() else "<not-symlink>"
        state_file = self.state / "state-v1.tsv"
        if state_file.exists():
            snapshot["state-v1.tsv"] = state_file.read_text(encoding="utf-8")
        return snapshot

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.home, ignore_errors=True)
        shutil.rmtree(self.state, ignore_errors=True)


class GroundworkSyncTests(unittest.TestCase):
    def add_fixture(self, name: str) -> GroundworkFixture:
        fixture = GroundworkFixture(name)
        self.addCleanup(fixture.cleanup)
        return fixture

    def test_clean_pinned_install_creates_discoverable_skill_and_protocol_entries(self) -> None:
        fixture = self.add_fixture("clean-install")

        result = fixture.install()

        assert_success(self, result)
        for target in [fixture.home / ".claude" / "skills", fixture.home / ".agents" / "skills"]:
            for name in ["orient", "debug", "take", "plan"]:
                entry = target / name
                self.assertTrue(entry.is_symlink(), f"{entry} should be a symlinked entry directory")
                skill_file = entry / "SKILL.md"
                self.assertTrue(skill_file.is_file(), f"{skill_file} should be discoverable")
                self.assertFalse(skill_file.is_symlink(), f"{skill_file} should be a real file")

        take_skill = fixture.home / ".agents" / "skills" / "take" / "SKILL.md"
        self.assertEqual(take_skill.read_text(encoding="utf-8"), "# Take\n")
        take_entry = fixture.home / ".agents" / "skills" / "take"
        expected_take_target = (
            fixture.state / "snapshots" / fixture.current_commit() / "source" / "protocols" / "take"
        )
        self.assertEqual(take_entry.resolve(), expected_take_target)
        state = (fixture.state / "state-v1.tsv").read_text(encoding="utf-8")
        self.assertIn("\t.claude/skills\torient\t", state)
        self.assertIn("\t.agents/skills\ttake\t", state)
        self.assertIn(str(expected_take_target), state)
        self.assertNotIn("/projections/", state)

    def test_reinstalling_same_source_state_is_idempotent(self) -> None:
        fixture = self.add_fixture("idempotent")
        assert_success(self, fixture.install())
        before = fixture.target_snapshot()

        result = fixture.install()

        assert_success(self, result)
        self.assertEqual(fixture.target_snapshot(), before)

    def test_installed_entries_do_not_drift_when_source_checkout_changes(self) -> None:
        fixture = self.add_fixture("drift-free")
        assert_success(self, fixture.install())
        installed = fixture.home / ".agents" / "skills" / "orient" / "SKILL.md"

        fixture.write("skills/orient/SKILL.md", "# Mutated orient\n")

        self.assertEqual(installed.read_text(encoding="utf-8"), "# Orient\n")

    def test_installed_protocol_relative_paths_resolve_to_source_content(self) -> None:
        fixture = self.add_fixture("protocol-relative-paths")
        fixture.write("docs/architecture/work-unit-model.md", "# Work unit model\n")
        fixture.write("schemas/work-unit.schema.json", '{"title": "Work unit"}\n')
        fixture.write("manifest.toml", 'name = "groundwork-test"\n')
        fixture.write(
            "protocols/take/PROTOCOL.md",
            """
            # Take

            Read [work-unit model](../../docs/architecture/work-unit-model.md).
            Validate against [schema](../../schemas/work-unit.schema.json).
            Coordinate with [orient](../../skills/orient/SKILL.md).
            Check [manifest](../../manifest.toml).
            """,
        )
        fixture.commit_detached("test: add protocol references")

        result = fixture.install()

        assert_success(self, result)
        installed_protocol = (fixture.home / ".agents" / "skills" / "take").resolve()
        installed_skill = installed_protocol / "SKILL.md"
        self.assertEqual(
            installed_skill.read_text(encoding="utf-8"),
            (fixture.root / "protocols" / "take" / "PROTOCOL.md").read_text(encoding="utf-8"),
        )
        for relative in [
            "../../docs/architecture/work-unit-model.md",
            "../../schemas/work-unit.schema.json",
            "../../skills/orient/SKILL.md",
            "../../manifest.toml",
        ]:
            installed_reference = (installed_skill.parent / relative).resolve()
            source_reference = (fixture.root / "protocols" / "take" / relative).resolve()
            self.assertTrue(
                installed_reference.is_file(),
                f"{relative} should resolve from the installed protocol",
            )
            self.assertEqual(
                installed_reference.read_text(encoding="utf-8"),
                source_reference.read_text(encoding="utf-8"),
                f"{relative} should resolve to the pinned source content",
            )

    def test_install_replaces_recorded_projection_target_with_source_shaped_target(self) -> None:
        fixture = self.add_fixture("projection-migration")
        commit = fixture.current_commit()
        old_projection = fixture.state / "projections" / commit / "take"
        old_projection.mkdir(parents=True)
        (old_projection / "SKILL.md").write_text("# Take\n", encoding="utf-8")
        managed = fixture.home / ".agents" / "skills" / "take"
        managed.parent.mkdir(parents=True)
        managed.symlink_to(old_projection)
        (fixture.state / "state-v1.tsv").write_text(
            f"{commit}\t.agents/skills\ttake\tprotocol\t{managed}\t{old_projection}\n",
            encoding="utf-8",
        )

        result = fixture.install()

        assert_success(self, result)
        expected = fixture.state / "snapshots" / commit / "source" / "protocols" / "take"
        self.assertEqual(managed.resolve(), expected)
        self.assertFalse(old_projection.exists())
        state = (fixture.state / "state-v1.tsv").read_text(encoding="utf-8")
        self.assertIn(f"\t.agents/skills\ttake\tprotocol\t{managed}\t{expected}", state)
        self.assertNotIn("/projections/", state)

    def test_reinstalling_new_pinned_ref_adds_and_removes_entries(self) -> None:
        fixture = self.add_fixture("sync-new-ref")
        assert_success(self, fixture.install())
        fixture.write("skills/research/SKILL.md", "# Research\n")
        fixture.remove("protocols/plan")
        new_sha = fixture.commit_detached("test: update methodology")

        result = fixture.install()

        assert_success(self, result)
        self.assertTrue((fixture.home / ".agents" / "skills" / "research" / "SKILL.md").is_file())
        self.assertFalse((fixture.home / ".agents" / "skills" / "plan").exists())
        state = (fixture.state / "state-v1.tsv").read_text(encoding="utf-8")
        self.assertIn(new_sha, state)
        self.assertNotIn("\t.agents/skills\tplan\t", state)

    def test_reinstall_refuses_tampered_stale_managed_entry(self) -> None:
        fixture = self.add_fixture("tampered-stale")
        assert_success(self, fixture.install())
        managed = fixture.home / ".agents" / "skills" / "plan"
        managed.unlink()
        managed.mkdir()
        (managed / "SKILL.md").write_text("# Operator replacement\n", encoding="utf-8")
        fixture.remove("protocols/plan")
        fixture.commit_detached("test: remove plan")

        result = fixture.install()

        assert_failure_contains(self, result, "managed entry was modified")
        self.assertTrue((managed / "SKILL.md").is_file())

    def test_uninstall_removes_only_recorded_entries(self) -> None:
        fixture = self.add_fixture("uninstall")
        operator_entry = fixture.home / ".agents" / "skills" / "operator"
        operator_entry.mkdir(parents=True)
        (operator_entry / "SKILL.md").write_text("# Operator\n", encoding="utf-8")
        assert_success(self, fixture.install())

        result = fixture.uninstall()

        assert_success(self, result)
        self.assertFalse((fixture.home / ".agents" / "skills" / "orient").exists())
        self.assertFalse((fixture.home / ".claude" / "skills" / "take").exists())
        self.assertTrue((operator_entry / "SKILL.md").is_file())

    def test_uninstall_refuses_modified_managed_entries(self) -> None:
        fixture = self.add_fixture("tampered-uninstall")
        assert_success(self, fixture.install())
        managed = fixture.home / ".agents" / "skills" / "orient"
        managed.unlink()
        managed.mkdir()
        (managed / "SKILL.md").write_text("# Operator replacement\n", encoding="utf-8")

        result = fixture.uninstall()

        assert_failure_contains(self, result, "managed entry was modified")
        self.assertTrue((managed / "SKILL.md").is_file())

    def test_install_rejects_branch_checkout(self) -> None:
        fixture = self.add_fixture("branch-source")
        run(["git", "checkout", "-q", "main"], fixture.root, check=True)

        result = fixture.install()

        assert_failure_contains(self, result, "source must be a detached checkout")

    def test_install_rejects_dirty_checkout(self) -> None:
        fixture = self.add_fixture("dirty-source")
        fixture.write("skills/orient/notes.md", "dirty\n")

        result = fixture.install()

        assert_failure_contains(self, result, "source checkout must be clean")

    def test_install_rejects_duplicate_skill_and_protocol_names(self) -> None:
        fixture = self.add_fixture("duplicate-names")
        fixture.write("protocols/orient/PROTOCOL.md", "# Orient protocol\n")
        fixture.commit_detached("test: duplicate name")

        result = fixture.install()

        assert_failure_contains(self, result, "duplicate skill/protocol name: orient")

    def test_install_rejects_unmanaged_entry_conflict(self) -> None:
        fixture = self.add_fixture("unmanaged-conflict")
        conflict = fixture.home / ".claude" / "skills" / "orient"
        conflict.mkdir(parents=True)
        (conflict / "SKILL.md").write_text("# Local orient\n", encoding="utf-8")

        result = fixture.install()

        assert_failure_contains(self, result, "existing unmanaged entry conflicts")


if __name__ == "__main__":
    unittest.main()
