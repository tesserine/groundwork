import os
import shutil
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "groundwork-install"
HANDOFF_RELATIVE_PATH = "scripts/interactive-session-surface-handoff.md"
HANDOFF_BEGIN = "<!-- groundwork-install:interactive-session-surface-handoff begin -->"
HANDOFF_END = "<!-- groundwork-install:interactive-session-surface-handoff end -->"


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


class MethodologyFixture:
    def __init__(self, name: str) -> None:
        self.root = Path(tempfile.mkdtemp(prefix=f"groundwork-install-source-{name}-"))
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
        self.write(HANDOFF_RELATIVE_PATH, (ROOT / HANDOFF_RELATIVE_PATH).read_text(encoding="utf-8"))
        self.write("skills/orient/SKILL.md", "---\nname: orient\n---\n# Orient\n")
        self.write("skills/reckon/SKILL.md", "---\nname: reckon\n---\n# Reckon\n")
        self.write("skills/reckon/references/example.md", "reckon reference\n")
        self.write("protocols/take/PROTOCOL.md", "---\nname: take\n---\n# Take\n")
        self.write("protocols/take/references/example.md", "take reference\n")
        self.write("protocols/submit/PROTOCOL.md", "---\nname: submit\n---\n# Submit\n")

    def init_git(self) -> None:
        run(["git", "init", "-q"], self.root, check=True)
        run(["git", "config", "user.name", "installer test"], self.root, check=True)
        run(["git", "config", "user.email", "installer-test@example.invalid"], self.root, check=True)
        run(["git", "config", "commit.gpgsign", "false"], self.root, check=True)
        run(["git", "config", "tag.gpgsign", "false"], self.root, check=True)
        run(["git", "checkout", "-q", "-b", "main"], self.root, check=True)
        run(["git", "add", "."], self.root, check=True)
        run(["git", "commit", "-q", "-m", "test: seed methodology"], self.root, check=True)
        run(["git", "tag", "v1"], self.root, check=True)
        run(["git", "checkout", "-q", "--detach", "v1"], self.root, check=True)

    def commit_new_ref(self, tag: str) -> None:
        run(["git", "checkout", "-q", "main"], self.root, check=True)
        run(["git", "add", "."], self.root, check=True)
        run(["git", "commit", "-q", "-m", f"test: {tag}"], self.root, check=True)
        run(["git", "tag", tag], self.root, check=True)
        run(["git", "checkout", "-q", "--detach", tag], self.root, check=True)

    def checkout_branch(self) -> None:
        run(["git", "checkout", "-q", "main"], self.root, check=True)

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class InstallRun:
    def __init__(self, test: unittest.TestCase, source: Path) -> None:
        self.test = test
        self.source = source
        self.home = Path(tempfile.mkdtemp(prefix="groundwork-install-home-"))
        self.state = Path(tempfile.mkdtemp(prefix="groundwork-install-state-"))
        test.addCleanup(lambda: shutil.rmtree(self.home, ignore_errors=True))
        test.addCleanup(lambda: shutil.rmtree(self.state, ignore_errors=True))

    def run_installer(
        self,
        *args: str,
        include_state_dir: bool = True,
        env: dict[str, str] | None = None,
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
        return run(command, self.source, env=env)

    def target(self, root: str, name: str) -> Path:
        return self.home / root / "skills" / name

    def default_state_file(self) -> Path:
        return self.home / ".local" / "state" / "groundwork-install" / "interactive-install.tsv"

    def state_file(self) -> Path:
        return self.state / "interactive-install.tsv"

    def runtime_root(self) -> Path:
        return self.home / ".groundwork"


class GroundworkInstallTests(unittest.TestCase):
    def add_fixture(self, name: str) -> MethodologyFixture:
        fixture = MethodologyFixture(name)
        self.addCleanup(fixture.cleanup)
        return fixture

    def assert_installed_inventory(self, install: InstallRun, expected: set[str]) -> None:
        for root in [".claude", ".agents"]:
            skills_dir = install.home / root / "skills"
            self.assertEqual({path.name for path in skills_dir.iterdir()}, expected)
            for name in expected:
                entry = skills_dir / name
                self.assertTrue((entry / "SKILL.md").is_file(), entry)
                self.assertFalse((entry / "SKILL.md").is_symlink(), entry)
                self.assertTrue((entry / ".groundwork-install").is_file(), entry)

    def installed_entry_stats(self, install: InstallRun) -> dict[str, tuple[int, int]]:
        stats = {}
        for root in [".claude", ".agents"]:
            skills_dir = install.home / root / "skills"
            for entry in sorted(skills_dir.iterdir()):
                marker = entry / ".groundwork-install"
                stats[str(entry.relative_to(install.home))] = (
                    entry.stat().st_ino,
                    entry.stat().st_mtime_ns,
                )
                stats[str(marker.relative_to(install.home))] = (
                    marker.stat().st_ino,
                    marker.stat().st_mtime_ns,
                )
        return stats

    def handoff_text(self, fixture: MethodologyFixture) -> str:
        return (fixture.root / HANDOFF_RELATIVE_PATH).read_text(encoding="utf-8")

    def write_runtime_surface(self, fixture: MethodologyFixture) -> None:
        fixture.write(
            "manifest.toml",
            """
            [[capabilities]]
            name = "forge"
            version = "1.1.0"
            schema = "schemas/forge-capability-v1.schema.json"
            provenance = "schemas/forge-capability-v1.provenance.json"
            """,
        )
        fixture.write(
            "schemas/forge-capability-v1.schema.json",
            (ROOT / "schemas" / "forge-capability-v1.schema.json").read_text(encoding="utf-8"),
        )
        fixture.write(
            "schemas/forge-capability-v1.provenance.json",
            (ROOT / "schemas" / "forge-capability-v1.provenance.json").read_text(encoding="utf-8"),
        )

    def assert_handoff_projected_once(self, body: str) -> None:
        self.assertEqual(body.count(HANDOFF_BEGIN), 1)
        self.assertEqual(body.count(HANDOFF_END), 1)

    def test_install_projects_skills_and_protocols_into_both_discovery_roots(self) -> None:
        fixture = self.add_fixture("clean-install")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        self.assert_installed_inventory(install, {"orient", "reckon", "take", "submit"})
        take_body = (install.target(".claude", "take") / "SKILL.md").read_text(encoding="utf-8")
        self.assert_handoff_projected_once(take_body)
        self.assertTrue((install.target(".agents", "take") / "references" / "example.md").is_file())
        self.assertTrue((install.target(".agents", "reckon") / "references" / "example.md").is_file())

    def test_install_projects_runtime_bundle_with_capability_contract(self) -> None:
        fixture = self.add_fixture("runtime-bundle")
        self.write_runtime_surface(fixture)
        fixture.commit_new_ref("v2")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertEqual(
            (install.runtime_root() / "schemas" / "forge-capability-v1.schema.json").read_bytes(),
            (fixture.root / "schemas" / "forge-capability-v1.schema.json").read_bytes(),
        )
        self.assertFalse((install.runtime_root() / "bin" / "groundwork-mechanic").exists())

    def test_install_projects_session_surface_handoff_into_every_protocol_entry(self) -> None:
        fixture = self.add_fixture("handoff-all-protocols")
        producer_protocols = [
            "survey",
            "decompose",
            "take",
            "specify",
            "plan",
            "implement",
            "verify",
            "document",
            "submit",
            "land",
        ]
        for protocol in producer_protocols:
            fixture.write(
                f"protocols/{protocol}/PROTOCOL.md",
                f"""
                ---
                name: {protocol}
                ---
                # {protocol.title()}

                ## Procedures

                Follow the protocol.
                """,
            )
        fixture.commit_new_ref("v2")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        handoff = self.handoff_text(fixture)
        for root in [".claude", ".agents"]:
            for protocol in producer_protocols:
                body = (install.target(root, protocol) / "SKILL.md").read_text(encoding="utf-8")
                with self.subTest(root=root, protocol=protocol):
                    self.assert_handoff_projected_once(body)
                    self.assertIn(handoff, body)
                    self.assertLess(body.index("# "), body.index(HANDOFF_BEGIN))
                    self.assertLess(body.index(HANDOFF_END), body.index("## Procedures"))

    def test_install_projects_session_surface_handoff_into_every_real_protocol_entry(self) -> None:
        source = Path(tempfile.mkdtemp(prefix="groundwork-install-real-source-"))
        self.addCleanup(lambda: shutil.rmtree(source, ignore_errors=True))
        run(["git", "clone", "-q", str(ROOT), str(source)], ROOT, check=True)
        self.assertTrue((source / HANDOFF_RELATIVE_PATH).is_file())
        run(["git", "checkout", "-q", "--detach", "HEAD"], source, check=True)
        protocol_names = sorted(path.parent.name for path in source.glob("protocols/*/PROTOCOL.md"))
        self.assertNotEqual(protocol_names, [])
        install = InstallRun(self, source)

        result = install.run_installer("install")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            for protocol in protocol_names:
                body = (install.target(root, protocol) / "SKILL.md").read_text(encoding="utf-8")
                with self.subTest(root=root, protocol=protocol):
                    self.assert_handoff_projected_once(body)

    def test_install_does_not_project_session_surface_handoff_into_skill_entries(self) -> None:
        fixture = self.add_fixture("handoff-skills")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            for skill in ["orient", "reckon"]:
                body = (install.target(root, skill) / "SKILL.md").read_text(encoding="utf-8")
                with self.subTest(root=root, skill=skill):
                    self.assertNotIn(HANDOFF_BEGIN, body)
                    self.assertNotIn(HANDOFF_END, body)

    def test_session_surface_handoff_prose_carries_non_bypassing_commitments(self) -> None:
        fixture = self.add_fixture("handoff-prose")
        handoff = " ".join(self.handoff_text(fixture).split())

        for expected in [
            "`runa go --work-unit <canonical-work-unit-id>`",
            "operator issues only `go`",
            "`next-protocol-context`",
            "current output tool",
            "`advance`",
            "validated by runa",
            "Do not assemble artifact bodies manually",
            "Do not write workspace JSON files directly",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, handoff)

        for bypass_phrase in [
            "no runa runtime",
            "no artifact tool",
            "no artifact store",
            "Present that artifact body to the human",
            "does not persist artifacts",
        ]:
            with self.subTest(bypass_phrase=bypass_phrase):
                self.assertNotIn(bypass_phrase, handoff)

    def test_install_is_idempotent_for_the_same_pinned_source(self) -> None:
        fixture = self.add_fixture("idempotent")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        before = self.installed_entry_stats(install)

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertEqual(self.installed_entry_stats(install), before)
        self.assert_installed_inventory(install, {"orient", "reckon", "take", "submit"})

    def test_install_restores_same_sha_managed_target_drift(self) -> None:
        fixture = self.add_fixture("same-sha-drift")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        entry = install.target(".agents", "orient")
        skill = entry / "SKILL.md"
        expected = skill.read_text(encoding="utf-8")
        skill.write_text("# drifted\n", encoding="utf-8")
        (entry / "local-only.md").write_text("local drift\n", encoding="utf-8")

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertEqual(skill.read_text(encoding="utf-8"), expected)
        self.assertFalse((entry / "local-only.md").exists())
        self.assert_installed_inventory(install, {"orient", "reckon", "take", "submit"})

    def test_install_restores_state_recorded_target_when_marker_is_missing(self) -> None:
        fixture = self.add_fixture("missing-marker-drift")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        entry = install.target(".agents", "orient")
        skill = entry / "SKILL.md"
        expected = skill.read_text(encoding="utf-8")
        (entry / ".groundwork-install").unlink()
        skill.write_text("# drifted\n", encoding="utf-8")
        (entry / "local-only.md").write_text("local drift\n", encoding="utf-8")

        result = install.run_installer("install")

        assert_success(self, result)
        self.assertTrue((entry / ".groundwork-install").is_file())
        self.assertEqual(skill.read_text(encoding="utf-8"), expected)
        self.assertFalse((entry / "local-only.md").exists())
        self.assert_installed_inventory(install, {"orient", "reckon", "take", "submit"})

    def test_sync_converges_to_a_different_pinned_source_state(self) -> None:
        fixture = self.add_fixture("sync")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        fixture.remove("skills/reckon")
        fixture.write("protocols/verify/PROTOCOL.md", "---\nname: verify\n---\n# Verify\n")
        fixture.commit_new_ref("v2")

        result = install.run_installer("sync")

        assert_success(self, result)
        self.assert_installed_inventory(install, {"orient", "take", "submit", "verify"})
        self.assertFalse(install.target(".claude", "reckon").exists())

    def test_sync_upgrades_state_owned_entry_when_kind_changes(self) -> None:
        fixture = self.add_fixture("kind-change")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        fixture.remove("skills/orient")
        fixture.write("protocols/orient/PROTOCOL.md", "---\nname: orient\n---\n# Orient Protocol\n")
        fixture.commit_new_ref("v2")

        result = install.run_installer("sync")

        assert_success(self, result)
        orient_body = (install.target(".agents", "orient") / "SKILL.md").read_text(encoding="utf-8")
        self.assert_handoff_projected_once(orient_body)
        self.assertIn("kind=protocol\n", (install.target(".agents", "orient") / ".groundwork-install").read_text(encoding="utf-8"))
        self.assertIn("\torient\tprotocol\t", install.state_file().read_text(encoding="utf-8"))

    def test_sync_fails_and_retains_state_when_obsolete_entry_is_missing_marker(self) -> None:
        fixture = self.add_fixture("obsolete-missing-marker")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        (install.target(".agents", "reckon") / ".groundwork-install").unlink()
        before_state = install.state_file().read_text(encoding="utf-8")
        fixture.remove("skills/reckon")
        fixture.commit_new_ref("v2")

        result = install.run_installer("sync")

        assert_failure_contains(self, result, "missing marker")
        self.assertTrue(install.target(".claude", "reckon").is_dir())
        self.assertTrue(install.target(".agents", "reckon").is_dir())
        self.assertEqual(install.state_file().read_text(encoding="utf-8"), before_state)

    def test_sync_fails_and_preserves_drift_when_obsolete_entry_is_missing_marker(self) -> None:
        fixture = self.add_fixture("obsolete-missing-marker-drift")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        agents_entry = install.target(".agents", "reckon")
        (agents_entry / ".groundwork-install").unlink()
        (agents_entry / "SKILL.md").write_text("# local drift\n", encoding="utf-8")
        before_state = install.state_file().read_text(encoding="utf-8")
        fixture.remove("skills/reckon")
        fixture.commit_new_ref("v2")

        result = install.run_installer("sync")

        assert_failure_contains(self, result, "missing marker")
        self.assertTrue(install.target(".claude", "reckon").is_dir())
        self.assertEqual((agents_entry / "SKILL.md").read_text(encoding="utf-8"), "# local drift\n")
        self.assertEqual(install.state_file().read_text(encoding="utf-8"), before_state)

    def test_sync_refreshes_stale_sha_metadata_without_rewriting_matching_payload(self) -> None:
        fixture = self.add_fixture("stale-sha-matching-payload")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        entry = install.target(".agents", "orient")
        payload = entry / "SKILL.md"
        before_entry_stat = (entry.stat().st_ino, entry.stat().st_mtime_ns)
        before_payload_stat = (payload.stat().st_ino, payload.stat().st_mtime_ns)
        fixture.write("README.md", "source-only change\n")
        fixture.commit_new_ref("v2")
        new_sha = run(["git", "rev-parse", "HEAD"], fixture.root, check=True).stdout.strip()

        result = install.run_installer("sync")

        assert_success(self, result)
        self.assertEqual((entry.stat().st_ino, entry.stat().st_mtime_ns), before_entry_stat)
        self.assertEqual((payload.stat().st_ino, payload.stat().st_mtime_ns), before_payload_stat)
        self.assertIn(f"source-sha={new_sha}\n", (entry / ".groundwork-install").read_text(encoding="utf-8"))
        self.assertIn(new_sha, install.state_file().read_text(encoding="utf-8"))

    def test_uninstall_removes_only_entries_owned_by_groundwork_install(self) -> None:
        fixture = self.add_fixture("uninstall")
        install = InstallRun(self, fixture.root)
        unrelated = install.home / ".agents" / "skills" / "operator"
        unrelated.mkdir(parents=True)
        (unrelated / "SKILL.md").write_text("# Operator\n", encoding="utf-8")
        assert_success(self, install.run_installer("install"))

        result = install.run_installer("uninstall")

        assert_success(self, result)
        self.assertTrue((unrelated / "SKILL.md").is_file())
        self.assertFalse(install.target(".agents", "orient").exists())
        self.assertFalse(install.target(".claude", "take").exists())

    def test_uninstall_fails_and_retains_state_when_managed_entry_is_missing_marker(self) -> None:
        fixture = self.add_fixture("uninstall-missing-marker")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        (install.target(".agents", "orient") / ".groundwork-install").unlink()
        before_state = install.state_file().read_text(encoding="utf-8")

        result = install.run_installer("uninstall")

        assert_failure_contains(self, result, "missing marker")
        self.assertTrue(install.target(".claude", "orient").is_dir())
        self.assertTrue(install.target(".agents", "orient").is_dir())
        self.assertEqual(install.state_file().read_text(encoding="utf-8"), before_state)

    def test_install_rejects_unmanaged_conflicts_before_changing_targets(self) -> None:
        fixture = self.add_fixture("conflict")
        install = InstallRun(self, fixture.root)
        conflict = install.home / ".claude" / "skills" / "orient"
        conflict.mkdir(parents=True)
        (conflict / "SKILL.md").write_text("# Mine\n", encoding="utf-8")

        result = install.run_installer("install")

        assert_failure_contains(self, result, "unmanaged conflict")
        self.assertEqual((conflict / "SKILL.md").read_text(encoding="utf-8"), "# Mine\n")
        self.assertFalse((install.home / ".agents" / "skills" / "take").exists())

    def test_install_rejects_marker_only_targets_as_unmanaged_conflicts(self) -> None:
        fixture = self.add_fixture("marker-only-conflict")
        install = InstallRun(self, fixture.root)
        conflict = install.target(".claude", "orient")
        conflict.mkdir(parents=True)
        (conflict / "SKILL.md").write_text("# Mine\n", encoding="utf-8")
        (conflict / ".groundwork-install").write_text("managed-by=groundwork-install\n", encoding="utf-8")

        result = install.run_installer("install")

        assert_failure_contains(self, result, "unmanaged conflict")
        self.assertEqual((conflict / "SKILL.md").read_text(encoding="utf-8"), "# Mine\n")
        self.assertFalse((install.home / ".agents" / "skills" / "take").exists())
        self.assertFalse(install.state_file().exists())

    def test_install_rejects_unmanaged_runtime_conflict_before_replacing_it(self) -> None:
        fixture = self.add_fixture("runtime-conflict")
        self.write_runtime_surface(fixture)
        fixture.commit_new_ref("v2")
        install = InstallRun(self, fixture.root)
        runtime = install.runtime_root()
        runtime.mkdir()
        local_file = runtime / "operator-data.txt"
        local_file.write_text("keep me\n", encoding="utf-8")

        result = install.run_installer("install")

        assert_failure_contains(self, result, "unmanaged conflict")
        self.assertEqual(local_file.read_text(encoding="utf-8"), "keep me\n")
        self.assertFalse((runtime / "schemas" / "forge-capability-v1.schema.json").exists())
        self.assertFalse(install.state_file().exists())

    def test_install_fails_without_writing_entries_when_any_target_root_is_not_preparable(self) -> None:
        fixture = self.add_fixture("target-root-file")
        install = InstallRun(self, fixture.root)
        first_root = install.home / ".claude" / "skills"
        first_root.mkdir(parents=True)
        before_first_root = sorted(path.name for path in first_root.iterdir())
        blocked_root = install.home / ".agents" / "skills"
        blocked_root.parent.mkdir(parents=True)
        blocked_root.write_text("not a directory\n", encoding="utf-8")

        result = install.run_installer("install")

        self.assertNotEqual(result.returncode, 0, "command unexpectedly succeeded")
        self.assertEqual(sorted(path.name for path in first_root.iterdir()), before_first_root)
        self.assertEqual(blocked_root.read_text(encoding="utf-8"), "not a directory\n")
        self.assertFalse(install.state_file().exists())

    def test_install_rejects_branch_checkouts(self) -> None:
        fixture = self.add_fixture("branch")
        fixture.checkout_branch()
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_failure_contains(self, result, "pinned checkout")

    def test_install_rejects_dirty_source_checkouts(self) -> None:
        fixture = self.add_fixture("dirty")
        fixture.write("skills/orient/SKILL.md", "# changed\n")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_failure_contains(self, result, "dirty")

    def test_install_from_branch_installs_committed_branch_head(self) -> None:
        fixture = self.add_fixture("from-branch")
        fixture.checkout_branch()
        expected_sha = run(["git", "rev-parse", "HEAD"], fixture.root, check=True).stdout.strip()
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install", "--from-branch")

        assert_success(self, result)
        self.assert_installed_inventory(install, {"orient", "reckon", "take", "submit"})
        recorded = {
            line.split("\t")[3]
            for line in install.state_file().read_text(encoding="utf-8").splitlines()
        }
        self.assertEqual(recorded, {expected_sha})

    def test_sync_from_branch_converges_to_the_moving_branch_head(self) -> None:
        fixture = self.add_fixture("sync-from-branch")
        fixture.checkout_branch()
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install", "--from-branch"))

        fixture.write("skills/added/SKILL.md", "---\nname: added\n---\n# Added\n")
        run(["git", "add", "."], fixture.root, check=True)
        run(["git", "commit", "-q", "-m", "test: advance branch"], fixture.root, check=True)
        advanced_sha = run(["git", "rev-parse", "HEAD"], fixture.root, check=True).stdout.strip()

        result = install.run_installer("sync", "--from-branch")

        assert_success(self, result)
        self.assert_installed_inventory(install, {"orient", "reckon", "take", "submit", "added"})
        recorded = {
            line.split("\t")[3]
            for line in install.state_file().read_text(encoding="utf-8").splitlines()
        }
        self.assertEqual(recorded, {advanced_sha})

    def test_from_branch_does_not_bypass_dirty_source_checkouts(self) -> None:
        fixture = self.add_fixture("from-branch-dirty")
        fixture.checkout_branch()
        fixture.write("skills/orient/SKILL.md", "# changed\n")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install", "--from-branch")

        assert_failure_contains(self, result, "dirty")

    def test_install_omits_ignored_files_inside_entry_directories(self) -> None:
        fixture = self.add_fixture("ignored-entry-files")
        fixture.write(".gitignore", "*.swp\n")
        fixture.commit_new_ref("v2")
        fixture.write("skills/orient/local.swp", "ignored skill artifact\n")
        fixture.write("protocols/take/local.swp", "ignored protocol artifact\n")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        for root in [".claude", ".agents"]:
            self.assertFalse((install.target(root, "orient") / "local.swp").exists())
            self.assertFalse((install.target(root, "take") / "local.swp").exists())

    def test_install_omits_ignored_top_level_files_under_skills(self) -> None:
        fixture = self.add_fixture("ignored-top-level-skill-files")
        fixture.write(".gitignore", "*.swp\n")
        fixture.commit_new_ref("v2")
        fixture.write("skills/local.swp", "ignored top-level artifact\n")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("install")

        assert_success(self, result)
        self.assert_installed_inventory(install, {"orient", "reckon", "take", "submit"})
        for root in [".claude", ".agents"]:
            self.assertFalse((install.home / root / "skills" / "local.swp").exists())

    def test_status_reports_missing_install_state_without_modifying_targets(self) -> None:
        fixture = self.add_fixture("status-empty")
        install = InstallRun(self, fixture.root)

        result = install.run_installer("status")

        assert_failure_contains(self, result, "not installed")
        self.assertFalse((install.home / ".agents").exists())

    def test_status_fails_when_expected_managed_runtime_is_absent(self) -> None:
        fixture = self.add_fixture("status-missing-runtime")
        self.write_runtime_surface(fixture)
        fixture.commit_new_ref("v2")
        install = InstallRun(self, fixture.root)
        assert_success(self, install.run_installer("install"))
        shutil.rmtree(install.runtime_root())

        result = install.run_installer("status")

        assert_failure_contains(self, result, "missing managed runtime")

    def test_home_option_supplies_default_state_dir_when_home_environment_is_unset(self) -> None:
        fixture = self.add_fixture("unset-home")
        install = InstallRun(self, fixture.root)
        env = os.environ.copy()
        env.pop("HOME", None)
        env.pop("XDG_STATE_HOME", None)

        install_result = install.run_installer("install", include_state_dir=False, env=env)

        assert_success(self, install_result)
        self.assertTrue(install.default_state_file().is_file())
        status_result = install.run_installer("status", include_state_dir=False, env=env)
        assert_success(self, status_result)
        uninstall_result = install.run_installer("uninstall", include_state_dir=False, env=env)
        assert_success(self, uninstall_result)
        self.assertFalse(install.default_state_file().exists())
        self.assertFalse(install.target(".agents", "orient").exists())

    def write_principles_surface(self, fixture: MethodologyFixture) -> None:
        self.write_runtime_surface(fixture)
        fixture.write(
            "principles/PRINCIPLES.md",
            """
            # Default Principles

            1. **Check.** Verify claims against reality.
            """,
        )
        for module in ["corpus_resolution.py", "principles_config.py"]:
            fixture.write(f"tooling/{module}", (ROOT / "tooling" / module).read_text(encoding="utf-8"))
        fixture.write(
            "schemas/principles-config.schema.json",
            (ROOT / "schemas" / "principles-config.schema.json").read_text(encoding="utf-8"),
        )

    def corpus_env(self, config_home: Path) -> dict[str, str]:
        return {**os.environ, "XDG_CONFIG_HOME": str(config_home)}

    def test_install_materializes_embedded_corpus_offline_with_no_configuration(self) -> None:
        fixture = self.add_fixture("corpus-embedded-default")
        self.write_principles_surface(fixture)
        fixture.commit_new_ref("v2")
        install = InstallRun(self, fixture.root)
        config_home = install.home / ".config"

        result = install.run_installer("install", env=self.corpus_env(config_home))

        assert_success(self, result)
        resolved = install.runtime_root() / "principles" / "PRINCIPLES.md"
        self.assertTrue(resolved.is_file())
        self.assertIn("Default Principles", resolved.read_text(encoding="utf-8"))

    def test_install_materializes_a_configured_external_corpus(self) -> None:
        fixture = self.add_fixture("corpus-configured-path")
        self.write_principles_surface(fixture)
        fixture.commit_new_ref("v2")
        install = InstallRun(self, fixture.root)
        external = install.home / "external-corpus"
        external.mkdir(parents=True)
        (external / "README.md").write_text("# External Corpus\n", encoding="utf-8")
        config_home = install.home / ".config"
        config_file = config_home / "groundwork" / "principles.toml"
        config_file.parent.mkdir(parents=True)
        config_file.write_text(f'[corpus]\nsource = "path"\npath = "{external}"\n', encoding="utf-8")

        result = install.run_installer("install", env=self.corpus_env(config_home))

        assert_success(self, result)
        resolved = install.runtime_root() / "principles"
        self.assertTrue((resolved / "README.md").is_file())
        self.assertFalse((resolved / "PRINCIPLES.md").exists())

    def test_install_fails_loudly_when_the_configured_remote_is_unreachable(self) -> None:
        fixture = self.add_fixture("corpus-unreachable-remote")
        self.write_principles_surface(fixture)
        fixture.commit_new_ref("v2")
        install = InstallRun(self, fixture.root)
        config_home = install.home / ".config"
        config_file = config_home / "groundwork" / "principles.toml"
        config_file.parent.mkdir(parents=True)
        missing = install.home / "no-such-repo"
        config_file.write_text(f'[corpus]\nsource = "git"\nurl = "{missing}"\n', encoding="utf-8")

        result = install.run_installer("install", env=self.corpus_env(config_home))

        assert_failure_contains(self, result, "principles-corpus resolution failed")

    def test_install_fails_in_preflight_before_projecting_when_config_is_invalid(self) -> None:
        fixture = self.add_fixture("corpus-invalid-config")
        self.write_principles_surface(fixture)
        fixture.commit_new_ref("v2")
        install = InstallRun(self, fixture.root)
        config_home = install.home / ".config"
        config_file = config_home / "groundwork" / "principles.toml"
        config_file.parent.mkdir(parents=True)
        config_file.write_text('[corpus]\nsource = "carrier-pigeon"\n', encoding="utf-8")

        result = install.run_installer("install", env=self.corpus_env(config_home))

        assert_failure_contains(self, result, "principles-corpus configuration is not resolvable")
        self.assertFalse(install.runtime_root().exists())
        for root in [".claude", ".agents"]:
            skills_dir = install.home / root / "skills"
            self.assertEqual([], list(skills_dir.iterdir()) if skills_dir.exists() else [])

    def test_sync_refreshes_the_resolved_corpus(self) -> None:
        fixture = self.add_fixture("corpus-sync-refresh")
        self.write_principles_surface(fixture)
        fixture.commit_new_ref("v2")
        install = InstallRun(self, fixture.root)
        config_home = install.home / ".config"
        assert_success(self, install.run_installer("install", env=self.corpus_env(config_home)))
        resolved = install.runtime_root() / "principles" / "PRINCIPLES.md"
        resolved.write_text("# Drifted\n", encoding="utf-8")

        result = install.run_installer("sync", env=self.corpus_env(config_home))

        assert_success(self, result)
        self.assertIn("Default Principles", resolved.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
