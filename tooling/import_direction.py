"""Reference fitness function: layer import direction.

Checks that no Python module inside one top-level layer imports from a
forbidden top-level layer — the structurally-checkable code-quality
projection the contract skill's code-quality dimension types as an
``executable`` criterion. A run of this checker is the recorded evidence
for such a criterion; a seeded violating change fails it.

Scope, stated honestly: layers are top-level directories under the given
root, and the checker resolves absolute ``import``/``from`` statements by
their first module segment. Relative imports stay inside their own
package and cannot cross top-level layers, so they are out of scope by
construction.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Violation:
    """One forbidden layer edge found in the tree."""

    path: Path
    lineno: int
    layer: str
    module: str

    def render(self) -> str:
        return f"{self.path}:{self.lineno}: layer {self.layer!r} imports {self.module!r}"


def _imported_modules(tree: ast.AST) -> list[tuple[int, str]]:
    modules: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules.append((node.lineno, node.module))
    return modules


def find_violations(
    root: Path, forbidden: list[tuple[str, str]]
) -> list[Violation]:
    """Return every forbidden layer edge under ``root``.

    ``forbidden`` pairs name edges as ``(importer_layer, imported_layer)``:
    a module whose path sits under ``importer_layer`` may not import a
    module whose top-level package is ``imported_layer``.
    """
    root = Path(root)
    violations: list[Violation] = []
    for importer_layer, imported_layer in forbidden:
        layer_dir = root / importer_layer
        if not layer_dir.is_dir():
            continue
        for source in sorted(layer_dir.rglob("*.py")):
            try:
                tree = ast.parse(source.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            for lineno, module in _imported_modules(tree):
                if module.split(".")[0] == imported_layer:
                    violations.append(
                        Violation(
                            path=source.relative_to(root),
                            lineno=lineno,
                            layer=importer_layer,
                            module=module,
                        )
                    )
    return violations


def _parse_edge(raw: str) -> tuple[str, str]:
    importer, separator, imported = raw.partition(":")
    if not separator or not importer or not imported:
        raise argparse.ArgumentTypeError(
            f"forbidden edge {raw!r} must be 'importer_layer:imported_layer'"
        )
    return importer, imported


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Fail when a module in one top-level layer imports from a "
            "forbidden top-level layer."
        )
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root whose top-level directories are the layers.",
    )
    parser.add_argument(
        "--forbid",
        action="append",
        required=True,
        type=_parse_edge,
        metavar="IMPORTER:IMPORTED",
        help="Forbidden layer edge; repeatable.",
    )
    args = parser.parse_args(argv)

    violations = find_violations(Path(args.root), args.forbid)
    for violation in violations:
        print(violation.render(), file=sys.stderr)
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
