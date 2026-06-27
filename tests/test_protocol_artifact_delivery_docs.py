import re
import tomllib
import unittest
from pathlib import Path


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
    def test_public_docs_do_not_describe_interactive_adapter_bypass(self) -> None:
        checked_paths = [
            ROOT / "README.md",
            ROOT / "scripts" / "groundwork-install",
            *sorted((ROOT / "docs").rglob("*.md")),
            *sorted((ROOT / "scripts").glob("*.md")),
        ]
        forbidden = [
            "interactive-artifact-delivery-adapter",
            "interactive artifact-delivery adapter",
            "interactive artifact delivery adapter",
            "session working file",
            "no runa runtime",
            "does not persist artifacts",
        ]

        for path in checked_paths:
            body = path.read_text(encoding="utf-8")
            for phrase in forbidden:
                with self.subTest(path=path.relative_to(ROOT), phrase=phrase):
                    self.assertNotIn(phrase, body)

    def test_all_artifact_producing_protocols_explain_mcp_tool_input_boundary(self) -> None:
        producers = [protocol for protocol in manifest_protocols() if protocol["produces"]]

        self.assertEqual(
            [
                "survey",
                "decompose",
                "take",
                "plan",
                "implement",
                "verify",
                "submit",
                "land",
            ],
            [protocol["name"] for protocol in producers],
        )

        for protocol in producers:
            protocol_name = protocol["name"]
            artifact = protocol["produces"][0]
            body = normalized_protocol(protocol_name)

            with self.subTest(protocol=protocol_name, artifact=artifact):
                self.assertIn(f"`{artifact}` MCP tool", body)
                self.assertIn("MCP tool input, not artifact body", body)
                self.assertIn("`instance_id` is a tool parameter", body)
                self.assertIn("extracted before validating artifact content", body)
                self.assertIn("must not appear in the artifact body", body)
                self.assertIn("Do not write", body)
                self.assertIn("directly", body)

    def test_scoped_protocol_delivery_docs_preserve_work_unit_injection_contract(self) -> None:
        for protocol in manifest_protocols():
            if not protocol["produces"]:
                continue

            protocol_name = protocol["name"]
            body = normalized_protocol(protocol_name)

            with self.subTest(protocol=protocol_name):
                if protocol.get("scoped") is True:
                    self.assertIn("Runa injects `work_unit` from session context", body)
                    self.assertIn("agent does not supply `work_unit`", body)
                else:
                    self.assertIn("runa does not inject `work_unit`", body.lower())

    def test_artifact_validation_sentences_name_post_extraction_body_scope(self) -> None:
        producers = [protocol for protocol in manifest_protocols() if protocol["produces"]]

        for protocol in producers:
            protocol_name = protocol["name"]
            body = normalized_protocol(protocol_name)
            validation_sentence = re.search(r"Runa validates [^.]+\.", body)

            with self.subTest(protocol=protocol_name):
                self.assertIsNotNone(validation_sentence)
                self.assertIn(
                    "remaining artifact body fields against",
                    validation_sentence.group(0),
                )
                self.assertNotIn("validates the payload against", validation_sentence.group(0))

    def test_decompose_delivery_docs_preserve_ticket_backed_work_unit_identity_rules(self) -> None:
        body = normalized_protocol("decompose")

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
        match = re.search(
            r"For refinements produced by `refine-work-unit`:\n\n```(?P<example>.*?)```",
            body,
            flags=re.DOTALL,
        )

        self.assertIsNotNone(match)
        example = match.group("example")

        for expected in [
            'instance_id: "<existing-instance-id>"',
            "handle: {",
            'id: "<existing connector handle id>"',
            'display: "<existing connector handle display>"',
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, example)


if __name__ == "__main__":
    unittest.main()
