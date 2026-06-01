import json
import re
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "manifest.toml"
FIXTURES = ROOT / "tests" / "fixtures" / "artifacts"


def manifest() -> dict:
    return tomllib.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def protocol(name: str) -> dict:
    for entry in manifest()["protocols"]:
        if entry["name"] == name:
            return entry
    raise AssertionError(f"protocol {name} not found")


def normalized_protocol(name: str) -> str:
    text = (ROOT / "protocols" / name / "PROTOCOL.md").read_text(encoding="utf-8")
    return re.sub(r"\s+", " ", text)


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def mechanics_for_forge(forge_tag: str) -> list[dict]:
    mechanics = []
    for path in sorted((ROOT / "mechanics").rglob("*.toml")):
        mechanic = tomllib.loads(path.read_text(encoding="utf-8"))
        if mechanic.get("forge_tag") == forge_tag:
            mechanics.append(mechanic)
    return mechanics


class ReferenceArcTopologyTests(unittest.TestCase):
    def test_manifest_routes_submit_review_land_through_disposition_artifacts(self) -> None:
        artifact_types = {entry["name"] for entry in manifest()["artifact_types"]}
        mechanics = {entry["name"] for entry in manifest()["mechanics"]}

        self.assertNotIn("patch", artifact_types)
        self.assertTrue(
            {
                "deliver-change-proposal",
                "revise",
                "review",
                "apply-approved-change",
                "reflect-disposition",
                "close-out",
            }.issubset(mechanics)
        )

        submit = protocol("submit")
        self.assertEqual(["completion-evidence", "documentation-record"], submit["requires"])
        self.assertEqual(["change-proposal", "change-needs-revision"], submit["accepts"])
        self.assertEqual(["change-proposal"], submit["produces"])
        self.assertEqual(
            {
                "type": "any_of",
                "conditions": [
                    {"type": "on_artifact", "name": "documentation-record"},
                    {"type": "on_artifact", "name": "change-needs-revision"},
                ],
            },
            submit["trigger"],
        )

        review = protocol("review")
        self.assertEqual(["change-proposal"], review["requires"])
        self.assertEqual({"change-approved", "change-needs-revision"}, set(review["required_output_choices"][0]["members"]))

        land = protocol("land")
        self.assertEqual(["change-approved", "change-proposal"], land["requires"])
        self.assertIn("completion-evidence", land["accepts"])
        self.assertEqual(["completion-record"], land["produces"])
        self.assertEqual({"type": "on_artifact", "name": "change-approved"}, land["trigger"])

    def test_github_reference_arc_mechanics_are_bound_once_in_manifest_and_c3(self) -> None:
        operations = {
            "deliver-change-proposal",
            "apply-approved-change",
            "reflect-disposition",
        }
        manifest_mechanics = {entry["name"]: entry for entry in manifest()["mechanics"]}
        github_mechanics = mechanics_for_forge("github")

        for operation in operations:
            self.assertIn("github", manifest_mechanics[operation]["forge_tags"])
            self.assertEqual(1, sum(1 for mechanic in github_mechanics if mechanic["name"] == operation))

    def test_land_approved_proposal_resolution_uses_work_unit_and_version_together(self) -> None:
        v1 = load_fixture("valid-change-proposal-github-issue340-v1.json")
        v2 = load_fixture("valid-change-proposal-github-issue340-v2.json")
        colliding_v2 = load_fixture("valid-change-proposal-github-issue341-v2.json")
        needs_revision = load_fixture("valid-change-needs-revision-issue340-v1.json")
        approved = load_fixture("valid-change-approved-issue340-v2.json")

        self.assertEqual(v1["work_unit"], v2["work_unit"])
        self.assertEqual(v1["handle"]["forge_tag"], v2["handle"]["forge_tag"])
        self.assertEqual(v1["handle"]["number"], v2["handle"]["number"])
        self.assertEqual(v1["version"], needs_revision["against_version"])
        self.assertEqual(v2["version"], approved["against_version"])

        proposals = [v1, colliding_v2, v2]
        version_only_matches = [proposal for proposal in proposals if proposal["version"] == approved["against_version"]]
        resolved = [
            proposal
            for proposal in proposals
            if proposal["work_unit"] == approved["work_unit"]
            and proposal["version"] == approved["against_version"]
        ]

        self.assertEqual(2, len(version_only_matches))
        self.assertEqual([v2], resolved)
        self.assertEqual("fb5ed767589810bfe5ef93f5b0a9e9c48b97c11a", resolved[0]["commit"])

    def test_submit_and_land_protocols_are_what_layer_disposition_protocols(self) -> None:
        submit = normalized_protocol("submit")
        land = normalized_protocol("land")

        self.assertIn("`change-proposal` MCP tool", submit)
        self.assertIn("`completion-record` MCP tool", land)
        self.assertIn("`change-needs-revision`", submit)
        self.assertIn("`change-approved`", land)
        self.assertIn("`work_unit` matches `change-approved.work_unit`", land)
        self.assertIn("`version` equals `change-approved.against_version`", land)

        for forbidden in ["`patch` artifact", "`patch` MCP tool", "pr-merge", "create-pr"]:
            self.assertNotIn(forbidden, submit)
            self.assertNotIn(forbidden, land)


if __name__ == "__main__":
    unittest.main()
