import tempfile
import unittest
from pathlib import Path

from tooling.artifact_schemas import registry_from_manifest
from tooling.mechanics import (
    MechanicError,
    MechanicRegistry,
    load_mechanic,
    validate_mechanic,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "mechanics"


class MechanicTests(unittest.TestCase):
    def fixture(self, name: str) -> Path:
        return FIXTURES / name

    def test_schema_accepts_forge_neutral_git_mechanic(self) -> None:
        mechanic = load_mechanic(self.fixture("valid-git.toml"))

        self.assertEqual(mechanic["name"], "git-push")

    def test_schema_accepts_generic_runtime_mcp_tool_mechanic(self) -> None:
        mechanic = load_mechanic(self.fixture("valid-mcp-tool.toml"))

        self.assertNotIn("forge_tag", mechanic)

    def test_schema_accepts_secret_parameter_metadata(self) -> None:
        mechanic = {
            "name": "sourcehut-upload",
            "purpose": "Upload with a bearer token.",
            "default_invocation": 'curl --header "Authorization: Bearer ${token}" "${url}"',
            "examples": ['curl --header "Authorization: Bearer ${token}" "${url}"'],
            "parameters": [
                {"name": "token", "purpose": "Bearer token.", "required": True, "secret": True},
                {"name": "url", "purpose": "Endpoint URL.", "required": True},
            ],
            "outcome": {"description": "Uploaded."},
        }

        validate_mechanic(mechanic)

    def test_schema_accepts_deployment_value_parameter_metadata(self) -> None:
        mechanic = {
            "name": "sourcehut-upload",
            "purpose": "Upload to a configured forge repository.",
            "default_invocation": 'printf "%s\\n" "$repo_number"',
            "examples": ['printf "%s\\n" "$repo_number"'],
            "parameters": [
                {
                    "name": "repo_number",
                    "purpose": "Configured forge repository ID.",
                    "required": True,
                    "deployment_value": "repo_id",
                }
            ],
            "outcome": {"description": "Printed."},
        }

        validate_mechanic(mechanic)

    def test_schema_rejects_secret_deployment_value_parameter_conflict(self) -> None:
        mechanic = {
            "name": "sourcehut-upload",
            "purpose": "Upload to a configured forge repository.",
            "default_invocation": 'printf "%s\\n" "$repo_number"',
            "examples": ['printf "%s\\n" "$repo_number"'],
            "parameters": [
                {
                    "name": "repo_number",
                    "purpose": "Configured forge repository ID.",
                    "required": True,
                    "secret": True,
                    "deployment_value": "repo_id",
                }
            ],
            "outcome": {"description": "Printed."},
        }

        with self.assertRaises(MechanicError) as context:
            validate_mechanic(mechanic)

        self.assertIn("parameters/0/deployment_value", context.exception.paths)
        self.assertIn("must not also be secret", str(context.exception))

    def test_invocation_rejects_bare_placeholder_parameters(self) -> None:
        mechanic = {
            "name": "git-push",
            "purpose": "Push a branch.",
            "default_invocation": "git push {remote} {branch}",
            "examples": ["git push origin main"],
            "parameters": [
                {"name": "remote", "purpose": "Remote.", "required": True},
                {"name": "branch", "purpose": "Branch.", "required": True},
            ],
            "outcome": {"description": "Pushed."},
        }

        with self.assertRaises(MechanicError) as context:
            validate_mechanic(mechanic)

        self.assertIn("default_invocation", context.exception.paths)
        self.assertIn("bare placeholder", str(context.exception))

    def test_invocation_accepts_quoted_embedded_language_braces(self) -> None:
        mechanic = {
            "name": "awk-print",
            "purpose": "Print a file with awk.",
            "default_invocation": """awk '{print}' "$file" """,
            "examples": ["""awk '{print}' "$file" """],
            "parameters": [{"name": "file", "purpose": "File to print.", "required": True}],
            "outcome": {"description": "Printed."},
        }

        validate_mechanic(mechanic)

    def test_invocation_rejects_unparseable_shell(self) -> None:
        mechanic = {
            "name": "git-push",
            "purpose": "Push a branch.",
            "default_invocation": 'git push "${remote}',
            "examples": ['git push "${remote}'],
            "parameters": [{"name": "remote", "purpose": "Remote.", "required": True}],
            "outcome": {"description": "Pushed."},
        }

        with self.assertRaises(MechanicError) as context:
            validate_mechanic(mechanic)

        self.assertIn("default_invocation", context.exception.paths)
        self.assertIn("valid /bin/sh", str(context.exception))

    def test_invocation_rejects_declared_parameter_that_shell_does_not_expand(self) -> None:
        mechanic = {
            "name": "git-push",
            "purpose": "Push a branch.",
            "default_invocation": "printf '%s\\n' '$remote'",
            "examples": ["printf '%s\\n' '$remote'"],
            "parameters": [{"name": "remote", "purpose": "Remote.", "required": True}],
            "outcome": {"description": "Pushed."},
        }

        with self.assertRaises(MechanicError) as context:
            validate_mechanic(mechanic)

        self.assertIn("parameters/0/name", context.exception.paths)
        self.assertIn("not expanded by /bin/sh", str(context.exception))

    def test_schema_rejects_parameter_names_that_cannot_be_environment_variables(self) -> None:
        mechanic = {
            "name": "bad-param",
            "purpose": "Bad parameter name.",
            "default_invocation": 'printf "%s\\n" "${bad-name}"',
            "examples": ['printf "%s\\n" "${bad-name}"'],
            "parameters": [{"name": "bad-name", "purpose": "Bad.", "required": True}],
            "outcome": {"description": "Rejected."},
        }

        with self.assertRaises(MechanicError) as context:
            validate_mechanic(mechanic)

        self.assertIn("parameters/0/name", context.exception.paths)

    def test_schema_rejects_malformed_shape_with_field_paths(self) -> None:
        with self.assertRaises(MechanicError) as context:
            load_mechanic(self.fixture("invalid-malformed-shape.toml"))

        self.assertIn("purpose", context.exception.paths)
        self.assertIn("parameters", context.exception.paths)
        self.assertIn("purpose", str(context.exception))

    def test_schema_rejects_missing_required_fields_with_field_paths(self) -> None:
        with self.assertRaises(MechanicError) as context:
            load_mechanic(self.fixture("invalid-missing-required.toml"))

        self.assertIn("purpose", context.exception.paths)
        self.assertIn("outcome", context.exception.paths)

    def test_schema_rejects_retired_forge_tag_field(self) -> None:
        with self.assertRaises(MechanicError) as context:
            load_mechanic(self.fixture("valid-github.toml"))

        self.assertIn("forge_tag", str(context.exception))

    def test_schema_rejects_empty_examples_with_field_path(self) -> None:
        with self.assertRaises(MechanicError) as context:
            load_mechanic(self.fixture("invalid-empty-examples.toml"))

        self.assertIn("examples", context.exception.paths)

    def test_registry_resolution_can_be_deferred_when_no_registry_is_loaded(self) -> None:
        mechanic = load_mechanic(self.fixture("invalid-registry-reference.toml"), registry=None)

        self.assertEqual(mechanic["name"], "deliver-artifact")

    def test_registry_resolution_rejects_unknown_references_when_registry_is_loaded(self) -> None:
        registry = MechanicRegistry(
            artifact_schemas={"completion-evidence"},
            artifact_types={"completion-evidence"},
        )

        with self.assertRaises(MechanicError) as context:
            load_mechanic(self.fixture("invalid-registry-reference.toml"), registry=registry)

        self.assertIn("parameters/0/schema_ref", context.exception.paths)
        self.assertIn("outcome/artifact_type", context.exception.paths)
        self.assertIn("artifact schema `missing-schema` does not resolve in registry", str(context.exception))

    def test_registry_resolution_accepts_manifest_backed_artifact_declaring_mechanic(self) -> None:
        mechanic = load_mechanic(self.fixture("valid-mcp-tool.toml"), registry=registry_from_manifest())

        self.assertEqual(mechanic["outcome"]["artifact_type"], "completion-evidence")
        self.assertNotIn("forge_tag", mechanic)

    def test_registry_resolution_accepts_manifest_backed_schema_ref_declaring_mechanic(self) -> None:
        mechanic = load_mechanic(self.fixture("valid-mcp-tool.toml"), registry=registry_from_manifest())

        self.assertEqual(mechanic["parameters"][0]["schema_ref"], "completion-evidence")
        self.assertEqual(mechanic["outcome"]["artifact_type"], "completion-evidence")

    def test_validate_mechanic_accepts_already_loaded_toml_data(self) -> None:
        mechanic = load_mechanic(self.fixture("valid-git.toml"))

        validate_mechanic(mechanic)

    def test_invalid_toml_reports_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.toml"
            path.write_text("name = [\n", encoding="utf-8")

            with self.assertRaises(MechanicError) as context:
                load_mechanic(path)

        self.assertEqual(["<toml>"], context.exception.paths)
        self.assertIn("bad.toml is invalid TOML", str(context.exception))


if __name__ == "__main__":
    unittest.main()
