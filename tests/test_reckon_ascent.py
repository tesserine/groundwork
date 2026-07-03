import re
import unittest
from pathlib import Path

from tooling.prose_conformance import frontmatter


ROOT = Path(__file__).resolve().parents[1]
RECKON = ROOT / "skills" / "reckon" / "SKILL.md"
EXCAVATION = ROOT / "skills" / "reckon" / "references" / "excavation.md"
CHANGELOG = ROOT / "CHANGELOG.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def prose(body: str) -> str:
    return re.sub(r"\s+", " ", body)


def section(body: str, heading: str) -> str:
    start = body.index(heading)
    next_heading = re.search(r"^##\s+", body[start + len(heading) :], re.MULTILINE)
    if next_heading is None:
        return body[start:]
    return body[start : start + len(heading) + next_heading.start()]


class ReckonAscentTests(unittest.TestCase):
    def test_excavation_intro_names_both_purpose_directions(self) -> None:
        intro = prose(read(EXCAVATION).split("## Socratic Drilling", 1)[0])

        self.assertIn("both purpose-directions", intro)
        self.assertIn("down to bedrock-fact", intro)
        self.assertIn("up to bedrock-purpose", intro)
        self.assertNotIn("actively drill to bedrock. Apply them during Orient and Decompose", intro)

    def test_ascent_section_defines_the_purpose_ladder(self) -> None:
        ascent = prose(section(read(EXCAVATION), "## Ascent (the Purpose Ladder)"))

        for expected in [
            "issue -> epic -> application-as-is -> application-as-envisioned -> ecosystem -> the exigence",
            "does this choice still serve that?",
            "terminates at the exigence",
            "bedrock-purpose",
            "fires during Reconstruct",
            "Recursive Why reaches the verified user need as a fact",
            "Ascent reaches it as the teleology a choice must serve",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, ascent)

    def test_ascent_trigger_is_a_verifiable_structural_condition(self) -> None:
        ascent = prose(section(read(EXCAVATION), "## Ascent (the Purpose Ladder)"))

        self.assertIn("local exigence admits multiple locally-valid solutions", ascent)
        self.assertIn("different structural characteristics", ascent)
        for structural_action in [
            "introduces a dependency",
            "creates an artifact",
            "commits to a mechanism",
        ]:
            with self.subTest(structural_action=structural_action):
                self.assertIn(structural_action, ascent)

    def test_purpose_drift_is_declared_as_a_dynamic_corruption_mode(self) -> None:
        corruption_modes = prose(read(RECKON).split("Dynamic face:", 1)[1])

        self.assertIn("**purpose drift**", corruption_modes)
        self.assertIn("structural choice", corruption_modes)
        self.assertIn("downward-sound links", corruption_modes)
        self.assertIn("stopped serving Orient's purpose", corruption_modes)
        self.assertIn("run Ascent", corruption_modes)
        self.assertIn("Local coherence", corruption_modes)
        self.assertIn("detail", corruption_modes)
        self.assertIn("structure", corruption_modes)

    def test_recognition_index_and_pointer_reach_ascent(self) -> None:
        body = read(RECKON)
        recognition = prose(section(body, "## Recognition Index"))

        self.assertIn("| Purpose drift |", recognition)
        self.assertIn("locally sound structure", recognition)
        self.assertIn("locally-valid detail", recognition)
        self.assertIn("Ascent", recognition)
        self.assertIn("climb to the exigence", recognition)
        self.assertIn("[references/excavation.md](references/excavation.md)", recognition)
        self.assertIn(
            "Purpose drift is a dynamic-face corruption whose full exposition is in the Corruption Modes section below.",
            recognition,
        )

    def test_upward_anchor_is_woven_through_the_skill_surface(self) -> None:
        reckon = read(RECKON)
        excavation = read(EXCAVATION)
        two_faces = section(reckon, "## The Discipline Beneath the Move")
        recognition = section(reckon, "## Recognition Index")
        closing = reckon.rsplit("---", 1)[1]

        self.assertIn("upward purpose anchor", prose(section(excavation, "## Ascent (the Purpose Ladder)")))
        self.assertIn("upward purpose anchor", prose(two_faces))
        closing_prose = prose(closing)

        self.assertIn(
            "Orient returns you to what is needed and, through Ascent, back upward to purpose before structure sets.",
            closing_prose,
        )
        self.assertNotIn("Ascent names purpose as an anchor you return to", closing_prose)
        self.assertIn("Purpose drift", prose(recognition))
        self.assertIn("Ascent", prose(recognition))

    def test_reckon_version_and_changelog_record_the_addition(self) -> None:
        reckon = read(RECKON)
        changelog = prose(read(CHANGELOG).split("## [Unreleased]", 1)[1].split("### Changed", 1)[0])
        metadata = frontmatter(reckon)["metadata"]

        self.assertRegex(metadata["version"], r"^[0-9]+[.][0-9]+[.][0-9]+$")
        self.assertRegex(metadata["updated"], r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
        self.assertIn("Ascent", changelog)
        self.assertIn("Purpose Ladder", changelog)
        self.assertIn("Purpose drift", changelog)


if __name__ == "__main__":
    unittest.main()
