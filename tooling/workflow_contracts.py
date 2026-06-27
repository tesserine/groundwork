from __future__ import annotations

import json
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from tooling.forge_capability import operation_names as forge_operation_names


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest.toml"
WORKFLOW_CONTRACT_SCHEMA = ROOT / "schemas" / "workflow-contract.schema.json"


class WorkflowContractError(ValueError):
    def __init__(self, errors: list[tuple[str, str]]) -> None:
        self.errors = errors
        self.paths = [path for path, _message in errors]
        super().__init__(self._format())

    def _format(self) -> str:
        return "; ".join(f"{path}: {message}" for path, message in self.errors)


@dataclass(frozen=True)
class WorkflowRegistry:
    disciplines: set[str] = field(default_factory=set)
    mechanics: set[str] = field(default_factory=set)
    artifact_schemas: set[str] = field(default_factory=set)
    outcome_types: set[str] = field(default_factory=set)
    required_output_choices: dict[str, list[dict[str, Any]]] = field(default_factory=dict)


def workflow_registry_from_manifest(
    path: Path | str = MANIFEST,
    root: Path | str | None = None,
) -> WorkflowRegistry:
    manifest_path = Path(path)
    root_path = Path(root) if root is not None else manifest_path.parent
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))

    artifact_types = {
        entry["name"]
        for entry in manifest.get("artifact_types", [])
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    outcome_types = {
        entry["name"]
        for entry in manifest.get("outcome_types", [])
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    required_output_choices = {
        entry["name"]: [
            {
                "name": choice["name"],
                "members": list(choice["members"]),
            }
            for choice in entry.get("required_output_choices", [])
            if isinstance(choice, dict)
            and isinstance(choice.get("name"), str)
            and isinstance(choice.get("members"), list)
            and all(isinstance(member, str) for member in choice["members"])
        ]
        for entry in manifest.get("protocols", [])
        if isinstance(entry, dict)
        and isinstance(entry.get("name"), str)
        and isinstance(entry.get("required_output_choices"), list)
    }
    mechanic_names = {
        entry["name"]
        for entry in manifest.get("mechanics", [])
        if isinstance(entry, dict) and isinstance(entry.get("name"), str)
    }
    mechanic_names.update(_mechanic_names_from_directory(root_path / "mechanics"))
    if (root_path / "schemas" / "forge-capability" / "v1" / "forge-capability.schema.json").exists() or root_path.resolve() == ROOT:
        mechanic_names.update(forge_operation_names())

    return WorkflowRegistry(
        disciplines=_directory_names(root_path / "skills") | _directory_names(root_path / "protocols"),
        mechanics=mechanic_names,
        artifact_schemas=artifact_types,
        outcome_types=outcome_types,
        required_output_choices=required_output_choices,
    )


def load_workflow_contract(path: Path | str, registry: WorkflowRegistry | None = None) -> dict[str, Any]:
    contract_path = Path(path)
    try:
        contract = tomllib.loads(contract_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        raise WorkflowContractError([("<toml>", f"{contract_path.name} is invalid TOML: {error}")]) from error

    validate_workflow_contract(contract, registry=registry)
    return contract


def validate_workflow_contract(contract: dict[str, Any], registry: WorkflowRegistry | None = None) -> None:
    errors: list[tuple[str, str]] = []
    errors.extend(_schema_errors(contract))
    if errors:
        raise WorkflowContractError(errors)

    errors.extend(_graph_errors(contract))
    if registry is not None:
        errors.extend(_registry_errors(contract, registry))

    if errors:
        raise WorkflowContractError(errors)


def _directory_names(directory: Path) -> set[str]:
    if not directory.exists():
        return set()
    return {entry.name for entry in directory.iterdir() if entry.is_dir()}


def _mechanic_names_from_directory(directory: Path) -> set[str]:
    if not directory.exists():
        return set()

    names: set[str] = set()
    for path in directory.rglob("*.toml"):
        try:
            mechanic = tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError):
            continue
        name = mechanic.get("name")
        if isinstance(name, str):
            names.add(name)
    return names


def _schema_errors(contract: dict[str, Any]) -> list[tuple[str, str]]:
    schema = json.loads(WORKFLOW_CONTRACT_SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    errors: list[tuple[str, str]] = []

    for error in sorted(validator.iter_errors(contract), key=lambda item: list(item.path)):
        path = "/".join(str(part) for part in error.path)
        if error.validator == "required":
            missing = error.message.split("'")[1]
            path = f"{path}/{missing}" if path else missing
        errors.append((path or "<root>", error.message))

    return errors


def _graph_errors(contract: dict[str, Any]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    nodes = contract["nodes"]
    edges = contract["edges"]
    terminals = contract["terminals"]
    node_names = [node["name"] for node in nodes]
    terminal_names = [terminal["name"] for terminal in terminals]
    node_name_set = set(node_names)
    terminal_name_set = set(terminal_names)
    target_names = node_name_set | terminal_name_set
    start_node = contract["start_node"]

    errors.extend(_duplicate_name_errors("nodes", node_names))
    errors.extend(_duplicate_name_errors("terminals", terminal_names))
    errors.extend(_name_collision_errors(node_name_set, terminal_names))

    if start_node not in node_name_set:
        errors.append(("start_node", f"start_node `{start_node}` does not reference a declared node"))

    for index, edge in enumerate(edges):
        from_name = edge["from"]
        to_name = edge["to"]
        if from_name not in node_name_set:
            errors.append(
                (
                    f"edges/{index}/from",
                    f"edge `{from_name} -> {to_name}` references unknown source `{from_name}`",
                )
            )
        if to_name not in target_names:
            errors.append(
                (
                    f"edges/{index}/to",
                    f"edge `{from_name} -> {to_name}` references unknown target `{to_name}`",
                )
            )

    errors.extend(_condition_errors(edges))

    graph_names_are_unambiguous = not any(path.endswith("/name") for path, _message in errors)
    graph_edges_are_resolved = not any(path.startswith("edges/") for path, _message in errors)
    if graph_names_are_unambiguous and graph_edges_are_resolved and start_node in node_name_set:
        errors.extend(_reachability_errors(contract, node_name_set, terminal_name_set))
        errors.extend(_loop_errors(edges, node_names))

    return errors


def _duplicate_name_errors(collection: str, names: list[str]) -> list[tuple[str, str]]:
    seen: set[str] = set()
    errors: list[tuple[str, str]] = []
    for index, name in enumerate(names):
        if name in seen:
            errors.append((f"{collection}/{index}/name", f"duplicate {collection[:-1]} name `{name}`"))
        seen.add(name)
    return errors


def _name_collision_errors(node_names: set[str], terminal_names: list[str]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for index, name in enumerate(terminal_names):
        if name in node_names:
            errors.append((f"terminals/{index}/name", f"name `{name}` is declared as both a node and a terminal"))
    return errors


def _condition_errors(edges: list[dict[str, Any]]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    by_source: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for index, edge in enumerate(edges):
        by_source.setdefault(edge["from"], []).append((index, edge))

    for source, outgoing in by_source.items():
        if len(outgoing) == 1:
            continue

        fields: set[str] = set()
        case_values: set[str] = set()
        default_seen = False
        for index, edge in outgoing:
            condition = edge["condition"]
            condition_type = condition["type"]
            if condition_type == "always":
                errors.append(
                    (
                        f"edges/{index}/condition",
                        f"node `{source}` mixes an always condition with other outgoing edges",
                    )
                )
                continue

            fields.add(condition["field"])
            if condition_type == "default":
                if default_seen:
                    errors.append(
                        (
                            f"edges/{index}/condition",
                            f"node `{source}` has multiple default outgoing edges",
                        )
                    )
                default_seen = True
                continue

            case_value = condition["equals"]
            if case_value in case_values:
                edges_to = " and ".join(
                    f"`{edge['to']}`"
                    for _index, edge in outgoing
                    if edge["condition"].get("equals") == case_value
                )
                errors.append(
                    (
                        f"edges/{index}/condition",
                        f"node `{source}` has overlapping conditions on outgoing edges to {edges_to}",
                    )
                )
            case_values.add(case_value)

        if len(fields) > 1:
            first_index = outgoing[0][0]
            errors.append(
                (
                    f"edges/{first_index}/condition",
                    f"node `{source}` uses multiple decision fields on outgoing edges",
                )
            )

    return errors


def _reachability_errors(
    contract: dict[str, Any],
    node_names: set[str],
    terminal_names: set[str],
) -> list[tuple[str, str]]:
    adjacency: dict[str, list[str]] = {node: [] for node in node_names}
    reverse_adjacency: dict[str, list[str]] = {name: [] for name in node_names | terminal_names}
    for edge in contract["edges"]:
        adjacency[edge["from"]].append(edge["to"])
        reverse_adjacency[edge["to"]].append(edge["from"])

    reachable: set[str] = set()
    stack = [contract["start_node"]]
    while stack:
        current = stack.pop()
        if current in reachable:
            continue
        reachable.add(current)
        stack.extend(adjacency.get(current, []))

    terminal_reaching: set[str] = set()
    stack = list(terminal_names)
    while stack:
        current = stack.pop()
        if current in terminal_reaching:
            continue
        terminal_reaching.add(current)
        stack.extend(reverse_adjacency.get(current, []))

    errors: list[tuple[str, str]] = []
    for index, node in enumerate(contract["nodes"]):
        node_name = node["name"]
        if node_name not in reachable:
            errors.append(
                (
                    f"nodes/{index}",
                    f"node `{node_name}` is not reachable from start_node `{contract['start_node']}`",
                )
            )
        elif node_name not in terminal_reaching:
            errors.append((f"nodes/{index}", f"node `{node_name}` cannot reach any terminal"))
    for index, terminal in enumerate(contract["terminals"]):
        if terminal["name"] not in reachable:
            errors.append(
                (
                    f"terminals/{index}",
                    f"terminal `{terminal['name']}` is not reachable from start_node `{contract['start_node']}`",
                )
            )
    return errors


def _loop_errors(
    edges: list[dict[str, Any]],
    node_names: list[str],
) -> list[tuple[str, str]]:
    node_name_set = set(node_names)
    adjacency: dict[str, list[str]] = {node: [] for node in node_names}
    for edge in edges:
        if edge["to"] in node_name_set:
            adjacency[edge["from"]].append(edge["to"])

    errors: list[tuple[str, str]] = []
    for component in _strongly_connected_components(adjacency):
        if not _is_loop(component, adjacency):
            continue
        has_exit = any(edge["from"] in component and edge["to"] not in component for edge in edges)
        if not has_exit:
            names = ", ".join(node for node in node_names if node in component)
            errors.append(("edges", f"loop `{names}` has no termination edge"))

    return errors


def _strongly_connected_components(adjacency: dict[str, list[str]]) -> list[set[str]]:
    index = 0
    stack: list[str] = []
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    on_stack: set[str] = set()
    components: list[set[str]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = index
        lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)

        for target in adjacency[node]:
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])

        if lowlinks[node] == indices[node]:
            component: set[str] = set()
            while True:
                member = stack.pop()
                on_stack.remove(member)
                component.add(member)
                if member == node:
                    break
            components.append(component)

    for node in adjacency:
        if node not in indices:
            visit(node)

    return components


def _is_loop(component: set[str], adjacency: dict[str, list[str]]) -> bool:
    if len(component) > 1:
        return True
    node = next(iter(component))
    return node in adjacency[node]


def _registry_errors(contract: dict[str, Any], registry: WorkflowRegistry) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    for node_index, node in enumerate(contract["nodes"]):
        for discipline_index, discipline in enumerate(node["disciplines"]):
            if discipline not in registry.disciplines:
                errors.append(
                    (
                        f"nodes/{node_index}/disciplines/{discipline_index}",
                        f"discipline `{discipline}` does not resolve in registry",
                    )
                )
        for mechanic_index, mechanic in enumerate(node["mechanics"]):
            if mechanic not in registry.mechanics:
                errors.append(
                    (
                        f"nodes/{node_index}/mechanics/{mechanic_index}",
                        f"mechanic `{mechanic}` does not resolve in registry",
                    )
                )

    for terminal_index, terminal in enumerate(contract["terminals"]):
        artifact = terminal["artifact_produced"]
        if artifact not in registry.artifact_schemas:
            errors.append(
                (
                    f"terminals/{terminal_index}/artifact_produced",
                    f"artifact schema `{artifact}` does not resolve in registry",
                )
            )

    errors.extend(_outcome_terminal_errors(contract, registry))

    return errors


def _outcome_terminal_errors(contract: dict[str, Any], registry: WorkflowRegistry) -> list[tuple[str, str]]:
    outcome_terminal_artifacts = [
        terminal["artifact_produced"]
        for terminal in contract["terminals"]
        if terminal["artifact_produced"] in registry.outcome_types
    ]
    manifest_choices = registry.required_output_choices.get(contract["name"], [])

    errors: list[tuple[str, str]] = []
    seen: set[str] = set()
    for terminal_index, terminal in enumerate(contract["terminals"]):
        artifact = terminal["artifact_produced"]
        if artifact not in registry.outcome_types:
            continue
        if artifact in seen:
            errors.append(
                (
                    f"terminals/{terminal_index}/artifact_produced",
                    f"outcome terminal repeats artifact_produced `{artifact}`",
                )
            )
        seen.add(artifact)

    if len(manifest_choices) > 1:
        errors.append(
            (
                "terminals",
                f"protocol `{contract['name']}` declares {len(manifest_choices)} "
                "manifest required_output_choices groups; outcome terminals require exactly one group",
            )
        )
        return errors

    if not manifest_choices:
        if outcome_terminal_artifacts:
            errors.append(
                (
                    "terminals",
                    f"outcome terminals for protocol `{contract['name']}` require exactly one "
                    "manifest required_output_choices group",
                )
            )
        return errors

    manifest_choice = manifest_choices[0]
    manifest_members = set(manifest_choice["members"])
    for terminal_index, terminal in enumerate(contract["terminals"]):
        artifact = terminal["artifact_produced"]
        if artifact not in manifest_members:
            errors.append(
                (
                    f"terminals/{terminal_index}/artifact_produced",
                    f"terminal artifact_produced `{artifact}` is not a member of "
                    f"manifest required_output_choices `{manifest_choice['name']}`",
                )
            )

    if not outcome_terminal_artifacts:
        errors.append(
            (
                "terminals",
                f"manifest required_output_choices declared for protocol `{contract['name']}` "
                "but workflow contract has no outcome terminals",
            )
        )

    terminal_members = set(outcome_terminal_artifacts)
    if manifest_members != terminal_members:
        errors.append(
            (
                "terminals",
                f"manifest required_output_choices `{manifest_choice['name']}` members "
                f"{sorted(manifest_members)} do not match outcome terminal artifact_produced values "
                f"{sorted(terminal_members)}",
            )
        )

    return errors
