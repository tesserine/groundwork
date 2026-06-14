from __future__ import annotations

import argparse
import json
import os
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
FORGE_ADDRESSES_ENV = "RUNA_PROJECT_FORGE_ADDRESSES"


class ForgeOperationError(ValueError):
    pass


def active_forge_type(environment: Mapping[str, str], override: str | None) -> str:
    if override:
        return override
    payload = _forge_address_payload(environment)
    resources = [*_resource_entries(payload, "repositories"), *_resource_entries(payload, "trackers")]
    forge_types = {
        str(instance.get("type"))
        for resource in resources
        if isinstance(instance := _resource_instance(payload, resource), Mapping)
        and isinstance(instance.get("type"), str)
    }
    if len(forge_types) == 1:
        return forge_types.pop()
    return "github"


def resolve_operation(
    root: Path | str,
    operation: str,
    *,
    forge_type: str | None = None,
    repository_selector: str | None = None,
    tracker_selector: str | None = None,
    environment: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    manifest = _load_toml(root_path / "manifest.toml")
    selected_forge_type = forge_type or _selected_forge_type(
        environment or os.environ,
        repository_selector=repository_selector,
        tracker_selector=tracker_selector,
    )
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


def render_shell_invocation(
    mechanic: Mapping[str, Any],
    values: Mapping[str, str],
    *,
    repository_selector: str | None = None,
    tracker_selector: str | None = None,
) -> tuple[str, dict[str, str]]:
    parameters = _parameters(mechanic)
    deployment_parameters = _deployment_parameters(mechanic)
    provided_deployment_values = sorted(set(values) & set(deployment_parameters))
    if provided_deployment_values:
        raise ForgeOperationError(
            f"deployment-resolved parameter(s) must come from the configured forge address payload: {', '.join(provided_deployment_values)}"
        )
    deployment_values = _deployment_parameter_values(
        mechanic,
        os.environ,
        repository_selector=repository_selector,
        tracker_selector=tracker_selector,
    )
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
    repository_selector: str | None = None,
    tracker_selector: str | None = None,
) -> subprocess.CompletedProcess[str]:
    command, invocation_environment = render_shell_invocation(
        mechanic,
        values,
        repository_selector=repository_selector,
        tracker_selector=tracker_selector,
    )
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
    parser.add_argument("--forge-type", help="Active forge type override for compatibility; selectors normally determine the type.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    resolve_parser = subparsers.add_parser("resolve", help="Print the resolved mechanic path-equivalent name.")
    resolve_parser.add_argument("operation")
    resolve_parser.add_argument("--repository", help="Configured repository selector for repository operations.")
    resolve_parser.add_argument("--tracker", help="Configured tracker selector for tracker operations.")

    inspect_parser = subparsers.add_parser("inspect", help="Print the constant shell invocation body.")
    inspect_parser.add_argument("operation")
    inspect_parser.add_argument("--repository", help="Configured repository selector for repository operations.")
    inspect_parser.add_argument("--tracker", help="Configured tracker selector for tracker operations.")

    run_parser = subparsers.add_parser("run", help="Run the resolved mechanic with parameter bindings.")
    run_parser.add_argument("operation")
    run_parser.add_argument("--repository", help="Configured repository selector for repository operations.")
    run_parser.add_argument("--tracker", help="Configured tracker selector for tracker operations.")
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
            forge_type=args.forge_type,
            repository_selector=args.repository,
            tracker_selector=args.tracker,
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
            result = run_invocation(
                mechanic,
                values,
                cwd=Path.cwd(),
                repository_selector=args.repository,
                tracker_selector=args.tracker,
            )
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
    *,
    repository_selector: str | None = None,
    tracker_selector: str | None = None,
) -> dict[str, str]:
    deployments = _deployment_parameters(mechanic)
    if not deployments:
        return {}
    forge_type = mechanic.get("forge_tag")
    if not isinstance(forge_type, str):
        raise ForgeOperationError("deployment-resolved parameters require mechanic forge_tag")
    resolved = _resolved_deployment_values(
        forge_type,
        set(deployments.values()),
        environment,
        repository_selector=repository_selector,
        tracker_selector=tracker_selector,
    )
    values: dict[str, str] = {}
    for name, deployment_value in deployments.items():
        values[name] = resolved[deployment_value]
    return values


