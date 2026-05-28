import tempfile
import unittest
from pathlib import Path

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

    def test_schema_accepts_github_tagged_forge_mechanic(self) -> None:
        mechanic = load_mechanic(self.fixture("valid-github.toml"))

        self.assertEqual(mechanic["forge_tag"], "github")

    def test_schema_accepts_generic_runtime_mcp_tool_mechanic(self) -> None:
        mechanic = load_mechanic(self.fixture("valid-mcp-tool.toml"))

        self.assertNotIn("forge_tag", mechanic)

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

    def test_schema_rejects_malformed_forge_tag_with_field_path(self) -> None:
        with self.assertRaises(MechanicError) as context:
            load_mechanic(self.fixture("invalid-forge-tag.toml"))

        self.assertIn("forge_tag", context.exception.paths)

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

    def test_registry_resolution_accepts_known_forge_tag_when_registry_is_loaded(self) -> None:
        registry = MechanicRegistry(
            artifact_types={"change-proposal"},
            forge_tags={"github"},
        )

        mechanic = load_mechanic(self.fixture("valid-github.toml"), registry=registry)

        self.assertEqual(mechanic["forge_tag"], "github")

    def test_registry_resolution_rejects_unknown_forge_tag_when_registry_is_loaded(self) -> None:
        registry = MechanicRegistry(forge_tags={"github"})

        with self.assertRaises(MechanicError) as context:
            load_mechanic(self.fixture("invalid-forge-tag-unregistered.toml"), registry=registry)

        self.assertIn("forge_tag", context.exception.paths)
        self.assertIn("forge tag `sourcehut-lists` does not resolve in registry", str(context.exception))

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
