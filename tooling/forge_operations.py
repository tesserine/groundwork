from __future__ import annotations

import argparse
import json
import os
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
RUNA_TARGET_PROJECT = "RUNA_TARGET_PROJECT"
RETIRED_RUNA_FORGE_ENVIRONMENT_ATOMS = (
    "RUNA_FORGE_TYPE",
    "RUNA_FORGE_OWNER",
    "RUNA_FORGE_NAME",
    "RUNA_FORGE_TRACKER_ID",
)
RESERVED_SELECTOR_PARAMETERS = {"repository_selector", "tracker_selector"}
SUPPORTED_FORGE_TYPES = {"github", "sourcehut"}


class ForgeOperationError(ValueError):
    pass


def active_forge_type(environment: Mapping[str, str], override: str | None) -> str:
    _reject_retired_runa_forge_environment_atoms(environment)
    if override:
        return override
    return _target_project_forge_type(_target_project(environment))


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
    unknown = sorted(set(values) - set(_parameters(mechanic)) - RESERVED_SELECTOR_PARAMETERS)
    if unknown:
        raise ForgeOperationError(f"unknown parameter(s): {', '.join(unknown)}")
    return _invocation_body(mechanic)


def render_shell_invocation(mechanic: Mapping[str, Any], values: Mapping[str, str]) -> tuple[str, dict[str, str]]:
    parameters = _parameters(mechanic)
    call_values, selector_values = _split_selector_values(values)
    deployment_parameters = _deployment_parameters(mechanic)
    provided_deployment_values = sorted(set(call_values) & set(deployment_parameters))
    if provided_deployment_values:
        raise ForgeOperationError(
            f"deployment-resolved parameter(s) must come from the configured project: {', '.join(provided_deployment_values)}"
        )
    deployment_values = _deployment_parameter_values(mechanic, os.environ, selector_values)
    resolved_values = {**call_values, **deployment_values}
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
        mechanic = resolve_operation(args.root, args.operation)
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
    selectors: Mapping[str, str],
) -> dict[str, str]:
    deployments = _deployment_parameters(mechanic)
    if not deployments:
        return {}
    forge_type = mechanic.get("forge_tag")
    if not isinstance(forge_type, str):
        raise ForgeOperationError("deployment-resolved parameters require mechanic forge_tag")
    resolved = _resolved_deployment_values(forge_type, set(deployments.values()), environment, selectors)
    values: dict[str, str] = {}
    for name, deployment_value in deployments.items():
        values[name] = resolved[deployment_value]
    return values


def _resolved_deployment_values(
    forge_type: str,
    deployment_values: set[str],
    environment: Mapping[str, str],
    selectors: Mapping[str, str],
) -> dict[str, str]:
    _reject_retired_runa_forge_environment_atoms(environment)
    target_project = _target_project(environment)
    project_forge_type = _target_project_forge_type(target_project)
    if project_forge_type != forge_type:
        raise ForgeOperationError(
            f"mechanic forge type `{forge_type}` does not match configured project forge type `{project_forge_type}`"
        )
    return {
        deployment_value: _resolve_deployment_value(forge_type, deployment_value, environment, target_project, selectors)
        for deployment_value in deployment_values
    }


def _resolve_deployment_value(
    forge_type: str,
    deployment_value: str,
    environment: Mapping[str, str],
    target_project: Mapping[str, Any],
    selectors: Mapping[str, str],
) -> str:
    if forge_type == "github":
        repository = _selected_repository(target_project, selectors.get("repository_selector"))
        if deployment_value == "owner":
            return _required_string_field(repository, "owner", "repository")
        if deployment_value == "name":
            return _required_string_field(repository, "name", "repository")
        if deployment_value == "repository":
            owner = _required_string_field(repository, "owner", "repository")
            name = _required_string_field(repository, "name", "repository")
            return f"{owner}/{name}"
        raise ForgeOperationError(
            f"deployment value `{deployment_value}` is not supported for forge type `{forge_type}`"
        )
    if forge_type == "sourcehut":
        tracker = _selected_tracker(target_project, selectors.get("tracker_selector"))
        repository = _selected_sourcehut_repository(target_project, tracker, selectors.get("repository_selector"))
        if deployment_value == "owner":
            return _required_string_field(tracker, "owner", "tracker")
        if deployment_value == "name":
            return _required_string_field(tracker, "name", "tracker")
        if deployment_value == "repository":
            owner = _required_string_field(repository, "owner", "repository")
            name = _required_string_field(repository, "name", "repository")
            return f"{owner}/{name}"
        if deployment_value == "todo_query_url":
            return f"https://todo.{_required_host(tracker, repository, 'tracker')}/query"
        if deployment_value == "git_query_url":
            return f"https://git.{_required_host(repository, tracker, 'repository')}/query"
        if deployment_value == "ssh_remote":
            endpoint = _required_host(repository, tracker, "repository")
            owner = _required_string_field(repository, "owner", "repository")
            name = _required_string_field(repository, "name", "repository")
            return f"git@git.{endpoint}:~{owner}/{name}"
        if deployment_value == "tracker_id":
            return _required_string_field(tracker, "tracker_id", "tracker")
        if deployment_value == "repo_id":
            return _required_environment(environment, "GROUNDWORK_FORGE_REPO_ID")
        raise ForgeOperationError(
            f"deployment value `{deployment_value}` is not supported for forge type `{forge_type}`"
        )
    raise ForgeOperationError(f"forge type `{forge_type}` does not support deployment identity")


