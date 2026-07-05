"""Conformance gates for the freshen-on-acquire built-in (groundwork#465).

Two layers of teeth, both discovered by `unittest` (CI's `conformance.yml`
runs `python -m unittest discover -s tests`):

* the freshen-record schema is validated against real fixtures — valid records
  pass, and each hollow record (a missing element, a missing facet, an
  out-of-set or compound disposition) fails; and
* the acquire surface is checked against the authorities that own its
  invariants (the schema's disposition set / facets / required elements, and
  the manifest-derived admitted destination), never against a phrase list.

The mutation probes copy the tree, hollow one thing, and assert the gate turns
red — the anti-theater evidence that the checks bite on every run, including a
schema mutation that proves the surface gate consults the schema rather than a
hard-coded list.
"""

import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "freshen-record.schema.json"
FIXTURES = ROOT / "tests" / "fixtures" / "freshen-record"

EXPECTED_DISPOSITION_SET = {
    "proceed-as-freshened",
    "close",
    "split",
    "relink",
    "reblock",
    "reframe-as-spike",
}
EXPECTED_GRAPH_FACETS = {
    "blockers",
    "blocked",
    "epic_membership",
    "siblings",
    "milestone",
    "labels",
}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def prose_conformance():
    try:
        from tooling import prose_conformance as module
    except ImportError as error:  # pragma: no cover - RED before helper exists.
        raise AssertionError("tooling.prose_conformance helper is missing") from error
    return module


def _copy_tree(tmp: str) -> Path:
    """A tree carrying every substrate the freshen gate reads: the acquire
    skill, the schemas, and the manifest."""
    tree = Path(tmp) / "tree"
    shutil.copytree(ROOT / "skills", tree / "skills")
    shutil.copytree(ROOT / "schemas", tree / "schemas")
    (tree / "manifest.toml").write_text(
        (ROOT / "manifest.toml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return tree


class FreshenRecordSchemaTests(unittest.TestCase):
    def test_schema_is_a_valid_draft_2020_12_schema(self) -> None:
        Draft202012Validator.check_schema(load_schema())

    def test_disposition_enum_is_the_declared_set(self) -> None:
        enum = load_schema()["properties"]["disposition"]["enum"]
        self.assertEqual(len(enum), len(set(enum)), "disposition enum has duplicates")
        self.assertEqual(set(enum), EXPECTED_DISPOSITION_SET)

    def test_graph_finding_requires_all_six_facets(self) -> None:
        graph = load_schema()["properties"]["graph_finding"]
        self.assertEqual(set(graph["required"]), EXPECTED_GRAPH_FACETS)
        self.assertFalse(
            graph.get("additionalProperties", True),
            "graph_finding must be a closed object",
        )

    def test_record_requires_its_four_elements(self) -> None:
        required = set(load_schema()["required"])
        self.assertEqual(
            required,
            {"work_unit", "grounded_against", "staleness_finding", "graph_finding", "disposition"},
        )

    def test_valid_records_pass(self) -> None:
        validator = Draft202012Validator(load_schema())
        for name in ("valid-proceed.json", "valid-close.json", "valid-reframe-as-spike.json"):
            with self.subTest(fixture=name):
                validator.validate(load_fixture(name))

    def test_hollow_records_fail(self) -> None:
        validator = Draft202012Validator(load_schema())
        for name in (
            "invalid-missing-graph-finding.json",
            "invalid-missing-grounded-against.json",
            "invalid-missing-facet.json",
            "invalid-out-of-set-disposition.json",
            "invalid-compound-disposition.json",
            "invalid-empty-staleness.json",
        ):
            with self.subTest(fixture=name):
                self.assertFalse(
                    validator.is_valid(load_fixture(name)),
                    f"hollow record {name} unexpectedly validated",
                )


class FreshenOnAcquireCoherenceTests(unittest.TestCase):
    def test_admitted_destination_is_manifest_derived(self) -> None:
        helper = prose_conformance()
        self.assertEqual(helper.acquisition_admitted_destination(ROOT), "define")

    def test_surface_coherence_passes(self) -> None:
        helper = prose_conformance()
        result = helper.freshen_on_acquire_coherence(ROOT)
        failing = [name for name, value in vars(result).items() if not value]
        self.assertTrue(result.passed, f"failing facets: {failing}")

    def test_probe_removed_disposition_row_turns_red(self) -> None:
        helper = prose_conformance()
        with tempfile.TemporaryDirectory() as tmp:
            tree = _copy_tree(tmp)
            acquire = tree / "skills" / "acquire" / "SKILL.md"
            body, count = re.subn(
                r"^\| `close` \|.*\|\n",
                "",
                acquire.read_text(encoding="utf-8"),
                flags=re.MULTILINE,
            )
            self.assertEqual(count, 1, "probe did not find the close disposition row")
            acquire.write_text(body, encoding="utf-8")
            result = helper.freshen_on_acquire_coherence(tree)
        self.assertFalse(result.disposition_set_matches_schema)
        self.assertFalse(result.passed)

    def test_probe_removed_withhold_clause_turns_red(self) -> None:
        helper = prose_conformance()
        with tempfile.TemporaryDirectory() as tmp:
            tree = _copy_tree(tmp)
            acquire = tree / "skills" / "acquire" / "SKILL.md"
            body, count = re.subn(
                r"Only a `proceed-as-freshened`\s+disposition may deliver the work-unit artifact;\s*",
                "",
                acquire.read_text(encoding="utf-8"),
            )
            self.assertEqual(count, 1, "probe did not find the withhold clause")
            acquire.write_text(body, encoding="utf-8")
            result = helper.freshen_on_acquire_coherence(tree)
        self.assertFalse(result.withhold_conditioning_present)
        self.assertFalse(result.passed)

    def test_probe_removed_graph_facet_token_turns_red(self) -> None:
        helper = prose_conformance()
        with tempfile.TemporaryDirectory() as tmp:
            tree = _copy_tree(tmp)
            acquire = tree / "skills" / "acquire" / "SKILL.md"
            body = acquire.read_text(encoding="utf-8").replace("`milestone`", "milestone")
            acquire.write_text(body, encoding="utf-8")
            result = helper.freshen_on_acquire_coherence(tree)
        self.assertFalse(result.graph_finding_covers_schema_facets)
        self.assertFalse(result.passed)

    def test_probe_removed_record_element_token_turns_red(self) -> None:
        helper = prose_conformance()
        with tempfile.TemporaryDirectory() as tmp:
            tree = _copy_tree(tmp)
            acquire = tree / "skills" / "acquire" / "SKILL.md"
            body = acquire.read_text(encoding="utf-8").replace(
                "`staleness_finding`", "staleness_finding"
            )
            acquire.write_text(body, encoding="utf-8")
            result = helper.freshen_on_acquire_coherence(tree)
        self.assertFalse(result.record_contract_covers_required_elements)
        self.assertFalse(result.passed)

    def test_probe_schema_enum_widened_turns_red(self) -> None:
        """The surface gate consults the schema enum, not a hard-coded list: a
        disposition added to the schema the surface does not render turns the
        gate red."""
        helper = prose_conformance()
        with tempfile.TemporaryDirectory() as tmp:
            tree = _copy_tree(tmp)
            schema_path = tree / "schemas" / "freshen-record.schema.json"
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
            schema["properties"]["disposition"]["enum"].append("proceed-with-caveats")
            schema_path.write_text(json.dumps(schema, indent=2), encoding="utf-8")
            result = helper.freshen_on_acquire_coherence(tree)
        self.assertFalse(result.disposition_set_matches_schema)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
