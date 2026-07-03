import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def prose_conformance():
    try:
        from tooling import prose_conformance as module
    except ImportError as error:  # pragma: no cover - RED before helper exists.
        raise AssertionError("tooling.prose_conformance helper is missing") from error
    return module


class ProseConformanceHelperTests(unittest.TestCase):
    def test_delivery_boundary_reads_manifest_and_schema_authorities(self) -> None:
        helper = prose_conformance()

        boundaries = helper.delivery_boundaries(ROOT)
        by_protocol = {boundary.protocol: boundary for boundary in boundaries}
        manifest_producers = [
            protocol["name"]
            for protocol in helper.manifest_protocols(ROOT)
            if protocol.get("produces")
        ]

        self.assertEqual(manifest_producers, [boundary.protocol for boundary in boundaries])
        self.assertEqual([], [boundary for boundary in boundaries if not boundary.passed])
        self.assertTrue(by_protocol["take"].scoped)
        self.assertTrue(by_protocol["take"].schema_requires_work_unit)
        self.assertFalse(by_protocol["decompose"].scoped)
        self.assertFalse(by_protocol["decompose"].schema_requires_work_unit)

    def test_manifest_scoped_flip_changes_delivery_boundary_result(self) -> None:
        helper = prose_conformance()

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            shutil.copytree(ROOT / "protocols", tree / "protocols")
            shutil.copytree(ROOT / "schemas", tree / "schemas")
            manifest = (ROOT / "manifest.toml").read_text(encoding="utf-8")
            manifest = manifest.replace(
                'name = "take"\nscoped = true\nrequires = ["work-unit"]',
                'name = "take"\nrequires = ["work-unit"]',
                1,
            )
            (tree / "manifest.toml").write_text(manifest, encoding="utf-8")

            take = [
                boundary
                for boundary in helper.delivery_boundaries(tree)
                if boundary.protocol == "take"
            ][0]

        self.assertFalse(take.passed)
        self.assertFalse(take.scoped)
        self.assertTrue(take.schema_requires_work_unit)

    def test_delivery_boundary_explanation_removal_flips_semantic_result(self) -> None:
        helper = prose_conformance()

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            shutil.copytree(ROOT / "protocols", tree / "protocols")
            shutil.copytree(ROOT / "schemas", tree / "schemas")
            (tree / "manifest.toml").write_text(
                (ROOT / "manifest.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            take = tree / "protocols" / "take" / "PROTOCOL.md"
            body, substitutions = re.subn(
                r"The object below\s+is MCP tool input, not artifact body[.]\s+"
                r"`instance_id` is a tool parameter\s+that names the artifact instance;.*?"
                r"must not appear in\s+the artifact body[.]\s*",
                "",
                take.read_text(encoding="utf-8"),
                count=1,
                flags=re.DOTALL,
            )
            self.assertEqual(1, substitutions)
            take.write_text(body, encoding="utf-8")

            boundary = [
                boundary
                for boundary in helper.delivery_boundaries(tree)
                if boundary.protocol == "take"
            ][0]

        self.assertTrue(boundary.passed)
        self.assertFalse(boundary.explains_mcp_tool_input_boundary)

    def test_scoped_work_unit_injection_clause_removal_flips_semantic_result(self) -> None:
        helper = prose_conformance()

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            shutil.copytree(ROOT / "protocols", tree / "protocols")
            shutil.copytree(ROOT / "schemas", tree / "schemas")
            (tree / "manifest.toml").write_text(
                (ROOT / "manifest.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            take = tree / "protocols" / "take" / "PROTOCOL.md"
            body, substitutions = re.subn(
                r"Runa injects `work_unit` from session context; the\s+"
                r"agent does not supply `work_unit`[.]",
                "The schema carries work-unit identity.",
                take.read_text(encoding="utf-8"),
                count=1,
            )
            self.assertEqual(1, substitutions)
            take.write_text(body, encoding="utf-8")

            boundary = [
                boundary
                for boundary in helper.delivery_boundaries(tree)
                if boundary.protocol == "take"
            ][0]

        self.assertTrue(boundary.passed)
        self.assertFalse(boundary.explains_work_unit_injection_contract)

    def test_unscoped_work_unit_non_injection_clause_removal_flips_semantic_result(self) -> None:
        helper = prose_conformance()

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            shutil.copytree(ROOT / "protocols", tree / "protocols")
            shutil.copytree(ROOT / "schemas", tree / "schemas")
            (tree / "manifest.toml").write_text(
                (ROOT / "manifest.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            survey = tree / "protocols" / "survey" / "PROTOCOL.md"
            body, substitutions = re.subn(
                r"This planning-phase artifact is unscoped; runa\s+"
                r"does not inject `work_unit`[.]",
                "This planning-phase artifact is unscoped.",
                survey.read_text(encoding="utf-8"),
                count=1,
            )
            self.assertEqual(1, substitutions)
            survey.write_text(body, encoding="utf-8")

            boundary = [
                boundary
                for boundary in helper.delivery_boundaries(tree)
                if boundary.protocol == "survey"
            ][0]

        self.assertTrue(boundary.passed)
        self.assertFalse(boundary.explains_work_unit_injection_contract)

    def test_validation_scope_clause_removal_flips_semantic_result(self) -> None:
        helper = prose_conformance()

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            shutil.copytree(ROOT / "protocols", tree / "protocols")
            shutil.copytree(ROOT / "schemas", tree / "schemas")
            (tree / "manifest.toml").write_text(
                (ROOT / "manifest.toml").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            take = tree / "protocols" / "take" / "PROTOCOL.md"
            body, substitutions = re.subn(
                r"Runa validates the remaining artifact body fields against the contract\s+"
                r"schema, persists the artifact, and records it in the artifact store[.]",
                "Runa validates the contract schema and records the artifact.",
                take.read_text(encoding="utf-8"),
                count=1,
            )
            self.assertEqual(1, substitutions)
            take.write_text(body, encoding="utf-8")

            boundary = [
                boundary
                for boundary in helper.delivery_boundaries(tree)
                if boundary.protocol == "take"
            ][0]

        self.assertTrue(boundary.passed)
        self.assertFalse(boundary.explains_post_extraction_validation_scope)

    def test_protocol_runtime_wiring_insertion_flips_absence_result(self) -> None:
        helper = prose_conformance()

        self.assertEqual([], helper.protocol_runtime_wiring_violations("Deliver the artifact."))
        violations = helper.protocol_runtime_wiring_violations(
            "After delivery, runa go will spawn the next tick with RUNA_WORKSPACE set."
        )

        self.assertIn("runa go command", violations)
        self.assertIn("RUNA environment atom", violations)

    def test_public_docs_bypass_insertion_flips_absence_result(self) -> None:
        helper = prose_conformance()

        with tempfile.TemporaryDirectory() as tmp:
            tree = Path(tmp) / "tree"
            (tree / "docs" / "architecture").mkdir(parents=True)
            (tree / "scripts").mkdir(parents=True)
            (tree / "README.md").write_text(
                (ROOT / "README.md").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
            (tree / "docs" / "architecture" / "connecting-structure.md").write_text(
                (ROOT / "docs" / "architecture" / "connecting-structure.md").read_text(
                    encoding="utf-8"
                )
                + "\nPresent that artifact body to the human.\n",
                encoding="utf-8",
            )
            (tree / "scripts" / "interactive-session-surface-handoff.md").write_text(
                (ROOT / "scripts" / "interactive-session-surface-handoff.md").read_text(
                    encoding="utf-8"
                ),
                encoding="utf-8",
            )

            violations = helper.public_docs_interactive_adapter_bypass_violations(tree)

        self.assertEqual(
            {"docs/architecture/connecting-structure.md": ["human artifact handoff bypass"]},
            violations,
        )

    def test_frontmatter_metadata_changes_are_read_from_the_skill(self) -> None:
        helper = prose_conformance()

        data = helper.frontmatter((ROOT / "skills" / "contract" / "SKILL.md").read_text())
        self.assertIn("metadata", data)
        metadata = data["metadata"]
        self.assertIsInstance(metadata, dict)
        self.assertRegex(metadata["version"], r"^[0-9]+[.][0-9]+[.][0-9]+$")
        self.assertRegex(metadata["updated"], r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")

    def test_json_schema_ref_resolution_reads_current_schema(self) -> None:
        helper = prose_conformance()
        schema = json.loads(
            (ROOT / "schemas" / "forge-capability" / "v1" / "forge-capability.schema.json").read_text(
                encoding="utf-8"
            )
        )

        handle = helper.schema_def(schema, "#/$defs/handle")

        self.assertEqual(["id", "display"], handle["required"])


if __name__ == "__main__":
    unittest.main()
