from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tooling.artifact_schemas import registry_from_manifest
from tooling.mechanics import load_mechanic


ROOT = Path(__file__).resolve().parents[1]
GROUNDWORK_FORGE_ENV = "GROUNDWORK_FORGE"
DEFAULT_FORGE = "github"


class MechanicResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedMechanic:
    data: dict[str, Any]
    path: Path


@dataclass(frozen=True)
class ShellInvocation:
    command: str
    environment: dict[str, str]

    def inspect(self) -> str:
        return self.command

    def run(self, *, cwd: Path | str | None = None) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment.update(self.environment)
        return subprocess.run(
            self.command,
            shell=True,
            executable="/bin/sh",
            cwd=cwd,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


def active_forge(*, override: str | None = None, environment: Mapping[str, str] | None = None) -> str:
    if override is not None:
        return override
    source = os.environ if environment is None else environment
    return source.get(GROUNDWORK_FORGE_ENV, DEFAULT_FORGE)


def resolve_mechanic(
    operation: str,
    *,
    forge: str | None = None,
    root: Path | str = ROOT,
) -> dict[str, Any]:
    return resolve_mechanic_with_path(operation, forge=forge, root=root).data


def resolve_mechanic_with_path(
    operation: str,
    *,
    forge: str | None = None,
    root: Path | str = ROOT,
) -> ResolvedMechanic:
    root_path = Path(root)
    selected_forge = active_forge(override=forge)
    manifest_path = root_path / "manifest.toml"
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    manifest_bindings = [
        entry
        for entry in manifest.get("mechanics", [])
        if isinstance(entry, dict)
        and entry.get("name") == operation
        and selected_forge in entry.get("forge_tags", [])
    ]
    if len(manifest_bindings) != 1:
        raise MechanicResolutionError(
            f"operation `{operation}` for forge `{selected_forge}` resolves to "
            f"{len(manifest_bindings)} manifest bindings; expected exactly 1"
        )

    matches: list[ResolvedMechanic] = []
    registry = registry_from_manifest(manifest_path)
    for path in sorted((root_path / "mechanics").rglob("*.toml")):
        mechanic = load_mechanic(path, registry=registry)
        if mechanic.get("name") == operation and mechanic.get("forge_tag") == selected_forge:
            matches.append(ResolvedMechanic(data=mechanic, path=path))

    if len(matches) != 1:
        raise MechanicResolutionError(
            f"operation `{operation}` for forge `{selected_forge}` resolves to "
            f"{len(matches)} C-3 mechanics; expected exactly 1"
        )
    return matches[0]


def prepare_invocation(mechanic: Mapping[str, Any], parameters: Mapping[str, object]) -> ShellInvocation:
    declared = {
        parameter["name"]: parameter
        for parameter in mechanic.get("parameters", [])
        if isinstance(parameter, dict) and isinstance(parameter.get("name"), str)
    }
    missing = [
        name
        for name, parameter in declared.items()
        if parameter.get("required") is True and name not in parameters
    ]
    if missing:
        raise MechanicResolutionError(f"missing required mechanic parameters: {', '.join(sorted(missing))}")

    environment = {
        name: str(value)
        for name, value in parameters.items()
        if name in declared
    }
    return ShellInvocation(command=str(mechanic["default_invocation"]), environment=environment)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve and inspect Groundwork mechanics.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve_parser = subparsers.add_parser("resolve", help="Resolve an operation for the active forge.")
    resolve_parser.add_argument("operation")
    resolve_parser.add_argument("--forge")
    resolve_parser.add_argument("--root", default=str(ROOT))

    args = parser.parse_args(argv)
    if args.command == "resolve":
        mechanic = resolve_mechanic_with_path(args.operation, forge=args.forge, root=args.root)
        print(mechanic.path.relative_to(Path(args.root)))
        return 0
    raise AssertionError(f"unhandled command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
