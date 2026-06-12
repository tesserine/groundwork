import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)#\s]+)(?:#[^)\s]*)?\)")


def instruction_files() -> list[Path]:
    return sorted(
        [
            *ROOT.glob("protocols/*/PROTOCOL.md"),
            *ROOT.glob("protocols/*/references/*.md"),
            *ROOT.glob("skills/*/SKILL.md"),
            *ROOT.glob("skills/*/references/*.md"),
        ]
    )


FENCED_BLOCK = re.compile(r"^`{3,}.*?^`{3,}", re.DOTALL | re.MULTILINE)


def relative_targets(body: str) -> list[str]:
    prose = FENCED_BLOCK.sub("", body)
    targets = []
    for target in MARKDOWN_LINK.findall(prose):
        if "://" in target or target.startswith("mailto:"):
            continue
        targets.append(target)
    return targets


SCRIPT_PATH = re.compile(r"(?<![\w/.@-])([\w.-]+(?:/[\w.-]+)+\.(?:py|sh))(?![\w/])")


class ReferenceLinkTests(unittest.TestCase):
    def test_instruction_files_exist_to_scan(self) -> None:
        self.assertNotEqual([], instruction_files())

    def test_script_paths_resolve_from_methodology_root(self) -> None:
        """Slash-containing .py/.sh paths in instruction files must resolve
        from the methodology root.

        Markdown links are file-relative (they render on the forge), but
        script invocation paths are read by agents whose working directory
        is not the instruction file's directory — a script path is only
        unambiguous when it is methodology-root-relative. Bare filenames
        (no slash) are prose mentions and exempt.
        """
        for path in instruction_files():
            body = path.read_text(encoding="utf-8")
            for target in SCRIPT_PATH.findall(body):
                with self.subTest(source=path.relative_to(ROOT), target=target):
                    self.assertTrue(
                        (ROOT / target).is_file(),
                        f"{path.relative_to(ROOT)} references script path {target}, "
                        "which does not resolve from the methodology root",
                    )

    def test_relative_references_in_instruction_files_resolve(self) -> None:
        for path in instruction_files():
            body = path.read_text(encoding="utf-8")
            for target in relative_targets(body):
                resolved = (path.parent / target).resolve()
                with self.subTest(source=path.relative_to(ROOT), target=target):
                    self.assertTrue(
                        resolved.is_file(),
                        f"{path.relative_to(ROOT)} links to {target}, which does not exist",
                    )


if __name__ == "__main__":
    unittest.main()
