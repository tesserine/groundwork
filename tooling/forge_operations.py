from __future__ import annotations

import argparse
import os
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]


class ForgeOperationError(ValueError):
    pass


def active_forge_type(environment: Mapping[str, str], override: str | None) -> str:
    if override:
        return override
    return environment.get("GROUNDWORK_FORGE_TYPE") or "github"


def resolve_operation(root: Path | str, operation: str, *, forge_type: str | None = None) -> dict[str, Any]:
    root_path = Path(root)
    manifest = _load_toml(root_path / "manifest.toml")
    selected_forge_type = active_forge_type(os.environ, forge_type)
    forge_tags = _manifest_names(manifest, "forge_tags")
    if selected_forge_type not in forge_tags:
        raise ForgeOperationError(f"forge type `{selected_forge_type}` does not resolve in forge_tags")

    operation_entry = _manifest_operation(manifest, operation)
    declared_forge_types = operation_entry.get("forge_tags")
    if not isinstance(declared_forge_types, list) or selected_forge_type not in declared_forge_types:
        raise ForgeOperationError(f"operation `{operation}` is not bound for forge type `{selected_forge_type}`")

    matches = [
        mechanic
        for mechanic in _load_mechanics(root_path / "mechanics")
        if mechanic.get("name") == operation and mechanic.get("forge_tag") == selected_forge_type
    ]
    if len(matches) != 1:
        raise ForgeOperationError(
            f"operation `{operation}` for forge type `{selected_forge_type}` resolves to {len(matches)} mechanics; expected exactly 1"
        )
    return matches[0]


def inspect_invocation(mechanic: Mapping[str, Any], values: Mapping[str, str]) -> str:
    unknown = sorted(set(values) - set(_parameters(mechanic)))
    if unknown:
        raise ForgeOperationError(f"unknown parameter(s): {', '.join(unknown)}")
    return _invocation_body(mechanic)


def render_shell_invocation(mechanic: Mapping[str, Any], values: Mapping[str, str]) -> tuple[str, dict[str, str]]:
    parameters = _parameters(mechanic)
    deployment_parameters = _deployment_parameters(mechanic)
    provided_deployment_values = sorted(set(values) & set(deployment_parameters))
    if provided_deployment_values:
        raise ForgeOperationError(
            f"deployment-resolved parameter(s) must come from GROUNDWORK_*: {', '.join(provided_deployment_values)}"
        )
    deployment_values = _deployment_parameter_values(mechanic, os.environ)
    resolved_values = {**values, **deployment_values}
    missing = [name for name, parameter in parameters.items() if parameter.get("required") and name not in resolved_values]
    if missing:
        raise ForgeOperationError(f"missing required parameter(s): {', '.join(sorted(missing))}")
    unknown = sorted(set(resolved_values) - set(parameters))
    if unknown:
        raise ForgeOperationError(f"unknown parameter(s): {', '.join(unknown)}")
    return _invocation_body(mechanic), {name: str(value) for name, value in resolved_values.items()}


