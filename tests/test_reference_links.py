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


class ReferenceLinkTests(unittest.TestCase):
    def test_instruction_files_exist_to_scan(self) -> None:
        self.assertNotEqual([], instruction_files())

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
