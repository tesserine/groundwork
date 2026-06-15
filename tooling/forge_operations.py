from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any, Mapping

def _runtime_root() -> Path:
    candidate = Path(__file__).resolve().parents[1]
    if (candidate / "manifest.toml").exists() or (candidate / "schemas").exists():
        return candidate
    installed = candidate.parent
    if (installed / "manifest.toml").exists() or (installed / "schemas").exists():
        return installed
    return candidate


ROOT = _runtime_root()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "lib") not in sys.path:
    sys.path.insert(0, str(ROOT / "lib"))

from tooling.forge_address import ForgeAddressContractError, validate_contract_value

MECHANIC_SCHEMA = ROOT / "schemas" / "mechanic.schema.json"
RUNA_FORGE_ADDRESSES = "RUNA_FORGE_ADDRESSES"
TRACKER_OPERATIONS = {
    "claim-work-unit",
    "close-out",
    "create-ticket",
    "read-ticket",
    "record-progress",
    "reflect-disposition",
}


class ForgeOperationError(ValueError):
    pass


def active_forge_type(environment: Mapping[str, str], override: str | None) -> str:
    if override:
        return override
    return "github"


def resolve_operation(
    root: Path | str,
    operation: str,
    *,
    forge_type: str | None = None,
    repository: str | None = None,
    tracker: str | None = None,
) -> dict[str, Any]:
    root_path = Path(root)
    manifest = _load_toml(root_path / "manifest.toml")
    resource = _selected_resource(operation, repository=repository, tracker=tracker, environment=os.environ)
    selected_forge_type = resource["forge_type"] if resource is not None else active_forge_type(os.environ, forge_type)
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
    mechanic = dict(matches[0])
    if resource is not None:
        mechanic["_groundwork_resource"] = resource
    return mechanic


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
    parser.add_argument("--forge-type", help=argparse.SUPPRESS)
    parser.add_argument("--repository", help="Repository selector from RUNA_FORGE_ADDRESSES.")
    parser.add_argument("--tracker", help="Tracker selector from RUNA_FORGE_ADDRESSES.")
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
            forge_type=args.forge_type,
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
    forge_type = mechanic.get("forge_tag")
    if not isinstance(forge_type, str):
        raise ForgeOperationError("deployment-resolved parameters require mechanic forge_tag")
    resource = mechanic.get("_groundwork_resource")
    resolved = _resolved_deployment_values(
        forge_type,
        set(deployments.values()),
        environment,
        resource if isinstance(resource, dict) else None,
    )
    values: dict[str, str] = {}
    for name, deployment_value in deployments.items():
        values[name] = resolved[deployment_value]
    return values


