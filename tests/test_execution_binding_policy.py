"""The execution-binding policy home: policy.toml.

ADR-0010 separates what a criterion is (contract content: the claim and
the operational procedure that checks it) from where its check runs (a
binding, selected per criterion). The binding register and the CI-gating
constraint are revisable policy with a single home: ``policy.toml`` at
the repository root, beside ``manifest.toml``.

The exactly-once gate consults the home rather than modelling it: it
reads the ``ci_gating`` line from ``policy.toml`` at run time and holds
no copy of it, so the gate follows any revision of the line unchanged
and structurally cannot match itself.
"""

import subprocess
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policy.toml"

BINDING_SET = {"ci", "harness", "manual"}
STRENGTHENING_ORDER = ["manual", "harness", "ci"]


def _execution_binding() -> dict:
    with POLICY_PATH.open("rb") as handle:
        return tomllib.load(handle)["execution-binding"]


class PolicyHomeTests(unittest.TestCase):
    """policy.toml exists at the root and carries the register."""

    def test_policy_home_exists_beside_manifest(self) -> None:
        self.assertTrue(POLICY_PATH.is_file())
        self.assertTrue((ROOT / "manifest.toml").is_file())

    def test_execution_binding_table_present(self) -> None:
        self.assertIsInstance(_execution_binding(), dict)


class BindingRegisterTests(unittest.TestCase):
    """The register declares the binding set, self-described."""

    def test_binding_set_is_exactly_ci_harness_manual(self) -> None:
        self.assertEqual(set(_execution_binding()["bindings"]), BINDING_SET)

    def test_every_binding_carries_a_meaning(self) -> None:
        meanings = _execution_binding()["meanings"]

        self.assertEqual(set(meanings), BINDING_SET)
        for binding, meaning in meanings.items():
            with self.subTest(binding=binding):
                self.assertIsInstance(meaning, str)
                self.assertTrue(meaning.strip())

    def test_attestation_redefinition_stated_at_the_home(self) -> None:
        attestation = _execution_binding()["attestation"]

        self.assertIsInstance(attestation, str)
        self.assertTrue(attestation.strip())

    def test_strengthening_is_monotone_weakest_to_strongest(self) -> None:
        strengthening = _execution_binding()["strengthening"]

        self.assertEqual(strengthening, STRENGTHENING_ORDER)
        self.assertEqual(set(strengthening), BINDING_SET)


class CiGatingConstraintTests(unittest.TestCase):
    """The CI-gating constraint: one revisable line, one home."""

    def test_constraint_is_one_revisable_line(self) -> None:
        line = _execution_binding()["ci_gating"]

        self.assertIsInstance(line, str)
        self.assertTrue(line.strip())
        self.assertNotIn("\n", line)

    def test_constraint_occurs_exactly_once_repository_wide(self) -> None:
        """The only tracked file containing the constraint line is the home.

        The line is read from policy.toml, never hardcoded here, so this
        gate enforces the count for whatever the home currently states.
        """
        line = _execution_binding()["ci_gating"]
        tracked = subprocess.run(
            ["git", "ls-files", "-z"],
            cwd=ROOT,
            capture_output=True,
            check=True,
        ).stdout.decode("utf-8")

        containing = []
        for name in filter(None, tracked.split("\0")):
            path = ROOT / name
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
            except (IsADirectoryError, FileNotFoundError):
                continue
            if line in content:
                containing.append(name)

        self.assertEqual(containing, ["policy.toml"])


if __name__ == "__main__":
    unittest.main()
