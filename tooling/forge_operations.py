from __future__ import annotations

import argparse
import json
import os
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
RUNA_FORGE_ADDRESSES = "RUNA_FORGE_ADDRESSES"
REPOSITORY_DEPLOYMENT_VALUES = {"repository", "owner", "name", "git_query_url", "ssh_remote"}
TRACKER_DEPLOYMENT_VALUES = {"owner_username", "tracker_id", "todo_query_url", "tracker_identity"}


class ForgeOperationError(ValueError):
    pass


def resolve_operation(
    root: Path | str,
    operation: str,
    *,
    repository: str | None = None,
    tracker: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    manifest = _load_toml(root_path / "manifest.toml")
    operation_entry = _manifest_operation(manifest, operation)
    declared_forge_types = operation_entry.get("forge_tags")
    if not isinstance(declared_forge_types, list):
        raise ForgeOperationError(f"operation `{operation}` does not declare forge_tags")
    forge_tags = _manifest_names(manifest, "forge_tags")
    environment = os.environ if environment is None else environment
    address_book = _forge_addresses(environment)
    selected_forge_types = _selected_forge_types(
        address_book,
        repository_selector=repository,
        tracker_selector=tracker,
    )

    matches: list[dict[str, Any]] = []
    for mechanic in _load_mechanics(root_path / "mechanics"):
        if mechanic.get("name") != operation:
            continue
        forge_type = mechanic.get("forge_tag")
        if not isinstance(forge_type, str):
            continue
        if forge_type not in forge_tags:
            raise ForgeOperationError(f"forge type `{forge_type}` does not resolve in forge_tags")
        if forge_type not in declared_forge_types:
            continue
        if selected_forge_types and forge_type not in selected_forge_types:
            continue
        try:
            context = _deployment_context_for_mechanic(
                mechanic,
                address_book,
                repository_selector=repository,
                tracker_selector=tracker,
            )
        except ForgeOperationError:
            continue
        if context["instance"]["type"] == forge_type:
            resolved = dict(mechanic)
            resolved["_deployment_context"] = context
            matches.append(resolved)
    if len(matches) != 1:
        selectors = []
        if repository is not None:
            selectors.append(f"repository `{repository}`")
        if tracker is not None:
            selectors.append(f"tracker `{tracker}`")
        selector_text = f" for {', '.join(selectors)}" if selectors else ""
        raise ForgeOperationError(
            f"operation `{operation}`{selector_text} resolves to {len(matches)} mechanics; expected exactly 1"
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
            f"deployment-resolved parameter(s) must come from the configured forge environment: {', '.join(provided_deployment_values)}"
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
    parser.add_argument("--repository", help="Configured repository selector for repository-scoped mechanics.")
    parser.add_argument("--tracker", help="Configured tracker selector for tracker-scoped mechanics.")
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
        mechanic = resolve_operation(
            args.root,
            args.operation,
            repository=args.repository,
            tracker=args.tracker,
        )
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
    context = mechanic.get("_deployment_context")
    if not isinstance(context, dict):
        context = _deployment_context_for_mechanic(
            mechanic,
            _forge_addresses(environment),
            repository_selector=None,
            tracker_selector=None,
        )
    resolved = _resolved_deployment_values(context, set(deployments.values()))
    values: dict[str, str] = {}
    for name, deployment_value in deployments.items():
        values[name] = resolved[deployment_value]
    return values


def _resolved_deployment_values(context: Mapping[str, Any], deployment_values: set[str]) -> dict[str, str]:
    return {
        deployment_value: _resolve_deployment_value(context, deployment_value)
        for deployment_value in deployment_values
    }


def _resolve_deployment_value(context: Mapping[str, Any], deployment_value: str) -> str:
    instance = context["instance"]
    resource = context["resource"]
    forge_type = instance["type"]
    if forge_type == "github":
        if deployment_value == "owner":
            return str(resource["owner"])
        if deployment_value == "name":
            return str(resource["name"])
        if deployment_value == "repository":
            return f"{resource['owner']}/{resource['name']}"
        if deployment_value == "tracker_identity":
            return f"github@{instance['services']['tracker']}/tracker/{resource['owner']}/{resource['name']}"
        raise ForgeOperationError(
            f"deployment value `{deployment_value}` is not supported for forge type `{forge_type}`"
        )
    if forge_type == "sourcehut":
        if deployment_value == "owner":
            return _sourcehut_remote_owner(str(resource["owner"]))
        if deployment_value == "owner_username":
            return _sourcehut_username_owner(str(resource["owner"]))
        if deployment_value == "name":
            return str(resource["name"])
        if deployment_value == "repository":
            return f"{_sourcehut_remote_owner(str(resource['owner']))}/{resource['name']}"
        if deployment_value == "todo_query_url":
            return f"https://{instance['services']['tracker']}/query"
        if deployment_value == "git_query_url":
            return f"https://{instance['services']['git']}/query"
        if deployment_value == "ssh_remote":
            return f"git@{instance['services']['git']}:{_sourcehut_remote_owner(str(resource['owner']))}/{resource['name']}"
        if deployment_value == "tracker_id":
            tracker_id = resource.get("tracker_id")
            if not tracker_id:
                raise ForgeOperationError("selected sourcehut tracker is missing tracker_id")
            return str(tracker_id)
        if deployment_value == "tracker_identity":
            return str(resource["identity"])
        raise ForgeOperationError(
            f"deployment value `{deployment_value}` is not supported for forge type `{forge_type}`"
        )
    raise ForgeOperationError(f"forge type `{forge_type}` does not support deployment identity")


def _deployment_context_for_mechanic(
    mechanic: Mapping[str, Any],
    address_book: Mapping[str, Any],
    *,
    repository_selector: str | None,
    tracker_selector: str | None,
) -> dict[str, Any]:
    deployments = set(_deployment_parameters(mechanic).values())
    if not deployments:
        forge_type = mechanic.get("forge_tag")
        if not isinstance(forge_type, str):
            raise ForgeOperationError("mechanic without deployment values requires forge_tag")
        return {"kind": "none", "resource": {}, "instance": {"type": forge_type, "services": {}}}
    forge_type = mechanic.get("forge_tag")
    if not isinstance(forge_type, str):
        raise ForgeOperationError("mechanic with deployment values requires forge_tag")
    resource_kind = _resource_kind_for_deployments(deployments, forge_type)
    if resource_kind == "tracker":
        resource = _select_resource(address_book, "trackers", tracker_selector)
    else:
        resource = _select_resource(address_book, "repositories", repository_selector)
    instance = _instance_for_resource(address_book, resource)
    return {"kind": resource_kind, "resource": resource, "instance": instance}


def _resource_kind_for_deployments(deployment_values: set[str], forge_type: str) -> str:
    if forge_type == "github":
        return "repository"
    if deployment_values & TRACKER_DEPLOYMENT_VALUES:
        if deployment_values & {"git_query_url", "ssh_remote"}:
            raise ForgeOperationError("mechanic mixes tracker and repository deployment values")
        return "tracker"
    return "repository"


def _sourcehut_remote_owner(owner: str) -> str:
    return f"~{owner.lstrip('~')}"


def _sourcehut_username_owner(owner: str) -> str:
    return owner.lstrip("~")


def _select_resource(address_book: Mapping[str, Any], key: str, selector: str | None) -> Mapping[str, Any]:
    resources = address_book.get(key)
    if not isinstance(resources, list):
        raise ForgeOperationError(f"forge address payload is missing `{key}`")
    if selector is not None:
        for resource in resources:
            if isinstance(resource, dict) and resource.get("id") == selector:
                return resource
        raise ForgeOperationError(f"{key[:-1]} selector `{selector}` does not name a configured resource")
    if len(resources) == 1 and isinstance(resources[0], dict):
        return resources[0]
    if not resources:
        raise ForgeOperationError(f"no configured {key} can satisfy this forge operation")
    raise ForgeOperationError(f"multiple configured {key} require an explicit selector")


def _instance_for_resource(address_book: Mapping[str, Any], resource: Mapping[str, Any]) -> Mapping[str, Any]:
    instance_id = resource.get("instance")
    instances = address_book.get("instances")
    if not isinstance(instance_id, str) or not isinstance(instances, list):
        raise ForgeOperationError("forge address resource is missing its instance")
    for instance in instances:
        if isinstance(instance, dict) and instance.get("id") == instance_id:
            return instance
    raise ForgeOperationError(f"forge resource references unknown instance `{instance_id}`")


def _selected_forge_types(
    address_book: Mapping[str, Any],
    *,
    repository_selector: str | None,
    tracker_selector: str | None,
) -> set[str]:
    selected = set()
    if repository_selector is not None:
        selected.add(
            str(
                _instance_for_resource(
                    address_book,
                    _select_resource(address_book, "repositories", repository_selector),
                )["type"]
            )
        )
    if tracker_selector is not None:
        selected.add(
            str(
                _instance_for_resource(
                    address_book,
                    _select_resource(address_book, "trackers", tracker_selector),
                )["type"]
            )
        )
    return selected


def _forge_addresses(environment: Mapping[str, str]) -> Mapping[str, Any]:
    payload = environment.get(RUNA_FORGE_ADDRESSES)
    if not payload:
        raise ForgeOperationError(f"missing required forge address payload `{RUNA_FORGE_ADDRESSES}`")
    try:
        data = json.loads(payload)
    except json.JSONDecodeError as error:
        raise ForgeOperationError(f"`{RUNA_FORGE_ADDRESSES}` is not valid JSON: {error}") from error
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ForgeOperationError(f"`{RUNA_FORGE_ADDRESSES}` must be a schema_version 1 object")
    return data


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
