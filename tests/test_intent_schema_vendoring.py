import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTENT_SCHEMA_PATH = ROOT / "schemas" / "intent.schema.json"
SCHEMAS_README_PATH = ROOT / "schemas" / "README.md"
FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"
COMMONS_IMMUTABLE_REF = (
    r"(?:[0-9a-f]{40}|v[0-9]+\.[0-9]+\.[0-9]+"
    r"(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?)"
)
COMMONS_CANONICAL_URL = re.compile(
    rf"^https://raw\.githubusercontent\.com/tesserine/commons/"
    rf"(?P<ref>{COMMONS_IMMUTABLE_REF})/(?P<path>.+)$"
)


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
    def assert_commons_canonical_url(self, url: str, expected_path: str) -> str:
        match = COMMONS_CANONICAL_URL.fullmatch(url)
        self.assertIsNotNone(match, f"{url!r} is not an immutable commons raw URL")
        assert match is not None
        self.assertEqual(match.group("path"), expected_path)
        self.assertNotEqual(match.group("ref"), "main")
        return match.group("ref")

    def test_intent_schema_declares_canonical_provenance(self) -> None:
        schema = json.loads(INTENT_SCHEMA_PATH.read_text())
        canonical = schema["x-tesserine-canonical"]

        self.assertNotIn("$id", schema)
        self.assertEqual(canonical["version"], "2.0.0")
        schema_ref = self.assert_commons_canonical_url(
            canonical["schema_url"],
            "schemas/intent/v2/intent.schema.json",
        )
        prose_ref = self.assert_commons_canonical_url(
            canonical["prose_url"],
            "INTENT.md",
        )
        self.assertEqual(schema_ref, prose_ref)

    def test_intent_schema_body_matches_v2_contract(self) -> None:
        schema = json.loads(INTENT_SCHEMA_PATH.read_text())

        self.assertEqual(schema["required"], ["statement", "source"])
        self.assertIs(schema["additionalProperties"], False)
        self.assertEqual(set(schema["properties"]), {"statement", "source", "target"})

        for field in ["statement", "source", "target"]:
            with self.subTest(field=field):
                self.assertEqual(schema["properties"][field]["type"], "string")
                self.assertEqual(schema["properties"][field]["minLength"], 1)

        self.assertNotIn("description", schema["properties"])
        self.assertNotIn("references", schema["properties"])
        self.assertNotIn("kind", json.dumps(schema))

    def test_schemas_readme_documents_intent_vendoring_discipline(self) -> None:
        readme = SCHEMAS_README_PATH.read_text()
        schema = json.loads(INTENT_SCHEMA_PATH.read_text())
        canonical = schema["x-tesserine-canonical"]
        schema_match = COMMONS_CANONICAL_URL.fullmatch(canonical["schema_url"])
        prose_match = COMMONS_CANONICAL_URL.fullmatch(canonical["prose_url"])
        assert schema_match is not None
        assert prose_match is not None

        self.assertIn("intent.schema.json", readme)
        self.assertIn(canonical["version"], readme)
        self.assertIn(schema_match.group("path"), readme)
        self.assertIn("tesserine/commons", canonical["schema_url"])
        self.assertRegex(readme, r"runtime consumers still read schemas from\s+groundwork")
        self.assertEqual(schema_match.group("ref"), prose_match.group("ref"))
        self.assertNotEqual("main", schema_match.group("ref"))

    def test_valid_intent_fixtures_match_vendored_schema_contract(self) -> None:
        schema = json.loads(INTENT_SCHEMA_PATH.read_text())

        for fixture_name in [
            "valid-intent.json",
            "valid-intent-with-target.json",
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
            "invalid-intent-empty-target.json": "target must be at least 1 characters",
        }

        for fixture_name, error in cases.items():
            with self.subTest(fixture_name=fixture_name):
                fixture = json.loads((FIXTURES / fixture_name).read_text())
                with self.assertRaisesRegex(ValueError, error):
                    validate_instance(schema, fixture)


if __name__ == "__main__":
    unittest.main()
