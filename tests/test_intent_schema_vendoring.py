import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTENT_SCHEMA_PATH = ROOT / "schemas" / "intent.schema.json"
SCHEMAS_README_PATH = ROOT / "schemas" / "README.md"
FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"


def validate_instance(schema: dict, instance: object, path: str = "instance") -> None:
    schema_type = schema["type"]

    if schema_type == "object":
        if not isinstance(instance, dict):
            raise ValueError(f"{path} must be an object")

        properties = schema.get("properties", {})

        for field in schema.get("required", []):
            if field not in instance:
                raise ValueError(f"missing required field: {field}")

        if schema.get("additionalProperties") is False:
            unknown_fields = set(instance) - set(properties)
            if unknown_fields:
                raise ValueError(f"unexpected fields: {sorted(unknown_fields)!r}")

        for field, value in instance.items():
            validate_instance(properties[field], value, field if path == "instance" else f"{path}.{field}")
        return

    if schema_type == "array":
        if not isinstance(instance, list):
            raise ValueError(f"{path} must be an array")
        min_items = schema.get("minItems")
        if min_items is not None and len(instance) < min_items:
            raise ValueError(f"{path} must contain at least {min_items} item")
        for index, item in enumerate(instance):
            validate_instance(schema["items"], item, f"{path}[{index}]")
        return

    if schema_type == "string":
        if not isinstance(instance, str):
            raise ValueError(f"{path} must be a string")
        if "enum" in schema and instance not in schema["enum"]:
            raise ValueError(f"{path} must be one of {schema['enum']!r}")
        min_length = schema.get("minLength")
        if min_length is not None and len(instance) < min_length:
            raise ValueError(f"{path} must be at least {min_length} characters")
        return

    raise AssertionError(f"unsupported schema type: {schema_type}")


class IntentSchemaVendoringTests(unittest.TestCase):
    def test_intent_schema_declares_canonical_provenance(self) -> None:
        schema = json.loads(INTENT_SCHEMA_PATH.read_text())

        self.assertNotIn("$id", schema)
        self.assertEqual(
            schema["x-tesserine-canonical"],
            {
                "version": "1.0.0",
                "schema_url": (
                    "https://raw.githubusercontent.com/tesserine/commons/"
                    "main/schemas/intent/v1/intent.schema.json"
                ),
                "prose_url": (
                    "https://raw.githubusercontent.com/tesserine/commons/main/INTENT.md"
                ),
            },
        )

    def test_schemas_readme_documents_intent_vendoring_discipline(self) -> None:
        readme = SCHEMAS_README_PATH.read_text()

        self.assertIn("methodology-private", readme)
        self.assertIn("intent.schema.json", readme)
        self.assertIn("tesserine/commons", readme)
        self.assertIn("runtime consumers still read schemas from groundwork", readme)
        self.assertIn("pins commons `main`", readme)
        self.assertIn("immutable", readme)
        self.assertIn("release-tag or commit-SHA URLs", readme)
        self.assertIn("full semver", readme)

    def test_valid_intent_fixtures_match_vendored_schema_contract(self) -> None:
        schema = json.loads(INTENT_SCHEMA_PATH.read_text())

        for fixture_name in [
            "valid-intent.json",
            "valid-intent-with-references.json",
        ]:
            with self.subTest(fixture_name=fixture_name):
                fixture = json.loads((FIXTURES / fixture_name).read_text())
                validate_instance(schema, fixture)

    def test_invalid_intent_fixtures_fail_vendored_schema_contract(self) -> None:
        schema = json.loads(INTENT_SCHEMA_PATH.read_text())

        cases = {
            "invalid-intent-missing-source.json": "missing required field: source",
            "invalid-intent-context.json": "unexpected fields: \\['context'\\]",
            "invalid-intent-unknown-field.json": "unexpected fields: \\['priority'\\]",
            "invalid-intent-empty-references.json": "references must contain at least 1 item",
            "invalid-intent-empty-ref.json": "references\\[0\\]\\.ref must be at least 1 characters",
            "invalid-intent-invalid-kind.json": "references\\[0\\]\\.kind must be one of",
        }

        for fixture_name, error in cases.items():
            with self.subTest(fixture_name=fixture_name):
                fixture = json.loads((FIXTURES / fixture_name).read_text())
                with self.assertRaisesRegex(ValueError, error):
                    validate_instance(schema, fixture)


if __name__ == "__main__":
    unittest.main()