def _split_selector_values(values: Mapping[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    call_values: dict[str, str] = {}
    selector_values: dict[str, str] = {}
    for name, value in values.items():
        if name in RESERVED_SELECTOR_PARAMETERS:
            selector_values[name] = str(value)
        else:
            call_values[name] = str(value)
    return call_values, selector_values


def _reject_retired_runa_forge_environment_atoms(environment: Mapping[str, str]) -> None:
    present = sorted(atom for atom in RETIRED_RUNA_FORGE_ENVIRONMENT_ATOMS if environment.get(atom))
    if present:
        raise ForgeOperationError(
            "retired runa forge environment atom(s) are not supported; use "
            f"{RUNA_TARGET_PROJECT}: {', '.join(present)}"
        )


def _target_project(environment: Mapping[str, str]) -> Mapping[str, Any]:
    raw_payload = _required_environment(environment, RUNA_TARGET_PROJECT)
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as error:
        raise ForgeOperationError(f"{RUNA_TARGET_PROJECT} must contain a JSON project payload: {error}") from error
    if not isinstance(payload, dict):
        raise ForgeOperationError(f"{RUNA_TARGET_PROJECT} must contain a JSON object")
    return payload


def _target_project_forge_type(target_project: Mapping[str, Any]) -> str:
    forge_type = target_project.get("forge_type")
    if not isinstance(forge_type, str) or forge_type not in SUPPORTED_FORGE_TYPES:
        raise ForgeOperationError(f"{RUNA_TARGET_PROJECT} must name a supported forge_type")
    return forge_type


def _selected_repository(target_project: Mapping[str, Any], selector: str | None) -> Mapping[str, Any]:
    repositories = _target_project_items(target_project, "repositories", "repository")
    if selector:
        for repository in repositories:
            if repository.get("selector") == selector:
                return repository
        raise ForgeOperationError(f"repository selector `{selector}` does not resolve in {RUNA_TARGET_PROJECT}")
    if len(repositories) == 1:
        return repositories[0]
    if not repositories:
        raise ForgeOperationError(f"{RUNA_TARGET_PROJECT} does not declare a repository")
    raise ForgeOperationError(
        "repository_selector is required when the configured project declares multiple repositories: "
        + ", ".join(_selectors(repositories))
    )


def _selected_tracker(target_project: Mapping[str, Any], selector: str | None) -> Mapping[str, Any]:
    trackers = _target_project_items(target_project, "trackers", "tracker")
    if selector:
        for tracker in trackers:
            if tracker.get("selector") == selector:
                return tracker
        raise ForgeOperationError(f"tracker selector `{selector}` does not resolve in {RUNA_TARGET_PROJECT}")
    if len(trackers) == 1:
        return trackers[0]
    if not trackers:
        raise ForgeOperationError(f"{RUNA_TARGET_PROJECT} does not declare a tracker")
    raise ForgeOperationError(
        "tracker_selector is required when the configured project declares multiple trackers: "
        + ", ".join(_selectors(trackers))
    )


def _selected_sourcehut_repository(
    target_project: Mapping[str, Any],
    tracker: Mapping[str, Any],
    selector: str | None,
) -> Mapping[str, Any]:
    if selector:
        return _selected_repository(target_project, selector)
    tracker_repository = tracker.get("repository")
    if isinstance(tracker_repository, str) and tracker_repository:
        return _selected_repository(target_project, tracker_repository)
    return _selected_repository(target_project, None)


def _target_project_items(target_project: Mapping[str, Any], key: str, item_name: str) -> list[Mapping[str, Any]]:
    raw_items = target_project.get(key, [])
    if not isinstance(raw_items, list):
        raise ForgeOperationError(f"{RUNA_TARGET_PROJECT}.{key} must be a list")
    items: list[Mapping[str, Any]] = []
    for index, item in enumerate(raw_items):
        if not isinstance(item, dict):
            raise ForgeOperationError(f"{RUNA_TARGET_PROJECT}.{key}[{index}] must be a {item_name} object")
        items.append(item)
    return items


def _selectors(items: list[Mapping[str, Any]]) -> list[str]:
    return [str(item.get("selector")) for item in items if isinstance(item.get("selector"), str)]


def _required_string_field(item: Mapping[str, Any], key: str, item_name: str) -> str:
    value = item.get(key)
    if not isinstance(value, str) or not value:
        raise ForgeOperationError(f"configured {item_name} is missing required field `{key}`")
    return value


def _required_host(primary: Mapping[str, Any], fallback: Mapping[str, Any], item_name: str) -> str:
    value = primary.get("host")
    if isinstance(value, str) and value:
        return value
    fallback_value = fallback.get("host")
    if isinstance(fallback_value, str) and fallback_value:
        return fallback_value
    raise ForgeOperationError(f"configured {item_name} is missing required field `host`")


def _required_environment(environment: Mapping[str, str], name: str) -> str:
    value = environment.get(name)
    if value is None or value == "":
        raise ForgeOperationError(f"missing required environment variable `{name}`")
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
