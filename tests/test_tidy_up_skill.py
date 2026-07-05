import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TIDY_UP = ROOT / "skills" / "tidy-up" / "SKILL.md"
TIDY_UP_SCRIPT = ROOT / "skills" / "tidy-up" / "scripts" / "tidy_up.py"
LAND = ROOT / "protocols" / "land" / "PROTOCOL.md"
CONTRACT = ROOT / "skills" / "contract" / "SKILL.md"
ORIENT = ROOT / "skills" / "orient" / "SKILL.md"
README = ROOT / "README.md"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def section(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^## {re.escape(heading)}\n(?P<section>.*?)(?=^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing section: {heading}")
    return match.group("section")


def subsection(body: str, heading: str) -> str:
    pattern = re.compile(
        rf"^### {re.escape(heading)}\n(?P<section>.*?)(?=^### |^## |\Z)",
        flags=re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(body)
    if match is None:
        raise AssertionError(f"missing subsection: {heading}")
    return match.group("section")


def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


class TidyUpSkillTests(unittest.TestCase):
    def test_skill_declares_four_distinct_canonical_clean_checks(self) -> None:
        clean_state = section(read(TIDY_UP), "The Canonical Clean State")
        checks = re.findall(r"(?m)^\d+[.] \*\*(?P<name>[^*]+)\*\*", clean_state)

        self.assertEqual(
            [
                "Working tree porcelain-clean.",
                "HEAD rests on the canonical branch.",
                "No run-scoped residue outside ignored paths.",
                "Landed work is untouched.",
            ],
            checks,
        )
        for expected in [
            "git status --porcelain",
            "origin/HEAD",
            "untracked-unignored residue",
            "byte-for-byte",
            "workspace.md",
            "Outcome 1",
            "Outcome 3",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, clean_state)

    def test_each_termination_kind_has_distinct_action_prose_and_invocation(self) -> None:
        termination = section(read(TIDY_UP), "Termination Kinds")
        expectations = {
            "Land": ["approved change has been applied", "deletes the supplied run branch", "land"],
            "Abandonment and Regeneration": [
                "work must not remain",
                "deletes the supplied run branch carrying unlanded work",
                "abandon",
            ],
            "Halt": ["disposition still needs to be visible", "halt-marked commit", "halt"],
        }

        for heading, expected_terms in expectations.items():
            with self.subTest(heading=heading):
                body = subsection(termination, heading)
                prose = normalized(body)
                for term in expected_terms:
                    self.assertIn(term, prose)
                self.assertIn(
                    f"python3 skills/tidy-up/scripts/tidy_up.py {expected_terms[-1]}",
                    body,
                )

        self.assertTrue(TIDY_UP_SCRIPT.is_file())

    def test_land_steps_section_invokes_tidy_up(self) -> None:
        body = read(LAND)
        steps = body.split("## Steps", 1)[1].split("## Failure Policy", 1)[0]
        cross_refs = body.split("## Cross-References", 1)[1]

        self.assertIn("6. **Tidy up.**", steps)
        self.assertIn("skills/tidy-up/SKILL.md", steps)
        self.assertIn("completion-record", steps)
        self.assertIn("change-proposal.branch", steps)
        self.assertIn("--run-branch", steps)
        self.assertIn("skills/tidy-up/SKILL.md", cross_refs)

    def test_non_land_surfaces_reference_one_skill_without_command_blocks(self) -> None:
        disposition = section(read(CONTRACT), "The disposition default")
        orient_shape = section(read(ORIENT), "The Shape of the Work")
        orient_disciplines = section(read(ORIENT), "Cross-Cutting Disciplines")

        for name, body in [
            ("contract disposition default", disposition),
            ("orient shape", orient_shape),
            ("orient disciplines", orient_disciplines),
        ]:
            with self.subTest(surface=name):
                self.assertIn("skills/tidy-up/SKILL.md", body)
                self.assertNotIn("```", body)

    def test_discovery_surfaces_reach_tidy_up(self) -> None:
        readme = read(README)
        changelog = read(ROOT / "CHANGELOG.md")

        self.assertIn("skills/tidy-up/SKILL.md", readme)
        self.assertIn("tests/test_tidy_up_skill.py", changelog)
        self.assertIn("tests/test_tidy_up_mechanics.py", changelog)

    def test_skill_prose_names_loud_failure_and_single_mechanics_home(self) -> None:
        body = normalized(read(TIDY_UP))

        for expected in [
            "canonical-clean residual",
            "exits nonzero",
            "script is the mechanics home",
            "Mechanics duplication",
            "Ignored-boundary breach",
        ]:
            with self.subTest(expected=expected):
                self.assertIn(expected, body)


if __name__ == "__main__":
    unittest.main()
