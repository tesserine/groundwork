import re
import tomllib
import unittest
from pathlib import Path

from tooling.prose_conformance import (
    artifact_schema,
    block_keys,
    delivery_boundaries,
    delivery_call_block,
    markdown_section,
    manifest_protocols as authoritative_manifest_protocols,
    protocol_runtime_wiring_violations,
    public_docs_interactive_adapter_bypass_violations,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.toml"
PROTOCOLS_DIR = ROOT / "protocols"


def manifest_protocols() -> list[dict]:
    return tomllib.loads(MANIFEST_PATH.read_text(encoding="utf-8"))["protocols"]


def normalized_protocol(name: str) -> str:
    text = (PROTOCOLS_DIR / name / "PROTOCOL.md").read_text(encoding="utf-8")
    return re.sub(r"\s+", " ", text)


def protocol_text(name: str) -> str:
    return (PROTOCOLS_DIR / name / "PROTOCOL.md").read_text(encoding="utf-8")


class ProtocolArtifactDeliveryDocsTests(unittest.TestCase):
    def test_public_docs_point_to_the_runtime_driven_session_surface(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        runtime_install = markdown_section(readme, "Install for Runtime-Driven Deployments")
        interactive_install = markdown_section(readme, "Interactive Installation")
        handoff = (ROOT / "scripts" / "interactive-session-surface-handoff.md").read_text(
            encoding="utf-8"
        )

        self.assertLess(readme.index("## Install for Runtime-Driven Deployments"), readme.index("## Interactive Installation"))
        self.assertIn("scripts/install install", runtime_install)
        self.assertIn("deprecated in favor of the runtime-driven path", interactive_install)
        self.assertIn("groundwork-install:interactive-session-surface-handoff begin", handoff)
        self.assertIn("next-protocol-context", handoff)
        self.assertIn("validated by runa", handoff)
        self.assertEqual({}, public_docs_interactive_adapter_bypass_violations(ROOT))

    def test_protocol_prose_carries_no_runtime_wiring_state(self) -> None:
        """ADR-0008 consequence 2: a protocol states the methodology's own
        seam and stops; which runtime commands are wired, configured, or
        pending belongs to the runtime's own repository and tracker."""

        for protocol in authoritative_manifest_protocols(ROOT):
            body = protocol_text(protocol["name"])
            with self.subTest(protocol=protocol["name"]):
                self.assertEqual([], protocol_runtime_wiring_violations(body))
                if protocol.get("produces"):
                    self.assertIn(
                        protocol["produces"][0],
                        delivery_call_block(body, protocol["produces"][0]),
                    )

    def test_all_artifact_producing_protocols_explain_mcp_tool_input_boundary(self) -> None:
        producers = [protocol for protocol in authoritative_manifest_protocols(ROOT) if protocol["produces"]]

        self.assertEqual(
            [
                "survey",
                "decompose",
                "define",
                "plan",
                "implement",
                "verify",
                "submit",
                "land",
            ],
            [protocol["name"] for protocol in producers],
        )

        boundaries = {boundary.protocol: boundary for boundary in delivery_boundaries(ROOT)}
        for protocol in producers:
            with self.subTest(protocol=protocol["name"]):
                self.assertTrue(boundaries[protocol["name"]].passed)
                self.assertTrue(boundaries[protocol["name"]].explanation_names_instance_id)
                self.assertTrue(boundaries[protocol["name"]].explanation_names_tool_input)
                self.assertTrue(
                    boundaries[protocol["name"]].explanation_distinguishes_artifact_body
                )
                self.assertTrue(boundaries[protocol["name"]].explains_mcp_tool_input_boundary)

    def test_scoped_protocol_delivery_docs_preserve_work_unit_injection_contract(self) -> None:
        for boundary in delivery_boundaries(ROOT):
            with self.subTest(protocol=boundary.protocol):
                self.assertTrue(boundary.passed)
                self.assertTrue(boundary.explains_work_unit_injection_contract)

    def test_artifact_validation_sentences_name_post_extraction_body_scope(self) -> None:
        for protocol in authoritative_manifest_protocols(ROOT):
            if not protocol["produces"]:
                continue
            artifact = protocol["produces"][0]
            body = protocol_text(protocol["name"])
            block = delivery_call_block(body, artifact)
            keys = block_keys(block)
            schema = artifact_schema(ROOT, artifact)

            with self.subTest(protocol=protocol["name"]):
                self.assertIn("instance_id", keys)
                self.assertNotIn("instance_id", schema.get("properties", {}))
                self.assertNotIn("work_unit", keys)
                self.assertEqual(
                    protocol.get("scoped") is True,
                    "work_unit" in schema.get("required", []),
                )
                boundary = {
                    boundary.protocol: boundary for boundary in delivery_boundaries(ROOT)
                }[protocol["name"]]
                self.assertTrue(boundary.explains_post_extraction_validation_scope)

    def test_decompose_delivery_docs_preserve_ticket_backed_work_unit_identity_rules(self) -> None:
        schema = artifact_schema(ROOT, "work-unit")
        handle = schema["properties"]["handle"]
        body = normalized_protocol("decompose")

        self.assertEqual({"$ref": "#/$defs/handle"}, handle)
        for expected in [
            "Every work-unit is tracker-backed",
            "first invoke the connector capability `create-ticket` operation",
            "`create-ticket` is a first-delivery-only step",
            "refinement never calls it",
            "decompose does not adopt a pre-existing tracker ticket into a new artifact",
            "must not create a second ticket",
            "uses a stable id derived from the connector handle's `id`",
            "populate `handle` exactly once from the identity returned by `create-ticket`",
            "carry the existing `handle` through unchanged",
            "Do not call `create-ticket`, re-derive `handle`, or omit `handle` during refinement",
            "no top-level `work_unit` field",
            "no forge identity outside the connector handle",
            "Dependency references must use canonical delivered work-unit `instance_id` values",
            "not tracker shorthand such as `#123`, `123`, `work-unit-123`, or `issue-123`",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)

    def test_decompose_refine_work_unit_example_carries_existing_handle(self) -> None:
        body = protocol_text("decompose")
        example = re.search(
            r"For refinements produced by `refine-work-unit`:\n\n```(?P<example>.*?)```",
            body,
            flags=re.DOTALL,
        ).group("example")
        keys = block_keys(example)
        handle_fields = {
            match.group("key")
            for match in re.finditer(r"^\s*(?P<key>id|display):", example, flags=re.MULTILINE)
        }

        self.assertIn("instance_id", keys)
        self.assertIn("handle", keys)
        self.assertEqual({"id", "display"}, handle_fields)


if __name__ == "__main__":
    unittest.main()
