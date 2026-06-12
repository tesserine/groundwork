"""Durable gates for the configurable-principles-corpus coherence upgrade.

These hold the invariants of epic #397 permanently:

- Reckon depends on a principles corpus, but never on a hard-coded one:
  its skill text references the corpus only through the configured/local
  abstraction.
- Reckon does not pre-digest the corpus: no skill or protocol text names
  a privileged subset of principles. Orient selects, per domain, from the
  resolved corpus.
- Principle authority never routes through the legacy commons mirrors:
  no tracked file links to them. (Prose provenance notes that record the
  historical citation route are legitimate; the gates target links.)

Functional gates for the same epic live elsewhere: offline zero-config
resolution and external-corpus materialization in
tests/test_corpus_resolution.py and tests/test_groundwork_install.py;
embedded-default smallness/independence in tests/test_embedded_corpus.py.
"""

import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# The phrase that named reckon's removed pre-selection, and the principle
# names it privileged. Principle selection belongs to Orient alone.
PRE_SELECTION_PHRASE = re.compile(r"three\s+universals", re.IGNORECASE)
PRIVILEGED_PRINCIPLE_NAMES = re.compile(r"\bGrounding\b|\bTraceability\b|\bParsimony\b|\bSingle Home\b")

# Link patterns into the legacy commons principle mirrors and superseded
# pointer-stub ADRs (PRINCIPLES.md, DESIGN-PRINCIPLES.md, ADRs 0001-0004,
# 0007, 0013).
COMMONS_MIRROR_LINKS = re.compile(
    r"tesserine/commons/(?:blob|raw|tree)/[^\s)\"']*(?:DESIGN-PRINCIPLES|PRINCIPLES\.md|adr/00(?:0[1-4]|07|13))"
)


def tracked_files() -> list[Path]:
    listing = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / line for line in listing.stdout.splitlines() if line]


def readable_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return ""


class ReckonCorpusPointerGates(unittest.TestCase):
    def test_reckon_carries_no_hard_coded_corpus_repository(self) -> None:
        for path in (ROOT / "skills" / "reckon").rglob("*"):
            if path.is_file():
                with self.subTest(file=path.relative_to(ROOT)):
                    self.assertNotIn("pentaxis93/principles", readable_text(path))

    def test_no_methodology_text_names_a_privileged_principle_subset(self) -> None:
        for path in tracked_files():
            if path.suffix != ".md":
                continue
            if path.parts[len(ROOT.parts)] not in {"skills", "protocols"}:
                continue
            with self.subTest(file=path.relative_to(ROOT)):
                self.assertIsNone(PRIVILEGED_PRINCIPLE_NAMES.search(readable_text(path)))


class PreSelectionAbsenceGates(unittest.TestCase):
    def test_the_pre_selection_phrase_is_absent_from_every_tracked_file(self) -> None:
        for path in tracked_files():
            with self.subTest(file=path.relative_to(ROOT)):
                self.assertIsNone(PRE_SELECTION_PHRASE.search(readable_text(path)))


class CommonsMirrorLinkGates(unittest.TestCase):
    def test_no_tracked_file_links_to_commons_principle_mirrors_or_stub_adrs(self) -> None:
        for path in tracked_files():
            with self.subTest(file=path.relative_to(ROOT)):
                self.assertIsNone(COMMONS_MIRROR_LINKS.search(readable_text(path)))


if __name__ == "__main__":
    unittest.main()
