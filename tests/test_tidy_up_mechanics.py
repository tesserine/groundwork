import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIDY_UP = ROOT / "skills" / "tidy-up" / "scripts" / "tidy_up.py"


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}")
    return result


def run_tidy(repo: Path, kind: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TIDY_UP), kind],
        cwd=repo,
        capture_output=True,
        text=True,
    )


def branch(repo: Path) -> str:
    return git(repo, "branch", "--show-current").stdout.strip()


def porcelain(repo: Path) -> str:
    return git(repo, "status", "--porcelain").stdout.strip()


class GitFixture:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.origin = root / "origin.git"
        self.seed = root / "seed"
        self.repo = root / "repo"
        self.run_branch = "issue-518/tidy-up"
        self.ignored = self.repo / "ignored.log"

        git(root, "init", "--bare", str(self.origin))
        self.seed.mkdir()
        git(self.seed, "init", "-b", "main")
        self.configure_identity(self.seed)
        (self.seed / ".gitignore").write_text("ignored.log\n", encoding="utf-8")
        (self.seed / "tracked.txt").write_text("base\n", encoding="utf-8")
        git(self.seed, "add", ".")
        git(self.seed, "commit", "-m", "initial")
        git(self.seed, "remote", "add", "origin", str(self.origin))
        git(self.seed, "push", "-u", "origin", "main")
        git(self.origin, "symbolic-ref", "HEAD", "refs/heads/main")
        git(root, "clone", str(self.origin), str(self.repo))
        self.configure_identity(self.repo)
        git(self.repo, "remote", "set-head", "origin", "-a")

    @staticmethod
    def configure_identity(repo: Path) -> None:
        git(repo, "config", "user.name", "Groundwork Test")
        git(repo, "config", "user.email", "groundwork-test@example.invalid")

    def checkout_run_branch(self) -> None:
        git(self.repo, "checkout", "-b", self.run_branch)

    def seed_common_residue(self) -> None:
        (self.repo / "tracked.txt").write_text("dirty tracked edit\n", encoding="utf-8")
        (self.repo / "build.tmp").write_text("run build artifact\n", encoding="utf-8")
        self.ignored.write_text("ignored survivor\n", encoding="utf-8")

    def create_landed_state(self) -> str:
        self.checkout_run_branch()
        landed = self.repo / "landed.txt"
        landed.write_text("landed content\n", encoding="utf-8")
        git(self.repo, "add", "landed.txt")
        git(self.repo, "commit", "-m", "landed change")
        git(self.repo, "checkout", "main")
        git(self.repo, "merge", "--ff-only", self.run_branch)
        git(self.repo, "push", "origin", "main")
        git(self.repo, "checkout", self.run_branch)
        self.seed_common_residue()
        return git(self.repo, "show", "HEAD:landed.txt").stdout


class TidyUpMechanicsTests(unittest.TestCase):
    def test_land_reaches_canonical_clean_preserving_landed_work_and_ignored_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GitFixture(Path(tmp))
            landed_before = fixture.create_landed_state()

            result = run_tidy(fixture.repo, "land")

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("", porcelain(fixture.repo))
            self.assertEqual("main", branch(fixture.repo))
            self.assertEqual(landed_before, git(fixture.repo, "show", "HEAD:landed.txt").stdout)
            self.assertFalse((fixture.repo / "build.tmp").exists())
            self.assertTrue(fixture.ignored.exists())
            self.assertNotEqual(
                0,
                git(fixture.repo, "show-ref", "--verify", f"refs/heads/{fixture.run_branch}", check=False).returncode,
            )

    def test_abandon_reaches_canonical_clean_and_removes_run_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GitFixture(Path(tmp))
            fixture.checkout_run_branch()
            (fixture.repo / "unlanded.txt").write_text("unlanded\n", encoding="utf-8")
            git(fixture.repo, "add", "unlanded.txt")
            git(fixture.repo, "commit", "-m", "unlanded work")
            fixture.seed_common_residue()

            result = run_tidy(fixture.repo, "abandon")

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("", porcelain(fixture.repo))
            self.assertEqual("main", branch(fixture.repo))
            self.assertFalse((fixture.repo / "build.tmp").exists())
            self.assertTrue(fixture.ignored.exists())
            self.assertNotIn("unlanded.txt", git(fixture.repo, "ls-tree", "--name-only", "HEAD").stdout)
            self.assertNotEqual(
                0,
                git(fixture.repo, "show-ref", "--verify", f"refs/heads/{fixture.run_branch}", check=False).returncode,
            )

    def test_halt_preserves_wip_commit_on_run_branch_and_returns_to_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GitFixture(Path(tmp))
            fixture.checkout_run_branch()
            fixture.seed_common_residue()

            result = run_tidy(fixture.repo, "halt")

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("", porcelain(fixture.repo))
            self.assertEqual("main", branch(fixture.repo))
            self.assertTrue(fixture.ignored.exists())
            self.assertEqual(
                "dirty tracked edit\n",
                git(fixture.repo, "show", f"{fixture.run_branch}:tracked.txt").stdout,
            )
            self.assertEqual(
                "run build artifact\n",
                git(fixture.repo, "show", f"{fixture.run_branch}:build.tmp").stdout,
            )
            self.assertIn(
                "halt: preserve work-in-progress",
                git(fixture.repo, "log", "-1", "--pretty=%s", fixture.run_branch).stdout,
            )

    def test_verify_fails_loudly_with_named_residual_on_dirty_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            fixture = GitFixture(Path(tmp))
            (fixture.repo / "dirty.tmp").write_text("dirty\n", encoding="utf-8")

            result = run_tidy(fixture.repo, "verify")

            self.assertNotEqual(0, result.returncode)
            self.assertIn("canonical-clean residual", result.stderr)
            self.assertIn("working tree is not porcelain-clean", result.stderr)


if __name__ == "__main__":
    unittest.main()
