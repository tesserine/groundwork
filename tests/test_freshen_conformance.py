import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

from tooling.conformance import run_conformance
from tooling.prose_conformance import (
    FRESHEN_ADR_0015_URL,
    freshen_dispositions,
    freshen_graph_facets,
    freshen_record_elements,
    freshen_record_schema,
    freshen_surface_coherence,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "freshen-record"
SCHEMA = ROOT / "schemas" / "freshen-record.schema.json"
ACQUIRE = ROOT / "skills" / "acquire" / "SKILL.md"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def validator(schema: dict | None = None) -> Draft202012Validator:
    return Draft202012Validator(schema if schema is not None else freshen_record_schema(ROOT))


def schema_errors(record: dict, schema: dict | None = None) -> list[str]:
    return [error.message for error in validator(schema).iter_errors(record)]


def valid_record(disposition: str = "proceed-as-freshened") -> dict:
    record = load_json(FIXTURES / "valid-proceed-as-freshened.json")
    record["disposition"] = disposition
    return record


class FreshenRecordSchemaTests(unittest.TestCase):
    def test_conformance_discovers_freshen_record_schema(self) -> None:
        results = run_conformance([SCHEMA])

        self.assertEqual([SCHEMA.resolve()], [result.path for result in results])
        self.assertTrue(all(result.passed for result in results), results)

    def test_valid_fixture_exists_for_each_disposition(self) -> None:
        schema = freshen_record_schema(ROOT)
        for disposition in freshen_dispositions(schema):
            with self.subTest(disposition=disposition):
                fixture = FIXTURES / f"valid-{disposition}.json"
                self.assertTrue(fixture.is_file())
                self.assertEqual([], schema_errors(load_json(fixture), schema))

    def test_invalid_disposition_shapes_fail(self) -> None:
        for name in [
            "invalid-missing-disposition.json",
            "invalid-out-of-set-disposition.json",
            "invalid-compound-disposition.json",
        ]:
            with self.subTest(fixture=name):
                self.assertNotEqual([], schema_errors(load_json(FIXTURES / name)))

    def test_required_record_elements_fail_when_missing(self) -> None:
        schema = freshen_record_schema(ROOT)
        for element in freshen_record_elements(schema):
            with self.subTest(element=element):
                record = valid_record()
                del record[element]
                self.assertNotEqual([], schema_errors(record, schema))

    def test_graph_finding_requires_each_schema_facet(self) -> None:
        schema = freshen_record_schema(ROOT)
        for facet in freshen_graph_facets(schema):
            with self.subTest(facet=facet):
                record = valid_record()
                del record["graph_finding"][facet]
                self.assertNotEqual([], schema_errors(record, schema))

    def test_nonfinding_strings_fail(self) -> None:
        self.assertNotEqual([], schema_errors(load_json(FIXTURES / "invalid-empty-finding.json")))

    def test_schema_required_mutation_turns_surface_projection_red(self) -> None:
        schema = freshen_record_schema(ROOT)

        record_schema = copy.deepcopy(schema)
        record_schema["required"].remove("staleness_finding")
        self.assertFalse(freshen_surface_coherence(ROOT, schema=record_schema).record_contract_matches_schema_required)

        graph_schema = copy.deepcopy(schema)
        graph_schema["properties"]["graph_finding"]["required"].remove("labels")
        self.assertFalse(freshen_surface_coherence(ROOT, schema=graph_schema).graph_facets_match_schema_required)


class FreshenAcquireSurfaceTests(unittest.TestCase):
    def test_acquire_surface_is_gate_bound_to_freshen_schema_and_manifest(self) -> None:
        coherence = freshen_surface_coherence(ROOT)

        self.assertTrue(coherence.passed, coherence)

    def test_withhold_conditioning_deletion_turns_gate_red(self) -> None:
        surface = ACQUIRE.read_text(encoding="utf-8")
        mutated, count = re.subn(
            r"Deliver the work-unit artifact only under a recorded `proceed-as-freshened` disposition[.]",
            "Deliver the work-unit artifact after the freshen pass.",
            surface,
            count=1,
        )

        self.assertEqual(1, count)
        self.assertFalse(freshen_surface_coherence(ROOT, acquire_text=mutated).delivery_conditioned_on_proceed)

    def test_routing_table_row_deletion_turns_projection_red(self) -> None:
        surface = ACQUIRE.read_text(encoding="utf-8")
        mutated, count = re.subn(
            r"\| reblock \|.*\n",
            "",
            surface,
            count=1,
        )

        self.assertEqual(1, count)
        coherence = freshen_surface_coherence(ROOT, acquire_text=mutated)
        self.assertFalse(coherence.routing_table_matches_disposition_enum)
        self.assertFalse(coherence.routing_table_routes_every_disposition)

    def test_adr_0015_url_is_the_canonical_commons_register_path(self) -> None:
        self.assertEqual(
            "https://github.com/tesserine/commons/blob/main/adr/0015-mode-is-a-property-of-the-session.md",
            FRESHEN_ADR_0015_URL,
        )
        self.assertIn(FRESHEN_ADR_0015_URL, ACQUIRE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