def run_invocation(
    mechanic: Mapping[str, Any],
    values: Mapping[str, str],
    *,
    cwd: Path | str,
) -> subprocess.CompletedProcess[str]:
    command, invocation_environment = render_shell_invocation(mechanic, values)
    environment = os.environ.copy()
    environment.update(invocation_environment)
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve and invoke Groundwork forge operations.")
    parser.add_argument("--root", default=str(ROOT), help="Groundwork methodology root. Defaults to this checkout.")
    parser.add_argument("--forge-type", help="Active forge type override. Defaults to GROUNDWORK_FORGE_TYPE, then github.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve_parser = subparsers.add_parser("resolve", help="Print the resolved mechanic path-equivalent name.")
    resolve_parser.add_argument("operation")

    inspect_parser = subparsers.add_parser("inspect", help="Print the constant shell invocation body.")
    inspect_parser.add_argument("operation")

    run_parser = subparsers.add_parser("run", help="Run the resolved mechanic with parameter bindings.")
    run_parser.add_argument("operation")
    run_parser.add_argument(
        "--secret-env",
        action="append",
        default=[],
        metavar="NAME=ENV",
        help="Bind secret parameter NAME from environment variable ENV without putting the value in argv.",
    )
    run_parser.add_argument("bindings", nargs="*", help="Parameter bindings in NAME=VALUE form.")

    args = parser.parse_args(argv)
    try:
        mechanic = resolve_operation(args.root, args.operation, forge_type=args.forge_type)
        if args.command == "resolve":
            print(f"{mechanic['name']}[{mechanic['forge_tag']}]")
            return 0
        if args.command == "inspect":
            print(inspect_invocation(mechanic, {}))
            return 0
        if args.command == "run":
            values = _parse_bindings(args.bindings, mechanic)
            values.update(_parse_secret_env_bindings(args.secret_env, mechanic, os.environ))
            result = run_invocation(mechanic, values, cwd=Path.cwd())
            if result.stdout:
                print(result.stdout, end="")
            if result.stderr:
                print(result.stderr, end="", file=os.sys.stderr)
            return result.returncode
    except ForgeOperationError as error:
        print(f"groundwork-mechanic: {error}", file=os.sys.stderr)
        return 1
    return 1


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise ForgeOperationError(f"{path} is invalid TOML: {error}") from error


def _manifest_names(manifest: Mapping[str, Any], key: str) -> set[str]:
    return {
        entry["name"]
        for entry in manifest.get(key, [])
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }


def _manifest_operation(manifest: Mapping[str, Any], operation: str) -> Mapping[str, Any]:
    matches = [
        entry
        for entry in manifest.get("mechanics", [])
        if isinstance(entry, dict) and entry.get("name") == operation
    ]
    if not matches:
        raise ForgeOperationError(f"operation `{operation}` does not resolve in manifest mechanics")
    if len(matches) != 1:
        raise ForgeOperationError(f"operation `{operation}` resolves to {len(matches)} manifest mechanics; expected exactly 1")
    return matches[0]


def _load_mechanics(directory: Path) -> list[dict[str, Any]]:
    if not directory.exists():
        return []
    return [_load_toml(path) for path in sorted(directory.rglob("*.toml"))]


def _parameters(mechanic: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {
        parameter["name"]: parameter
        for parameter in mechanic.get("parameters", [])
        if isinstance(parameter, dict) and isinstance(parameter.get("name"), str)
    }


def _secret_parameters(mechanic: Mapping[str, Any]) -> set[str]:
    return {name for name, parameter in _parameters(mechanic).items() if parameter.get("secret") is True}


def _deployment_parameters(mechanic: Mapping[str, Any]) -> dict[str, str]:
    return {
        name: str(parameter["deployment_value"])
        for name, parameter in _parameters(mechanic).items()
        if isinstance(parameter.get("deployment_value"), str)
    }


def _deployment_parameter_values(
    mechanic: Mapping[str, Any],
    environment: Mapping[str, str],
) -> dict[str, str]:
    deployments = _deployment_parameters(mechanic)
    if not deployments:
        return {}
    forge_type = mechanic.get("forge_tag")
    if not isinstance(forge_type, str):
        raise ForgeOperationError("deployment-resolved parameters require mechanic forge_tag")
    resolved = _resolved_deployment_values(forge_type, set(deployments.values()), environment)
    values: dict[str, str] = {}
    for name, deployment_value in deployments.items():
        values[name] = resolved[deployment_value]
    return values


def _resolved_deployment_values(
    forge_type: str,
    deployment_values: set[str],
    environment: Mapping[str, str],
) -> dict[str, str]:
    return {
        deployment_value: _resolve_deployment_value(forge_type, deployment_value, environment)
        for deployment_value in deployment_values
    }


def _resolve_deployment_value(
    forge_type: str,
    deployment_value: str,
    environment: Mapping[str, str],
) -> str:
    if forge_type == "github":
        if deployment_value == "owner":
            return _required_environment(environment, "GROUNDWORK_FORGE_OWNER")
        if deployment_value == "name":
            return _required_environment(environment, "GROUNDWORK_FORGE_NAME")
        if deployment_value == "repository":
            owner = _required_environment(environment, "GROUNDWORK_FORGE_OWNER")
            name = _required_environment(environment, "GROUNDWORK_FORGE_NAME")
            return f"{owner}/{name}"
        raise ForgeOperationError(
            f"deployment value `{deployment_value}` is not supported for forge type `{forge_type}`"
        )
    if forge_type == "sourcehut":
        if deployment_value == "owner":
            return _required_environment(environment, "GROUNDWORK_FORGE_OWNER")
        if deployment_value == "name":
            return _required_environment(environment, "GROUNDWORK_FORGE_NAME")
        if deployment_value == "repository":
            owner = _required_environment(environment, "GROUNDWORK_FORGE_OWNER")
            name = _required_environment(environment, "GROUNDWORK_FORGE_NAME")
            return f"{owner}/{name}"
        if deployment_value == "todo_query_url":
            endpoint = _required_environment(environment, "GROUNDWORK_FORGE_ENDPOINT")
            return f"https://todo.{endpoint}/query"
        if deployment_value == "git_query_url":
            endpoint = _required_environment(environment, "GROUNDWORK_FORGE_ENDPOINT")
            return f"https://git.{endpoint}/query"
        if deployment_value == "ssh_remote":
            endpoint = _required_environment(environment, "GROUNDWORK_FORGE_ENDPOINT")
            owner = _required_environment(environment, "GROUNDWORK_FORGE_OWNER")
            name = _required_environment(environment, "GROUNDWORK_FORGE_NAME")
            return f"git@git.{endpoint}:~{owner}/{name}"
        if deployment_value == "tracker_id":
            return _required_environment(environment, "GROUNDWORK_FORGE_TRACKER_ID")
        if deployment_value == "repo_id":
            return _required_environment(environment, "GROUNDWORK_FORGE_REPO_ID")
        raise ForgeOperationError(
            f"deployment value `{deployment_value}` is not supported for forge type `{forge_type}`"
        )
    raise ForgeOperationError(f"forge type `{forge_type}` does not support deployment identity")


def _required_environment(environment: Mapping[str, str], name: str) -> str:
    value = environment.get(name)
    if value is None or value == "":
        raise ForgeOperationError(f"missing required deployment identity atom `{name}`")
    return value


def _invocation_body(mechanic: Mapping[str, Any]) -> str:
    body = mechanic.get("default_invocation")
    if not isinstance(body, str) or not body:
        raise ForgeOperationError("mechanic default_invocation must be a non-empty string")
    return body


def _parse_bindings(bindings: list[str], mechanic: Mapping[str, Any] | None = None) -> dict[str, str]:
    parsed: dict[str, str] = {}
    secret_parameters = _secret_parameters(mechanic) if mechanic is not None else set()
    for binding in bindings:
        if "=" not in binding:
            raise ForgeOperationError(f"binding `{binding}` must use NAME=VALUE")
        name, value = binding.split("=", 1)
        if not name:
            raise ForgeOperationError("binding name must not be empty")
        if name in secret_parameters:
            raise ForgeOperationError(f"secret parameter `{name}` must use --secret-env, not NAME=VALUE")
        parsed[name] = value
    return parsed


def _parse_secret_env_bindings(
    bindings: list[str],
    mechanic: Mapping[str, Any],
    environment: Mapping[str, str],
) -> dict[str, str]:
    parsed: dict[str, str] = {}
    parameters = _parameters(mechanic)
    secret_parameters = _secret_parameters(mechanic)
    for binding in bindings:
        if "=" not in binding:
            raise ForgeOperationError(f"secret binding `{binding}` must use NAME=ENV")
        name, env_name = binding.split("=", 1)
        if not name:
            raise ForgeOperationError("secret binding name must not be empty")
        if not env_name:
            raise ForgeOperationError(f"secret binding `{name}` must name an environment variable")
        if name not in parameters:
            raise ForgeOperationError(f"unknown parameter(s): {name}")
        if name not in secret_parameters:
            raise ForgeOperationError(f"parameter `{name}` is not secret; use NAME=VALUE")
        if env_name not in environment:
            raise ForgeOperationError(f"secret environment variable `{env_name}` for `{name}` is not set")
        parsed[name] = environment[env_name]
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
