import json
import unittest
from pathlib import Path

from tooling.forge_address import assert_derived_schema_matches_authority


ROOT = Path(__file__).resolve().parents[1]
FORGE_ADDRESS_SCHEMA = ROOT / "schemas" / "forge-address.schema.json"
WORK_UNIT_SCHEMA = ROOT / "schemas" / "work-unit.schema.json"


class ForgeAddressSchemaVendoringTests(unittest.TestCase):
    def test_forge_address_schema_declares_immutable_runa_provenance(self) -> None:
        schema = json.loads(FORGE_ADDRESS_SCHEMA.read_text(encoding="utf-8"))
        canonical = schema["x-tesserine-canonical"]

        self.assertNotIn("$id", schema)
        self.assertEqual("tesserine/runa", canonical["source"])
        self.assertRegex(canonical["commit"], r"^[0-9a-f]{40}$")
        self.assertIn(canonical["commit"], canonical["schema_url"])
        self.assertNotIn("/main/", canonical["schema_url"])

    def test_derived_schema_matches_pinned_runa_authority(self) -> None:
        assert_derived_schema_matches_authority()

    def test_work_unit_handle_refs_authoritative_schema_without_local_defs(self) -> None:
        schema = json.loads(WORK_UNIT_SCHEMA.read_text(encoding="utf-8"))

        self.assertEqual(
            "forge-address.schema.json#/$defs/work_unit_handle",
            schema["properties"]["handle"]["$ref"],
        )
        self.assertNotIn("$defs", schema)
        serialized = json.dumps(schema)
        self.assertNotIn("github-handle", serialized)
        self.assertNotIn("sourcehut-handle", serialized)


if __name__ == "__main__":
    unittest.main()