def _resolved_deployment_values(
    forge_type: str,
    deployment_values: set[str],
    environment: Mapping[str, str],
    *,
    repository_selector: str | None = None,
    tracker_selector: str | None = None,
) -> dict[str, str]:
    payload = _forge_address_payload(environment, required=True)
    resource = _selected_resource(
        payload,
        deployment_values,
        repository_selector=repository_selector,
        tracker_selector=tracker_selector,
    )
    instance = _resource_instance(payload, resource)
    return {
        deployment_value: _resolve_deployment_value(
            forge_type,
            deployment_value,
            resource,
            instance,
        )
        for deployment_value in deployment_values
    }


def _resolve_deployment_value(
    forge_type: str,
    deployment_value: str,
    resource: Mapping[str, Any],
    instance: Mapping[str, Any],
) -> str:
    if forge_type == "github":
        if deployment_value == "owner":
            return _required_resource_value(resource, "owner")
        if deployment_value == "name":
            return _required_resource_value(resource, "name")
        if deployment_value == "repository":
            owner = _required_resource_value(resource, "owner")
            name = _required_resource_value(resource, "name")
            return f"{owner}/{name}"
        raise ForgeOperationError(
            f"deployment value `{deployment_value}` is not supported for forge type `{forge_type}`"
        )
    if forge_type == "sourcehut":
        if deployment_value == "owner":
            return _required_resource_value(resource, "owner")
        if deployment_value == "name":
            return _required_resource_value(resource, "name")
        if deployment_value == "repository":
            owner = _required_resource_value(resource, "owner")
            name = _required_resource_value(resource, "name")
            return f"{owner}/{name}"
        if deployment_value == "todo_query_url":
            host = _service_host(instance, "tracker")
            return f"https://{host}/query"
        if deployment_value == "git_query_url":
            host = _service_host(instance, "git")
            return f"https://{host}/query"
        if deployment_value == "ssh_remote":
            host = _service_host(instance, "git")
            owner = _required_resource_value(resource, "owner")
            name = _required_resource_value(resource, "name")
            return f"git@{host}:~{owner}/{name}"
        if deployment_value == "tracker_id":
            return _required_resource_value(resource, "tracker_id")
        raise ForgeOperationError(
            f"deployment value `{deployment_value}` is not supported for forge type `{forge_type}`"
        )
    raise ForgeOperationError(f"forge type `{forge_type}` does not support deployment identity")


def _required_resource_value(resource: Mapping[str, Any], name: str) -> str:
    value = resource.get(name)
    if value is None or value == "":
        raise ForgeOperationError(f"selected forge resource is missing required coordinate `{name}`")
    return str(value)