def _resolved_deployment_values(
    forge_type: str,
    deployment_values: set[str],
    environment: Mapping[str, str],
    resource: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    return {
        deployment_value: _resolve_deployment_value(forge_type, deployment_value, environment, resource)
        for deployment_value in deployment_values
    }


def _resolve_deployment_value(
    forge_type: str,
    deployment_value: str,
    environment: Mapping[str, str],
    resource: Mapping[str, Any] | None = None,
) -> str:
    if deployment_value not in deployment_value_vocabulary():
        raise ForgeOperationError(f"deployment value `{deployment_value}` is not declared by mechanic.schema.json")
    if resource is not None:
        return _resolve_resource_deployment_value(forge_type, deployment_value, resource)
    raise ForgeOperationError(
        f"deployment value `{deployment_value}` requires --repository or --tracker with {RUNA_FORGE_ADDRESSES}"
    )


def deployment_value_vocabulary() -> set[str]:
    schema = json.loads(MECHANIC_SCHEMA.read_text(encoding="utf-8"))
    values = schema["$defs"]["parameter"]["properties"]["deployment_value"]["enum"]
    return {str(value) for value in values}


def _selected_resource(
    operation: str,
    *,
    repository: str | None,
    tracker: str | None,
    environment: Mapping[str, str],
) -> dict[str, Any] | None:
    if repository and tracker:
        raise ForgeOperationError("--repository and --tracker are mutually exclusive")
    if not repository and not tracker:
        return None

    payload = _address_payload(environment)
    if repository:
        resource = _named_resource(payload, "repositories", repository)
        instance = _instance(payload, resource["instance"])
        forge_type = instance["type"]
        tracker_resource = _tracker_for_repository(payload, resource) if forge_type == "github" else None
        if operation in TRACKER_OPERATIONS and forge_type != "github":
            raise ForgeOperationError(f"operation `{operation}` requires --tracker for sourcehut resources")
        return {
            "kind": "repository",
            "forge_type": forge_type,
            "resource": resource,
            "instance": instance,
            "tracker": tracker_resource,
        }

    assert tracker is not None
    resource = _named_resource(payload, "trackers", tracker)
    forge_type = resource["type"]
    if forge_type == "github":
        raise ForgeOperationError(f"github operation `{operation}` must use --repository")
    return {
        "kind": "tracker",
        "forge_type": forge_type,
        "resource": resource,
        "instance": _instance(payload, resource["instance"]),
        "tracker": resource,
    }


def _address_payload(environment: Mapping[str, str]) -> Mapping[str, Any]:
    raw = environment.get(RUNA_FORGE_ADDRESSES)
    if not raw:
        raise ForgeOperationError(f"missing required {RUNA_FORGE_ADDRESSES} payload")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ForgeOperationError(f"{RUNA_FORGE_ADDRESSES} is invalid JSON: {error}") from error
    if not isinstance(payload, dict):
        raise ForgeOperationError(f"{RUNA_FORGE_ADDRESSES} must be a JSON object")
    try:
        validate_contract_value(payload)
    except ForgeAddressContractError as error:
        raise ForgeOperationError(f"{RUNA_FORGE_ADDRESSES} does not match forge-address schema: {error}") from error
    return payload


def _named_resource(payload: Mapping[str, Any], collection: str, name: str) -> Mapping[str, Any]:
    matches = [
        resource
        for resource in payload.get(collection, [])
        if isinstance(resource, dict) and resource.get("name") == name
    ]
    if len(matches) != 1:
        raise ForgeOperationError(f"{collection[:-1]} selector `{name}` resolved to {len(matches)} resources; expected exactly 1")
    return matches[0]


def _instance(payload: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    return _named_resource(payload, "instances", name)


def _tracker_for_repository(payload: Mapping[str, Any], repository: Mapping[str, Any]) -> Mapping[str, Any]:
    matches = [
        tracker
        for tracker in payload.get("trackers", [])
        if (
            isinstance(tracker, dict)
            and tracker.get("type") == "github"
            and tracker.get("repository") == repository.get("name")
        )
    ]
    if len(matches) != 1:
        raise ForgeOperationError(
            f"github repository selector `{repository.get('name')}` resolved to {len(matches)} trackers; expected exactly 1"
        )
    return matches[0]


def _resolve_resource_deployment_value(
    forge_type: str,
    deployment_value: str,
    selected: Mapping[str, Any],
) -> str:
    resource = selected["resource"]
    instance = selected["instance"]
    if deployment_value == "owner":
        return _bare_owner(str(resource["owner"]))
    if deployment_value == "name":
        return str(resource.get("repository") or resource.get("tracker"))
    if deployment_value == "tracker":
        tracker = selected.get("tracker")
        if not isinstance(tracker, dict):
            raise ForgeOperationError("deployment value `tracker` requires a tracker-backed selector")
        return str(tracker["name"])
    if deployment_value == "tracker_identity":
        tracker = selected.get("tracker")
        if not isinstance(tracker, dict):
            raise ForgeOperationError("deployment value `tracker_identity` requires a tracker-backed selector")
        return str(tracker["identity"])
    if deployment_value == "repository":
        if selected["kind"] != "repository":
            raise ForgeOperationError("deployment value `repository` requires a repository selector")
        return f"{_bare_owner(str(resource['owner']))}/{resource['repository']}"
    if deployment_value == "todo_query_url":
        if forge_type != "sourcehut":
            raise ForgeOperationError("deployment value `todo_query_url` requires a sourcehut resource")
        return f"https://{instance['tracker_host']}/query"
    if deployment_value == "git_query_url":
        if forge_type != "sourcehut":
            raise ForgeOperationError("deployment value `git_query_url` requires a sourcehut resource")
        return f"https://{instance['git_host']}/query"
    if deployment_value == "ssh_remote":
        if selected["kind"] != "repository" or forge_type != "sourcehut":
            raise ForgeOperationError("deployment value `ssh_remote` requires a sourcehut repository selector")
        return f"git@{instance['git_host']}:{_canonical_sourcehut_owner(str(resource['owner']))}/{resource['repository']}"
    if deployment_value == "tracker_id":
        if selected["kind"] != "tracker":
            raise ForgeOperationError("deployment value `tracker_id` requires a tracker selector")
        return str(resource["tracker_id"])
    if deployment_value == "repo_id":
        raise ForgeOperationError("deployment value `repo_id` is declared but not provided by the forge-address contract")
    raise ForgeOperationError(f"deployment value `{deployment_value}` is not supported for forge type `{forge_type}`")


def _bare_owner(owner: str) -> str:
    return owner.removeprefix("~")


def _canonical_sourcehut_owner(owner: str) -> str:
    return "~" + _bare_owner(owner)


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
