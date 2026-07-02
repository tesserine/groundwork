"""The protocol-prose conformance gate: prose agrees with the owning schema.

Four teeth, each protecting a distinct clause of the gate's contract:

- the live tree passes, for every manifest protocol — the standing CI gate;
- every producing protocol yielded at least one parsed delivery block, so a
  silent parse miss can never green;
- a document attributing fields the schema rejects fails, on both prose
  surfaces (delivery-block key, backticked ``###`` field heading), against
  the live schemas — the standing red;
- removing a property from the schema flips the check on the live survey
  document without the checker being edited — the gate consults the
  authority, it does not snapshot vocabulary.
"""

import json
import shutil
import tempfile
import tomllib
import unittest
from pathlib import Path

from tooling.protocol_prose import check_tree, schema_property_names


ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / "schemas"
RED_TREE = ROOT / "tests" / "fixtures" / "protocol_prose" / "red_tree"


def manifest_protocols() -> list[dict]:
    manifest = tomllib.loads((ROOT / "manifest.toml").read_text(encoding="utf-8"))
    return manifest["protocols"]


class LiveTreeConformanceTests(unittest.TestCase):
    def test_live_tree_conforms_for_every_manifest_protocol(self) -> None:
        report = check_tree(ROOT)

        self.assertEqual(
            [entry["name"] for entry in manifest_protocols()],
            report.protocols,
            "the gate reads the protocol set from the manifest",
        )
        self.assertEqual(
            [],
            [violation.render() for violation in report.violations],
        )
        self.assertTrue(report.passed)

    def test_every_producing_protocol_yields_a_parsed_delivery_block(self) -> None:
        report = check_tree(ROOT)

        for entry in manifest_protocols():
            if not entry.get("produces"):
                continue
            with self.subTest(protocol=entry["name"]):
                self.assertGreaterEqual(
                    report.delivery_blocks.get(entry["name"], 0),
                    1,
                    "a producer whose delivery block the parser cannot "
                    "find would pass vacuously — absence must not green",
                )


class StandingRedTests(unittest.TestCase):
    def test_phantom_attributions_fail_against_the_live_schemas(self) -> None:
        report = check_tree(RED_TREE, schemas_dir=SCHEMAS)

        found = {
            (violation.protocol, violation.surface, violation.token)
            for violation in report.violations
        }
        self.assertEqual(
            {
                ("survey", "field-heading", "surveyed-territory"),
                ("survey", "delivery-block", "chosen_exigence"),
                ("silent", "field-heading", "orphan-field"),
            },
            found,
        )
        for violation in report.violations:
            with self.subTest(token=violation.token):
                self.assertIn(
                    "grants no such property",
                    violation.render(),
                )
        granted_heading_flagged = any(
            violation.token == "scope" for violation in report.violations
        )
        self.assertFalse(
            granted_heading_flagged,
            "a heading the schema grants is not a violation",
        )

    def test_violation_names_the_consulted_schema_file(self) -> None:
        report = check_tree(RED_TREE, schemas_dir=SCHEMAS)

        survey_violations = [
            violation
            for violation in report.violations
            if violation.protocol == "survey"
        ]
        self.assertTrue(survey_violations)
        for violation in survey_violations:
            with self.subTest(surface=violation.surface):
                self.assertEqual(
                    SCHEMAS / "requirements.schema.json",
                    violation.schema_path,
                )


class ConsultsTheAuthorityTests(unittest.TestCase):
    def test_schema_property_removal_flips_the_check_unedited(self) -> None:
        schema = json.loads(
            (SCHEMAS / "requirements.schema.json").read_text(encoding="utf-8")
        )
        live_doc = (ROOT / "protocols" / "survey" / "PROTOCOL.md").read_text(
            encoding="utf-8"
        )
        removable = [
            name
            for name in schema_property_names(schema)
            if f"`{name}`" in live_doc and name not in schema.get("required", [])
        ]
        self.assertTrue(
            removable,
            "the live survey document names schema-granted fields; if this "
            "fails, the prose no longer derives from the schema",
        )
        removed = sorted(removable)[0]
        del schema["properties"][removed]

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            (tree / "protocols" / "survey").mkdir(parents=True)
            (tree / "schemas").mkdir()
            (tree / "manifest.toml").write_text(
                'name = "rename-flip"\n\n'
                "[[artifact_types]]\n"
                'name = "requirements"\n\n'
                "[[protocols]]\n"
                'name = "survey"\n'
                'produces = ["requirements"]\n',
                encoding="utf-8",
            )
            (tree / "protocols" / "survey" / "PROTOCOL.md").write_text(
                live_doc, encoding="utf-8"
            )
            (tree / "schemas" / "requirements.schema.json").write_text(
                json.dumps(schema), encoding="utf-8"
            )

            report = check_tree(tree)

        flagged = {violation.token for violation in report.violations}
        self.assertIn(
            removed,
            flagged,
            "the schema moved and the unedited checker flipped — the gate "
            "consults the schema, it does not snapshot vocabulary",
        )

    def test_baseline_live_survey_passes_with_the_full_schema(self) -> None:
        live_doc = (ROOT / "protocols" / "survey" / "PROTOCOL.md").read_text(
            encoding="utf-8"
        )
        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            (tree / "protocols" / "survey").mkdir(parents=True)
            (tree / "manifest.toml").write_text(
                'name = "rename-flip-baseline"\n\n'
                "[[artifact_types]]\n"
                'name = "requirements"\n\n'
                "[[protocols]]\n"
                'name = "survey"\n'
                'produces = ["requirements"]\n',
                encoding="utf-8",
            )
            (tree / "protocols" / "survey" / "PROTOCOL.md").write_text(
                live_doc, encoding="utf-8"
            )
            shutil.copytree(SCHEMAS, tree / "schemas")

            report = check_tree(tree)

        self.assertEqual(
            [],
            [violation.render() for violation in report.violations],
            "the flip test's contrast baseline: the same document against "
            "the unmodified schema is clean",
        )


if __name__ == "__main__":
    unittest.main()
