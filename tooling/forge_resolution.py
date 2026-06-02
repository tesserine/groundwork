from __future__ import annotations

import argparse
import json
import os
import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FORGE = "github"
FORGE_ENV = "GROUNDWORK_FORGE"


class ForgeResolutionError(ValueError):
    pass


@dataclass(frozen=True)
class ResolvedMechanic:
    operation: str
    forge_tag: str
    path: Path
    mechanic: dict[str, Any]


def active_forge(
    explicit_forge: str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
) -> str:
    environment = os.environ if environ is None else environ
    return explicit_forge or environment.get(FORGE_ENV) or DEFAULT_FORGE


def resolve_mechanic(
    operation: str,
    *,
    forge: str | None = None,
    root: Path | str = ROOT,
    environ: Mapping[str, str] | None = None,
) -> ResolvedMechanic:
    root_path = Path(root)
    manifest = _load_manifest(root_path)
    forge_tag = active_forge(forge, environ=environ)
    registered_forges = _registered_forges(manifest)
    if forge_tag not in registered_forges:
        raise ForgeResolutionError(f"active forge `{forge_tag}` does not resolve in forge_tags")

    declared_forges = _declared_operation_forges(manifest, operation)
    matches = _c3_matches(root_path, operation, forge_tag) if forge_tag in declared_forges else []
    if len(matches) != 1:
        raise ForgeResolutionError(
            f"operation `{operation}` for forge `{forge_tag}` resolves to "
            f"{len(matches)} C-3 mechanics; expected exactly 1"
        )

    path, mechanic = matches[0]
    return ResolvedMechanic(operation=operation, forge_tag=forge_tag, path=path, mechanic=mechanic)


def invoke_operation(
    operation: str,
    parameters: Mapping[str, str],
    *,
    forge: str | None = None,
    root: Path | str = ROOT,
    environ: Mapping[str, str] | None = None,
    cwd: Path | str | None = None,
) -> subprocess.CompletedProcess[str]:
    resolved = resolve_mechanic(operation, forge=forge, root=root, environ=environ)
    command = resolved.mechanic["default_invocation"]
    for name, value in parameters.items():
        command = command.replace(f"{{{name}}}", value)

    environment = os.environ.copy()
    if environ is not None:
        environment.update(environ)
    return subprocess.run(
        command,
        shell=True,
        executable="/bin/sh",
        cwd=cwd,
        env=environment,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def _load_manifest(root: Path) -> dict[str, Any]:
    try:
        return tomllib.loads((root / "manifest.toml").read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ForgeResolutionError(f"manifest.toml is invalid TOML: {error}") from error
    except OSError as error:
        raise ForgeResolutionError(f"cannot read manifest.toml: {error}") from error


def _registered_forges(manifest: dict[str, Any]) -> set[str]:
    return {
        entry["name"]
        for entry in manifest.get("forge_tags", [])
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def _declared_operation_forges(manifest: dict[str, Any], operation: str) -> set[str]:
    declared: set[str] = set()
    for entry in manifest.get("mechanics", []):
        if not isinstance(entry, dict) or entry.get("name") != operation:
            continue
        forge_tags = entry.get("forge_tags")
        if isinstance(forge_tags, list):
            declared.update(forge_tag for forge_tag in forge_tags if isinstance(forge_tag, str))
    return declared


def _c3_matches(root: Path, operation: str, forge_tag: str) -> list[tuple[Path, dict[str, Any]]]:
    mechanics = root / "mechanics"
    if not mechanics.exists():
        return []

    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in sorted(mechanics.rglob("*.toml")):
        try:
            mechanic = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
            continue
        if mechanic.get("name") == operation and mechanic.get("forge_tag") == forge_tag:
            matches.append((path, mechanic))
    return matches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve Groundwork forge-specific mechanics.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    resolve_parser = subparsers.add_parser("resolve", help="Resolve an operation to the active forge mechanic.")
    resolve_parser.add_argument("operation", help="Forge-invariant operation name.")
    resolve_parser.add_argument("--forge", help="Override GROUNDWORK_FORGE for standalone tests/conformance.")
    resolve_parser.add_argument("--root", default=str(ROOT), help="Methodology root. Defaults to this checkout.")
    invoke_parser = subparsers.add_parser("invoke", help="Resolve and invoke the active forge mechanic.")
    invoke_parser.add_argument("operation", help="Forge-invariant operation name.")
    invoke_parser.add_argument("parameters", nargs="*", help="Mechanic parameters as name=value replacements.")
    invoke_parser.add_argument("--forge", help="Override GROUNDWORK_FORGE for standalone tests/conformance.")
    invoke_parser.add_argument("--root", default=str(ROOT), help="Methodology root. Defaults to this checkout.")
    args = parser.parse_args(argv)

    try:
        if args.command == "invoke":
            result = invoke_operation(
                args.operation,
                _parse_parameter_arguments(args.parameters),
                forge=args.forge,
                root=Path(args.root),
            )
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="")
            return result.returncode

        resolved = resolve_mechanic(args.operation, forge=args.forge, root=Path(args.root))
    except ForgeResolutionError as error:
        print(error)
        return 1

    print(
        json.dumps(
            {
                "operation": resolved.operation,
                "forge_tag": resolved.forge_tag,
                "path": str(resolved.path),
                "mechanic": resolved.mechanic,
            },
            sort_keys=True,
        )
    )
    return 0


def _parse_parameter_arguments(arguments: list[str]) -> dict[str, str]:
    parameters: dict[str, str] = {}
    for argument in arguments:
        if "=" not in argument:
            raise ForgeResolutionError(f"parameter `{argument}` must use name=value form")
        name, value = argument.split("=", 1)
        parameters[name] = value
    return parameters


if __name__ == "__main__":
    raise SystemExit(main())