def _forge_address_payload(
    environment: Mapping[str, str],
    *,
    required: bool = False,
) -> Mapping[str, Any]:
    raw = environment.get(FORGE_ADDRESSES_ENV)
    if not raw:
        if required:
            raise ForgeOperationError(f"missing required forge address payload `{FORGE_ADDRESSES_ENV}`")
        return {}
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ForgeOperationError(f"{FORGE_ADDRESSES_ENV} is not valid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ForgeOperationError(f"{FORGE_ADDRESSES_ENV} must be a JSON object")
    return payload


def _resource_entries(payload: Mapping[str, Any], key: str) -> list[Mapping[str, Any]]:
    collection = payload.get(key, [])
    if isinstance(collection, list):
        return [entry for entry in collection if isinstance(entry, Mapping)]
    if isinstance(collection, Mapping):
        entries = []
        for resource_id, entry in collection.items():
            if isinstance(entry, Mapping):
                merged = dict(entry)
                merged.setdefault("id", resource_id)
                entries.append(merged)
        return entries
    return []


def _resource_instance(payload: Mapping[str, Any], resource: Mapping[str, Any]) -> Mapping[str, Any]:
    instance_id = resource.get("instance")
    instances = payload.get("instances", {})
    if isinstance(instances, Mapping) and instance_id in instances and isinstance(instances[instance_id], Mapping):
        instance = dict(instances[instance_id])
        instance.setdefault("id", instance_id)
        return instance
    for instance in _resource_entries(payload, "instances"):
        if instance.get("id") == instance_id:
            return instance
    raise ForgeOperationError(f"configured resource references unknown forge instance `{instance_id}`")


def _selected_forge_type(
    environment: Mapping[str, str],
    *,
    repository_selector: str | None,
    tracker_selector: str | None,
) -> str:
    payload = _forge_address_payload(environment)
    if not payload:
        return "github"
    resource = _selected_resource(
        payload,
        set(),
        repository_selector=repository_selector,
        tracker_selector=tracker_selector,
    )
    instance = _resource_instance(payload, resource)
    forge_type = instance.get("type")
    if not isinstance(forge_type, str) or not forge_type:
        raise ForgeOperationError("selected forge instance is missing required type")
    return forge_type


def _selected_resource(
    payload: Mapping[str, Any],
    deployment_values: set[str],
    *,
    repository_selector: str | None,
    tracker_selector: str | None,
) -> Mapping[str, Any]:
    if tracker_selector:
        return _select_resource(payload, "trackers", tracker_selector)
    if repository_selector:
        return _select_resource(payload, "repositories", repository_selector)
    if deployment_values & {"tracker_id", "todo_query_url"}:
        return _single_resource(payload, "trackers")
    if deployment_values & {"ssh_remote", "git_query_url"}:
        return _single_resource(payload, "repositories")
    repositories = _resource_entries(payload, "repositories")
    trackers = _resource_entries(payload, "trackers")
    candidates = [*repositories, *trackers]
    if len(candidates) == 1:
        return candidates[0]
    raise ForgeOperationError("forge operation requires --repository or --tracker to select a configured resource")


def _single_resource(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    resources = _resource_entries(payload, key)
    if len(resources) != 1:
        selector = "--repository" if key == "repositories" else "--tracker"
        raise ForgeOperationError(f"forge operation requires {selector} to select one configured resource")
    return resources[0]


def _select_resource(payload: Mapping[str, Any], key: str, selector: str) -> Mapping[str, Any]:
    matches = [resource for resource in _resource_entries(payload, key) if _resource_matches(resource, selector)]
    if len(matches) != 1:
        raise ForgeOperationError(f"selector `{selector}` resolved to {len(matches)} configured resources; expected exactly 1")
    return matches[0]


def _resource_matches(resource: Mapping[str, Any], selector: str) -> bool:
    if resource.get("id") == selector:
        return True
    instance = resource.get("instance")
    owner = resource.get("owner")
    name = resource.get("name")
    if not all(isinstance(value, str) and value for value in [instance, owner, name]):
        return False
    if selector == f"{instance}:{owner}/{name}":
        return True
    tracker_id = resource.get("tracker_id")
    return tracker_id is not None and selector == f"{instance}:{owner}/{name}/{tracker_id}"


def _service_host(instance: Mapping[str, Any], service: str) -> str:
    direct_name = f"{service}_host"
    value = instance.get(direct_name)
    if isinstance(value, str) and value:
        return value
    services = instance.get("services")
    if isinstance(services, Mapping):
        value = services.get(service)
        if isinstance(value, str) and value:
            return value
    value = instance.get("host")
    if service in {"git", "tracker"} and instance.get("type") == "github" and isinstance(value, str) and value:
        return value
    raise ForgeOperationError(f"selected forge instance is missing required `{service}` service host")


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
