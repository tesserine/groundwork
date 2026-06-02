from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


def _default_root() -> Path:
    module_directory = Path(__file__).resolve().parent
    for candidate in (module_directory, module_directory.parent):
        if (candidate / "manifest.toml").exists():
            return candidate
    return module_directory.parent


ROOT = _default_root()
ACTIVE_FORGE_ENV = "GROUNDWORK_FORGE"
DEFAULT_FORGE = "github"
PLACEHOLDER_PATTERN = re.compile(r"\{\{([a-z][a-z0-9]*([_.-][a-z0-9]+)*)\}\}")


class ForgeOperationError(ValueError):
    pass


@dataclass(frozen=True)
class Resolution:
    name: str
    forge_tag: str
    mechanic: dict[str, Any]

    def as_json(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "forge_tag": self.forge_tag,
            "purpose": self.mechanic["purpose"],
            "default_invocation": self.mechanic["default_invocation"],
        }


def render_invocation(mechanic: dict[str, Any], parameters: Mapping[str, str]) -> str:
    declared = {
        parameter["name"]
        for parameter in mechanic.get("parameters", [])
        if isinstance(parameter, dict) and isinstance(parameter.get("name"), str)
    }
    required = {
        parameter["name"]
        for parameter in mechanic.get("parameters", [])
        if isinstance(parameter, dict) and parameter.get("required") is True and isinstance(parameter.get("name"), str)
    }
    supplied = set(parameters)
    missing = sorted(required - supplied)
    if missing:
        raise ForgeOperationError(f"missing required parameters: {', '.join(missing)}")
    unknown = sorted(supplied - declared)
    if unknown:
        raise ForgeOperationError(f"unknown parameters: {', '.join(unknown)}")

    def substitute(match: re.Match[str]) -> str:
        name = match.group(1)
        if name not in parameters:
            raise ForgeOperationError(f"placeholder `{{{{{name}}}}}` has no supplied parameter")
        return shlex.quote(parameters[name])

    return PLACEHOLDER_PATTERN.sub(substitute, mechanic["default_invocation"])


def active_forge(override: str | None = None, environ: Mapping[str, str] | None = None) -> str:
    if override:
        return override
    environment = os.environ if environ is None else environ
    return environment.get(ACTIVE_FORGE_ENV) or DEFAULT_FORGE


def resolve_operation(
    operation: str,
    *,
    root: Path | str = ROOT,
    forge: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> Resolution:
    root_path = Path(root)
    manifest = _load_toml(root_path / "manifest.toml")
    forge_tag = active_forge(forge, environ)
    registered_forges = _registered_forge_tags(manifest)
    if forge_tag not in registered_forges:
        raise ForgeOperationError(f"forge `{forge_tag}` is not registered")

    matrix_entries = [
        entry
        for entry in manifest.get("mechanics", [])
        if isinstance(entry, dict)
        and entry.get("name") == operation
        and isinstance(entry.get("forge_tags"), list)
        and forge_tag in entry["forge_tags"]
    ]
    if len(matrix_entries) != 1:
        raise ForgeOperationError(
            f"operation `{operation}` for forge `{forge_tag}` resolves to {len(matrix_entries)} manifest entries; expected exactly 1"
        )

    matches = [
        mechanic
        for mechanic in _load_mechanics(root_path / "mechanics")
        if mechanic.get("name") == operation and mechanic.get("forge_tag") == forge_tag
    ]
    if len(matches) != 1:
        raise ForgeOperationError(
            f"operation `{operation}` for forge `{forge_tag}` resolves to {len(matches)} C-3 mechanics; expected exactly 1"
        )
    return Resolution(name=operation, forge_tag=forge_tag, mechanic=matches[0])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="groundwork-forge-operation")
    subcommands = parser.add_subparsers(dest="command", required=True)
    resolve = subcommands.add_parser("resolve")
    resolve.add_argument("operation")
    resolve.add_argument("--forge")
    resolve.add_argument("--root", default=str(ROOT))
    render = subcommands.add_parser("render")
    render.add_argument("operation")
    render.add_argument("--forge")
    render.add_argument("--root", default=str(ROOT))
    render.add_argument("--param", action="append", default=[])
    invoke = subcommands.add_parser("invoke")
    invoke.add_argument("operation")
    invoke.add_argument("--forge")
    invoke.add_argument("--root", default=str(ROOT))
    invoke.add_argument("--param", action="append", default=[])
    args = parser.parse_args(argv)

    try:
        if args.command == "resolve":
            sys.stdout.write(json.dumps(resolve_operation(args.operation, root=args.root, forge=args.forge).as_json()) + "\n")
        elif args.command == "render":
            resolved = resolve_operation(args.operation, root=args.root, forge=args.forge)
            sys.stdout.write(render_invocation(resolved.mechanic, _parse_parameters(args.param)) + "\n")
        elif args.command == "invoke":
            resolved = resolve_operation(args.operation, root=args.root, forge=args.forge)
            command = render_invocation(resolved.mechanic, _parse_parameters(args.param))
            result = subprocess.run(
                command,
                shell=True,
                executable="/bin/sh",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            sys.stdout.write(result.stdout)
            sys.stderr.write(result.stderr)
            return result.returncode
    except ForgeOperationError as error:
        print(f"groundwork-forge-operation: {error}", file=sys.stderr)
        return 1
    return 0


def _parse_parameters(values: list[str]) -> dict[str, str]:
    parameters: dict[str, str] = {}
    for value in values:
        name, separator, parameter_value = value.partition("=")
        if not separator or not name:
            raise ForgeOperationError(f"parameter `{value}` must use NAME=VALUE")
        parameters[name] = parameter_value
    return parameters


def _load_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _registered_forge_tags(manifest: dict[str, Any]) -> set[str]:
    return {
        entry["name"]
        for entry in manifest.get("forge_tags", [])
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def _load_mechanics(directory: Path) -> list[dict[str, Any]]:
    mechanics: list[dict[str, Any]] = []
    if not directory.exists():
        return mechanics
    for path in sorted(directory.rglob("*.toml")):
        mechanics.append(_load_toml(path))
    return mechanics


if __name__ == "__main__":
    raise SystemExit(main())
