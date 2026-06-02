from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
GROUNDWORK_FORGE_ENV = "GROUNDWORK_FORGE"
DEFAULT_FORGE = "github"
PLACEHOLDER_RE = re.compile(r"\{([A-Za-z_][A-Za-z0-9_.-]*)\}")


class ForgeResolutionError(ValueError):
    pass


def active_forge(
    *,
    env: Mapping[str, str] | None = None,
    override: str | None = None,
) -> str:
    if override is not None and override != "":
        return override
    environment = os.environ if env is None else env
    value = environment.get(GROUNDWORK_FORGE_ENV)
    return value if value else DEFAULT_FORGE


def resolve_operation(
    operation: str,
    *,
    root: Path | str = ROOT,
    active_forge_override: str | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    manifest = _load_manifest(root_path)
    forge = active_forge(env=env, override=active_forge_override)
    forge_tags = _manifest_names(manifest, "forge_tags")
    if forge not in forge_tags:
        raise ForgeResolutionError(f"forge `{forge}` is not registered for operation `{operation}`")

    mechanic_entries = [
        entry
        for entry in manifest.get("mechanics", [])
        if isinstance(entry, dict) and entry.get("name") == operation
    ]
    if not mechanic_entries:
        raise ForgeResolutionError(f"operation `{operation}` is not registered for forge `{forge}`")

    declared_tags = mechanic_entries[0].get("forge_tags")
    if not isinstance(declared_tags, list) or forge not in declared_tags:
        raise ForgeResolutionError(f"operation `{operation}` has no declared mechanic for forge `{forge}`")

    matches = [
        mechanic
        for mechanic in _load_c3_mechanics(root_path / "mechanics")
        if mechanic.get("name") == operation and mechanic.get("forge_tag") == forge
    ]
    if len(matches) != 1:
        raise ForgeResolutionError(
            f"operation `{operation}` for forge `{forge}` resolved to {len(matches)} mechanics; expected exactly 1"
        )
    return matches[0]


def render_invocation(invocation: str, parameters: Mapping[str, object]) -> str:
    rendered: list[str] = []
    index = 0
    quote_state: str | None = None

    while index < len(invocation):
        character = invocation[index]
        if character == "'" and quote_state != "double":
            quote_state = None if quote_state == "single" else "single"
            rendered.append(character)
            index += 1
            continue
        if character == '"' and quote_state != "single":
            quote_state = None if quote_state == "double" else "double"
            rendered.append(character)
            index += 1
            continue

        if character == "{":
            match = PLACEHOLDER_RE.match(invocation, index)
            if match is not None:
                name = match.group(1)
                if name not in parameters:
                    raise ForgeResolutionError(f"missing parameter `{name}` for mechanic invocation")
                rendered.append(_quote_parameter(str(parameters[name]), quote_state))
                index = match.end()
                continue

        rendered.append(character)
        index += 1

    return "".join(rendered)


def invoke_mechanic(
    mechanic: Mapping[str, Any],
    parameters: Mapping[str, object],
    *,
    cwd: Path | str | None = None,
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    invocation = mechanic.get("default_invocation")
    if not isinstance(invocation, str):
        raise ForgeResolutionError("mechanic has no string default_invocation")
    command = render_invocation(invocation, parameters)
    return subprocess.run(
        command,
        shell=True,
        executable="/bin/sh",
        cwd=cwd,
        env=None if env is None else dict(env),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve a forge-invariant operation to an active-forge mechanic.")
    parser.add_argument("operation", help="Forge-invariant operation name.")
    parser.add_argument("--root", default=str(ROOT), help="Groundwork checkout or installed resolver root.")
    parser.add_argument("--forge", help=f"Explicit forge override. Defaults to ${GROUNDWORK_FORGE_ENV} or github.")
    parser.add_argument(
        "--invoke",
        action="store_true",
        help="Render and run the mechanic default_invocation with --param values.",
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="Parameter value supplied to --invoke. May be repeated.",
    )
    args = parser.parse_args(argv)

    try:
        mechanic = resolve_operation(args.operation, root=args.root, active_forge_override=args.forge)
        if not args.invoke:
            print(json.dumps(mechanic, sort_keys=True))
            return 0
        result = invoke_mechanic(mechanic, _parse_params(args.param), cwd=args.root)
    except ForgeResolutionError as error:
        print(f"forge-resolution: {error}", file=os.sys.stderr)
        return 1

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=os.sys.stderr)
    return result.returncode


def _quote_parameter(value: str, quote_state: str | None) -> str:
    if quote_state == "single":
        return value.replace("'", "'\\''")
    if quote_state == "double":
        return value.translate(str.maketrans({'"': '\\"', "\\": "\\\\", "$": "\\$", "`": "\\`"}))
    return shlex.quote(value)


def _parse_params(values: list[str]) -> dict[str, str]:
    parameters: dict[str, str] = {}
    for value in values:
        if "=" not in value:
            raise ForgeResolutionError(f"parameter `{value}` must be NAME=VALUE")
        name, parameter_value = value.split("=", 1)
        if not name:
            raise ForgeResolutionError("parameter name must not be empty")
        parameters[name] = parameter_value
    return parameters


def _load_manifest(root: Path) -> dict[str, Any]:
    try:
        return tomllib.loads((root / "manifest.toml").read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ForgeResolutionError(f"manifest.toml not found under {root}") from error
    except tomllib.TOMLDecodeError as error:
        raise ForgeResolutionError(f"manifest.toml is invalid TOML: {error}") from error


def _manifest_names(manifest: dict[str, Any], key: str) -> set[str]:
    return {
        entry["name"]
        for entry in manifest.get(key, [])
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def _load_c3_mechanics(directory: Path) -> list[dict[str, Any]]:
    mechanics: list[dict[str, Any]] = []
    if not directory.exists():
        return mechanics
    for path in sorted(directory.rglob("*.toml")):
        try:
            mechanics.append(tomllib.loads(path.read_text(encoding="utf-8")))
        except (OSError, tomllib.TOMLDecodeError, UnicodeDecodeError):
            continue
    return mechanics


if __name__ == "__main__":
    raise SystemExit(main())
