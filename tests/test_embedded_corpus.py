import re
import tempfile
import unittest

from tooling.principles_config import (
    EMBEDDED_CORPUS_PATH,
    SOURCE_EMBEDDED,
    load_principles_config,
)


CORPUS_FILE = EMBEDDED_CORPUS_PATH / "PRINCIPLES.md"


class EmbeddedDefaultCorpusTests(unittest.TestCase):
    """Gates on the embedded default corpus: present, small, sequenced,
    framed as fallback, and independent of any external corpus."""

    def corpus(self) -> str:
        return CORPUS_FILE.read_text(encoding="utf-8")

    def test_corpus_exists_at_the_embedded_location(self) -> None:
        self.assertTrue(CORPUS_FILE.is_file())

    def test_corpus_is_short(self) -> None:
        # Smallness is the spec, not a compromise. The cap is generous
        # headroom over the authored size, not a target.
        self.assertLessEqual(len(self.corpus().splitlines()), 80)

    def test_principles_are_sequenced(self) -> None:
        numbers = [int(match) for match in re.findall(r"^(\d+)\. ", self.corpus(), re.MULTILINE)]

        self.assertGreaterEqual(len(numbers), 3)
        self.assertEqual(numbers, list(range(1, len(numbers) + 1)))

    def test_missing_deployment_config_selects_the_embedded_corpus(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_principles_config(path=f"{tmp}/missing/principles.toml")

        self.assertEqual(SOURCE_EMBEDDED, config.source)
        self.assertEqual(EMBEDDED_CORPUS_PATH, CORPUS_FILE.parent)

    def test_corpus_is_standalone_with_no_external_references(self) -> None:
        # Independence gate: the default is its own corpus — not a digest,
        # subset, or pointer to the canonical one — and works offline.
        corpus = self.corpus()
        configured_canonical = "https://github.com/pentaxis93/principles"

        self.assertNotIn(configured_canonical, corpus)
        self.assertNotIn("://", corpus)


if __name__ == "__main__":
    unittest.main()
