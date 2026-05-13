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


class ProtocolArtifactDeliveryDocsTests(unittest.TestCase):
    def test_all_artifact_producing_protocols_explain_mcp_tool_input_boundary(self) -> None:
        producers = [protocol for protocol in manifest_protocols() if protocol["produces"]]

        self.assertEqual(
            [
                "survey",
                "decompose",
                "take",
                "specify",
                "plan",
                "implement",
                "verify",
                "document",
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


if __name__ == "__main__":
    unittest.main()
