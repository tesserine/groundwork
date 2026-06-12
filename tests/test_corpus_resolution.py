import subprocess
import tempfile
import unittest
from pathlib import Path

from tooling.corpus_resolution import (
    CorpusResolutionError,
    check_resolvable,
    corpus_index,
    main,
    materialize,
)
from tooling.principles_config import PrinciplesCorpusConfig


def run(args: list[str], cwd: Path) -> None:
    subprocess.run(args, cwd=cwd, check=True, capture_output=True, text=True)


class CorpusFixture:
    def __init__(self, test: unittest.TestCase) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="corpus-resolution-"))
        test.addCleanup(lambda: __import__("shutil").rmtree(self.root, ignore_errors=True))

    def directory(self, name: str, *, index: str | None = "PRINCIPLES.md") -> Path:
        directory = self.root / name
        directory.mkdir(parents=True)
        if index is not None:
            (directory / index).write_text(f"# Corpus {name}\n\n1. **Check.** Verify.\n", encoding="utf-8")
        return directory

    def git_corpus(self, name: str, *, tag: str | None = None) -> Path:
        repository = self.directory(name)
        run(["git", "init", "-q"], repository)
        run(["git", "config", "user.name", "corpus test"], repository)
        run(["git", "config", "user.email", "corpus-test@example.invalid"], repository)
        run(["git", "config", "commit.gpgsign", "false"], repository)
        run(["git", "config", "tag.gpgsign", "false"], repository)
        run(["git", "add", "."], repository)
        run(["git", "commit", "-q", "-m", "seed corpus"], repository)
        if tag is not None:
            (repository / "TAGGED.md").write_text("tagged revision marker\n", encoding="utf-8")
            run(["git", "add", "."], repository)
            run(["git", "commit", "-q", "-m", "tagged revision"], repository)
            run(["git", "tag", tag], repository)
        return repository

    def target(self) -> Path:
        return self.root / "resolved" / "principles"


class EmbeddedResolutionTests(unittest.TestCase):
    def test_embedded_source_materializes_offline(self) -> None:
        fixture = CorpusFixture(self)
        embedded = fixture.directory("embedded")
        target = fixture.target()

        materialize(PrinciplesCorpusConfig.embedded(), embedded, target)

        self.assertTrue((target / "PRINCIPLES.md").is_file())

    def test_missing_embedded_corpus_is_a_named_failure(self) -> None:
        fixture = CorpusFixture(self)

        with self.assertRaises(CorpusResolutionError):
            materialize(PrinciplesCorpusConfig.embedded(), fixture.root / "absent", fixture.target())

    def test_check_only_validates_embedded_corpus_presence(self) -> None:
        fixture = CorpusFixture(self)

        with self.assertRaises(CorpusResolutionError):
            check_resolvable(PrinciplesCorpusConfig.embedded(), fixture.root / "absent")


class PathResolutionTests(unittest.TestCase):
    def test_path_source_materializes_the_configured_directory(self) -> None:
        fixture = CorpusFixture(self)
        corpus = fixture.directory("local", index="README.md")
        target = fixture.target()

        materialize(
            PrinciplesCorpusConfig(source="path", path=corpus),
            fixture.directory("embedded"),
            target,
        )

        self.assertTrue((target / "README.md").is_file())
        self.assertIn("local", (target / "README.md").read_text(encoding="utf-8"))

    def test_missing_path_source_is_a_named_failure(self) -> None:
        fixture = CorpusFixture(self)

        with self.assertRaises(CorpusResolutionError) as caught:
            materialize(
                PrinciplesCorpusConfig(source="path", path=fixture.root / "absent"),
                fixture.directory("embedded"),
                fixture.target(),
            )

        self.assertIn("does not exist", str(caught.exception))

    def test_corpus_without_an_index_is_a_named_failure(self) -> None:
        fixture = CorpusFixture(self)
        corpus = fixture.directory("indexless", index=None)
        (corpus / "notes.txt").write_text("not an index\n", encoding="utf-8")

        with self.assertRaises(CorpusResolutionError) as caught:
            materialize(
                PrinciplesCorpusConfig(source="path", path=corpus),
                fixture.directory("embedded"),
                fixture.target(),
            )

        self.assertIn("no readable index", str(caught.exception))


