"""Architecture prose carries rationale; structural renderings live in
their substrate homes.

ADR-0008 (Prose Is Projection), consequence 3: `manifest.toml`,
`schemas/`, and `workflow-contracts/` hold the structure, validated by
`tooling/conformance.py`; an architecture document links to those homes
and carries the why. A hand-maintained manifest copy in prose is a
second editable home.

The invariant this module enforces: no document under `docs/` renders
the manifest's managed set — a `[[protocols]]` or `[[artifact_types]]`
TOML table belongs to `manifest.toml` and nowhere else. The check runs
over every markdown file `docs/` contains, discovered by walking the
tree, so a new document enters the gate the moment it exists.
"""

import unittest
from pathlib import Path

from tooling.prose_conformance import managed_docs_markdown_files


ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

MANAGED_SET_TABLES = ("[[protocols]]", "[[artifact_types]]")


def docs_markdown_files() -> list[Path]:
    return managed_docs_markdown_files(ROOT)


class ArchitectureProseConformanceTests(unittest.TestCase):
    def test_docs_tree_is_scanned(self) -> None:
        """An empty scan would pass vacuously — absence must not green."""
        files = docs_markdown_files()
        self.assertNotEqual([], files)
        self.assertIn(
            DOCS / "architecture" / "connecting-structure.md",
            files,
            "the architecture rationale document is part of the scanned set",
        )

    def test_no_docs_file_renders_the_manifest_managed_set(self) -> None:
        for path in docs_markdown_files():
            body = path.read_text(encoding="utf-8")
            for table in MANAGED_SET_TABLES:
                with self.subTest(document=path.relative_to(ROOT), table=table):
                    self.assertNotIn(
                        table,
                        body,
                        f"{path.relative_to(ROOT)} renders {table}; the "
                        "manifest's managed set has one home, manifest.toml "
                        "(ADR-0008, consequence 3)",
                    )


if __name__ == "__main__":
    unittest.main()