class GitResolutionTests(unittest.TestCase):
    def test_git_source_materializes_once_without_git_metadata(self) -> None:
        fixture = CorpusFixture(self)
        repository = fixture.git_corpus("remote")
        target = fixture.target()

        materialize(
            PrinciplesCorpusConfig(source="git", url=str(repository)),
            fixture.directory("embedded"),
            target,
        )

        self.assertTrue((target / "PRINCIPLES.md").is_file())
        self.assertFalse((target / ".git").exists())

    def test_git_source_honors_the_configured_ref(self) -> None:
        fixture = CorpusFixture(self)
        repository = fixture.git_corpus("tagged-remote", tag="v1")
        target = fixture.target()

        materialize(
            PrinciplesCorpusConfig(source="git", url=str(repository), ref="v1"),
            fixture.directory("embedded"),
            target,
        )

        self.assertTrue((target / "TAGGED.md").is_file())

    def test_unreachable_remote_is_a_named_failure(self) -> None:
        fixture = CorpusFixture(self)

        with self.assertRaises(CorpusResolutionError) as caught:
            materialize(
                PrinciplesCorpusConfig(source="git", url=str(fixture.root / "no-such-repo")),
                fixture.directory("embedded"),
                fixture.target(),
            )

        self.assertIn("cannot fetch corpus repository", str(caught.exception))


class AtomicSwapTests(unittest.TestCase):
    def test_failed_resolution_preserves_the_existing_resolved_corpus(self) -> None:
        fixture = CorpusFixture(self)
        embedded = fixture.directory("embedded")
        target = fixture.target()
        materialize(PrinciplesCorpusConfig.embedded(), embedded, target)
        original = (target / "PRINCIPLES.md").read_text(encoding="utf-8")

        with self.assertRaises(CorpusResolutionError):
            materialize(
                PrinciplesCorpusConfig(source="path", path=fixture.root / "absent"),
                embedded,
                target,
            )

        self.assertEqual(original, (target / "PRINCIPLES.md").read_text(encoding="utf-8"))
        self.assertEqual([], list(target.parent.glob("*.resolve.*")))

    def test_resolution_replaces_a_previously_resolved_corpus(self) -> None:
        fixture = CorpusFixture(self)
        embedded = fixture.directory("embedded")
        external = fixture.directory("external", index="README.md")
        target = fixture.target()
        materialize(PrinciplesCorpusConfig.embedded(), embedded, target)

        materialize(PrinciplesCorpusConfig(source="path", path=external), embedded, target)

        self.assertTrue((target / "README.md").is_file())
        self.assertFalse((target / "PRINCIPLES.md").exists())


class CommandLineTests(unittest.TestCase):
    def test_invalid_config_exits_nonzero_with_named_error(self) -> None:
        fixture = CorpusFixture(self)
        config = fixture.root / "principles.toml"
        config.write_text('[corpus]\nsource = "carrier-pigeon"\n', encoding="utf-8")

        result = subprocess.run(
            [
                "python3",
                "-m",
                "tooling.corpus_resolution",
                "--config",
                str(config),
                "--embedded",
                str(fixture.directory("embedded")),
                "--target",
                str(fixture.target()),
            ],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("corpus-resolution:", result.stderr)

    def test_missing_config_resolves_the_embedded_default(self) -> None:
        fixture = CorpusFixture(self)
        embedded = fixture.directory("embedded")
        target = fixture.target()

        exit_code = main(
            [
                "--config",
                str(fixture.root / "absent.toml"),
                "--embedded",
                str(embedded),
                "--target",
                str(target),
            ]
        )

        self.assertEqual(0, exit_code)
        self.assertIsNotNone(corpus_index(target))


if __name__ == "__main__":
    unittest.main()
