import os
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(
    args: list[str],
    cwd: Path,
    *,
    check: bool = False,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    result = subprocess.run(
        args,
        cwd=cwd,
        env=merged_env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed: {' '.join(args)}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return result


def assert_success(test: unittest.TestCase, result: subprocess.CompletedProcess[str]) -> None:
    test.assertEqual(
        result.returncode,
        0,
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
    )


def assert_failure_contains(
    test: unittest.TestCase,
    result: subprocess.CompletedProcess[str],
    expected: str,
) -> None:
    test.assertNotEqual(result.returncode, 0, f"command unexpectedly succeeded\n{result.stdout}")
    test.assertIn(expected, result.stderr)


class ReleaseFixture:
    def __init__(self, name: str, version: str = "1.2.3") -> None:
        self.root = Path(tempfile.mkdtemp(prefix=f"groundwork-release-{name}-"))
        self.write_valid_surface(version)
        self.install_scripts()

    def write(self, relative: str, contents: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(contents).lstrip(), encoding="utf-8")

    def remove(self, relative: str) -> None:
        path = self.root / relative
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()

    def install_scripts(self) -> None:
        scripts = self.root / "scripts"
        scripts.mkdir(exist_ok=True)
        for name in ["release_lib.py", "release-check", "release-cut"]:
            source = ROOT / "scripts" / name
            destination = scripts / name
            shutil.copy(source, destination)
            if name != "release_lib.py":
                destination.chmod(destination.stat().st_mode | stat.S_IXUSR)

    def write_valid_surface(self, version: str) -> None:
        self.write(
            "manifest.toml",
            f"""
            name = "groundwork"
            version = "{version}"

            [[artifact_types]]
            name = "claim"

            [[protocols]]
            name = "take"
            requires = ["claim"]
            accepts = []
            produces = ["claim"]
            may_produce = []
            trigger = {{ type = "on_artifact", name = "claim" }}
            """,
        )
        self.write(
            "CHANGELOG.md",
            f"""
            # Changelog

            ## [Unreleased]

            ## [{version}] — 2026-05-05

            ### Added

            - Release ceremony tooling.
            """,
        )
        self.write("schemas/claim.schema.json", '{"type":"object"}\n')
        self.write("protocols/take/PROTOCOL.md", "# Take\n")
        self.write("skills/orient/SKILL.md", "# Orient\n")
        self.write("README.md", "# Groundwork\n")
        self.write("RELEASING.md", "scripts/release-cut vX.Y.Z\nADR-0012\n")
        self.write_release_workflow(
            """
            name: Release

            on:
              push:
                tags:
                  - "v*"

            jobs:
              publish:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v4

                  - name: Restore annotated tag refs
                    run: git fetch --tags --force origin

                  - name: Verify restored tag matches event
                    run: |
                      restored_commit=$(git rev-parse "refs/tags/$GITHUB_REF_NAME^{commit}")
                      if [ "$restored_commit" != "$GITHUB_SHA" ]; then
                        echo "Tag $GITHUB_REF_NAME moved since trigger: expected $GITHUB_SHA, got $restored_commit" >&2
                        exit 1
                      fi

                  - name: Require annotated tag
                    run: test "$(git cat-file -t "refs/tags/$GITHUB_REF_NAME")" = tag

                  - name: Require tag target on main
                    run: git merge-base --is-ancestor "$tag_commit" refs/remotes/origin/main

                  - name: Verify release identity
                    run: ./scripts/release-check release "$GITHUB_REF_NAME"
            """
        )
        self.write(".github/workflows/release-metadata.yml", "name: Release Metadata\n")

    def write_release_workflow(self, contents: str) -> None:
        self.write(".github/workflows/release.yml", contents)

    def run_release_check(self, *args: str) -> subprocess.CompletedProcess[str]:
        return run([sys.executable, "scripts/release-check", *args], self.root)

    def run_release_cut(self, *args: str) -> subprocess.CompletedProcess[str]:
        return run([sys.executable, "scripts/release-cut", *args], self.root)

    def init_git_with_remote(self) -> Path:
        remote = self.root.parent / f"{self.root.name}-origin.git"
        run(["git", "init", "-q"], self.root, check=True)
        run(["git", "config", "user.name", "release test"], self.root, check=True)
        run(["git", "config", "user.email", "release-test@example.invalid"], self.root, check=True)
        run(["git", "checkout", "-q", "-b", "main"], self.root, check=True)
        run(["git", "add", "."], self.root, check=True)
        run(["git", "commit", "-q", "-m", "test: seed release fixture"], self.root, check=True)
        run(["git", "init", "--bare", "-q", str(remote)], self.root, check=True)
        run(["git", "remote", "add", "origin", str(remote)], self.root, check=True)
        run(["git", "push", "-q", "-u", "origin", "main"], self.root, check=True)
        return remote

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class ReleaseCeremonyTests(unittest.TestCase):
    def add_fixture(self, name: str, version: str = "1.2.3") -> ReleaseFixture:
        fixture = ReleaseFixture(name, version)
        self.addCleanup(fixture.cleanup)
        return fixture

    def test_metadata_accepts_a_coherent_groundwork_release_surface(self) -> None:
        fixture = self.add_fixture("metadata-success")

        result = fixture.run_release_check("metadata")

        assert_success(self, result)

    def test_metadata_rejects_missing_manifest_version(self) -> None:
        fixture = self.add_fixture("metadata-missing-version")
        fixture.write("manifest.toml", 'name = "groundwork"\n')

        result = fixture.run_release_check("metadata")

        assert_failure_contains(self, result, "manifest.toml top-level version not found")

    def test_metadata_rejects_unsupported_version_strings(self) -> None:
        for version in ["01.2.3", "1.2.3-rc.0", "1.2.3-beta.1", "1.2.3+build.1"]:
            with self.subTest(version=version):
                fixture = self.add_fixture(f"metadata-version-{version.replace('/', '-')}", version)

                result = fixture.run_release_check("metadata")

                assert_failure_contains(self, result, "version must look like X.Y.Z or X.Y.Z-rc.N")

    def test_metadata_derives_methodology_integrity_from_filesystem(self) -> None:
        fixture = self.add_fixture("metadata-derived-integrity")
        fixture.remove("schemas/claim.schema.json")

        result = fixture.run_release_check("metadata")

        assert_failure_contains(self, result, "artifact type claim has no schema")

    def test_metadata_rejects_malformed_schema_json(self) -> None:
        fixture = self.add_fixture("metadata-malformed-schema")
        fixture.write("schemas/claim.schema.json", '{"type": "object"\n')

        result = fixture.run_release_check("metadata")

        assert_failure_contains(self, result, "schema schemas/claim.schema.json is not valid JSON")

    def test_metadata_rejects_duplicate_release_headings_for_one_version(self) -> None:
        fixture = self.add_fixture("metadata-duplicate-release-heading", "1.2.3-rc.1")
        fixture.write(
            "CHANGELOG.md",
            """
            # Changelog

            ## [Unreleased]

            ## [1.2.3-rc.1] — 2026-05-06

            ### Changed

            - Candidate notes from a later section.

            ## [1.2.3-rc.1] — 2026-05-05

            ### Added

            - Candidate notes from an earlier section.
            """,
        )

        result = fixture.run_release_check("metadata")

        assert_failure_contains(
            self,
            result,
            "CHANGELOG.md has duplicate release heading for [1.2.3-rc.1]",
        )

    def test_metadata_rejects_release_workflow_without_tag_ref_restore(self) -> None:
        fixture = self.add_fixture("metadata-workflow-missing-tag-ref-restore")
        fixture.write_release_workflow(
            """
            name: Release

            on:
              push:
                tags:
                  - "v*"

            jobs:
              publish:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v4

                  - name: Verify restored tag matches event
                    run: |
                      restored_commit=$(git rev-parse "refs/tags/$GITHUB_REF_NAME^{commit}")
                      if [ "$restored_commit" != "$GITHUB_SHA" ]; then
                        exit 1
                      fi

                  - name: Require annotated tag
                    run: test "$(git cat-file -t "refs/tags/$GITHUB_REF_NAME")" = tag

                  - name: Require tag target on main
                    run: git merge-base --is-ancestor "$tag_commit" refs/remotes/origin/main

                  - name: Verify release identity
                    run: ./scripts/release-check release "$GITHUB_REF_NAME"
            """
        )

        result = fixture.run_release_check("metadata")

        assert_failure_contains(self, result, "must restore annotated tag refs before checking tag type")

    def test_metadata_rejects_release_workflow_without_event_identity_verification(self) -> None:
        fixture = self.add_fixture("metadata-workflow-missing-event-identity")
        fixture.write_release_workflow(
            """
            name: Release

            on:
              push:
                tags:
                  - "v*"

            jobs:
              publish:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v4

                  - name: Restore annotated tag refs
                    run: git fetch --tags --force origin

                  - name: Require annotated tag
                    run: test "$(git cat-file -t "refs/tags/$GITHUB_REF_NAME")" = tag

                  - name: Require tag target on main
                    run: git merge-base --is-ancestor "$tag_commit" refs/remotes/origin/main

                  - name: Verify release identity
                    run: ./scripts/release-check release "$GITHUB_REF_NAME"
            """
        )

        result = fixture.run_release_check("metadata")

        assert_failure_contains(
            self,
            result,
            "must verify the restored tag matches the triggering event before checking tag type",
        )

    def test_metadata_rejects_release_workflow_that_captures_event_identity_before_restore(self) -> None:
        fixture = self.add_fixture("metadata-workflow-event-assignment-before-restore")
        fixture.write_release_workflow(
            """
            name: Release

            on:
              push:
                tags:
                  - "v*"

            jobs:
              publish:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v4

                  - name: Capture stale tag target
                    run: restored_commit=$(git rev-parse "refs/tags/$GITHUB_REF_NAME^{commit}")

                  - name: Restore annotated tag refs
                    run: git fetch --tags --force origin

                  - name: Verify restored tag matches event
                    run: |
                      if [ "$restored_commit" != "$GITHUB_SHA" ]; then
                        exit 1
                      fi

                  - name: Require annotated tag
                    run: test "$(git cat-file -t "refs/tags/$GITHUB_REF_NAME")" = tag

                  - name: Require tag target on main
                    run: git merge-base --is-ancestor "$tag_commit" refs/remotes/origin/main

                  - name: Verify release identity
                    run: ./scripts/release-check release "$GITHUB_REF_NAME"
            """
        )

        result = fixture.run_release_check("metadata")

        assert_failure_contains(
            self,
            result,
            "must capture the restored tag target after restoring annotated tag refs",
        )

    def test_metadata_rejects_release_workflow_that_compares_event_identity_after_tag_type(self) -> None:
        fixture = self.add_fixture("metadata-workflow-event-comparison-after-tag-type")
        fixture.write_release_workflow(
            """
            name: Release

            on:
              push:
                tags:
                  - "v*"

            jobs:
              publish:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v4

                  - name: Restore annotated tag refs
                    run: git fetch --tags --force origin

                  - name: Capture restored tag target
                    run: restored_commit=$(git rev-parse "refs/tags/$GITHUB_REF_NAME^{commit}")

                  - name: Require annotated tag
                    run: test "$(git cat-file -t "refs/tags/$GITHUB_REF_NAME")" = tag

                  - name: Compare restored tag target
                    run: |
                      if [ "$restored_commit" != "$GITHUB_SHA" ]; then
                        exit 1
                      fi

                  - name: Require tag target on main
                    run: git merge-base --is-ancestor "$tag_commit" refs/remotes/origin/main

                  - name: Verify release identity
                    run: ./scripts/release-check release "$GITHUB_REF_NAME"
            """
        )

        result = fixture.run_release_check("metadata")

        assert_failure_contains(self, result, "must compare the restored tag target before checking tag type")

    def test_metadata_rejects_release_workflow_that_runs_repository_code_before_tag_trust(self) -> None:
        fixture = self.add_fixture("metadata-workflow-repository-code-before-tag-trust")
        fixture.write_release_workflow(
            """
            name: Release

            on:
              push:
                tags:
                  - "v*"

            jobs:
              publish:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v4

                  - name: Restore annotated tag refs
                    run: git fetch --tags --force origin

                  - name: Verify restored tag matches event
                    run: |
                      restored_commit=$(git rev-parse "refs/tags/$GITHUB_REF_NAME^{commit}")
                      if [ "$restored_commit" != "$GITHUB_SHA" ]; then
                        exit 1
                      fi

                  - name: Verify release identity
                    run: ./scripts/release-check release "$GITHUB_REF_NAME"

                  - name: Require annotated tag
                    run: test "$(git cat-file -t "refs/tags/$GITHUB_REF_NAME")" = tag

                  - name: Require tag target on main
                    run: git merge-base --is-ancestor "$tag_commit" refs/remotes/origin/main
            """
        )

        result = fixture.run_release_check("metadata")

        assert_failure_contains(self, result, "must establish tag trust before running repository code")

    def test_metadata_ignores_workflow_comments_when_validating_release_trust_shape(self) -> None:
        fixture = self.add_fixture("metadata-workflow-comment-only-trust")
        fixture.write_release_workflow(
            """
            name: Release

            on:
              push:
                tags:
                  - "v*"

            jobs:
              publish:
                steps:
                  - name: Checkout
                    uses: actions/checkout@v4

                  # run: git fetch --tags --force origin
                  # run: ./scripts/release-check release "$GITHUB_REF_NAME"
                  - name: Commented checks
                    run: |
                      true  # git cat-file -t "refs/tags/$GITHUB_REF_NAME"
                      true  # git merge-base --is-ancestor "$tag_commit" refs/remotes/origin/main

                  - name: Verify release identity
                    run: ./scripts/release-check release "$GITHUB_REF_NAME"
            """
        )

        result = fixture.run_release_check("metadata")

        assert_failure_contains(self, result, "must restore annotated tag refs before checking tag type")

    def test_notes_emit_matching_changelog_section_without_outer_blank_lines(self) -> None:
        fixture = self.add_fixture("notes-success", "1.2.3-rc.1")

        result = fixture.run_release_check("notes", "v1.2.3-rc.1")

        assert_success(self, result)
        self.assertEqual(result.stdout, "### Added\n\n- Release ceremony tooling.\n")

    def test_release_rejects_tag_versions_that_do_not_match_manifest_version(self) -> None:
        fixture = self.add_fixture("release-version-mismatch", "1.2.3")

        result = fixture.run_release_check("release", "v1.2.4")

        assert_failure_contains(self, result, "manifest version 1.2.3 does not match tag version 1.2.4")

    def test_release_rejects_tag_with_non_empty_unreleased_entries(self) -> None:
        fixture = self.add_fixture("release-unreleased-entries", "1.2.3")
        fixture.write(
            "CHANGELOG.md",
            """
            # Changelog

            ## [Unreleased]

            ### Added

            - Pending release note.

            ## [1.2.3] — 2026-05-05

            ### Added

            - Release ceremony tooling.
            """,
        )

        result = fixture.run_release_check("release", "v1.2.3")

        assert_failure_contains(
            self,
            result,
            "Unreleased contains entries; roll them into the release section before tagging",
        )

    def test_release_allows_unreleased_structural_placeholders(self) -> None:
        fixture = self.add_fixture("release-unreleased-placeholders", "1.2.3")
        fixture.write(
            "CHANGELOG.md",
            """
            # Changelog

            ## [Unreleased]

            ### Added

            ### Changed

            ## [1.2.3] — 2026-05-05

            ### Added

            - Release ceremony tooling.
            """,
        )

        result = fixture.run_release_check("release", "v1.2.3")

        assert_success(self, result)

    def test_release_heading_lookup_uses_literal_version_matching(self) -> None:
        fixture = self.add_fixture("release-literal-heading", "1.2.3-rc.1")

        source = (fixture.root / "scripts" / "release_lib.py").read_text(encoding="utf-8")

        self.assertIn("line.startswith(prefix)", source)
        self.assertNotIn("re.search(prefix", source)
        self.assertNotIn("re.fullmatch(prefix", source)

    def test_release_cut_creates_stable_release_commit_and_annotated_tag(self) -> None:
        fixture = self.add_fixture("release-cut-stable", "1.2.2")
        remote = fixture.init_git_with_remote()
        reviewed_main = run(
            ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
            fixture.root,
            check=True,
        ).stdout.strip()

        result = fixture.run_release_cut("v1.2.3")

        assert_success(self, result)
        self.assertEqual((fixture.root / "manifest.toml").read_text().count('version = "1.2.3"'), 1)
        self.assertIn("## [1.2.3] —", (fixture.root / "CHANGELOG.md").read_text())
        self.assertEqual(
            run(["git", "cat-file", "-t", "v1.2.3"], fixture.root, check=True).stdout.strip(),
            "tag",
        )
        self.assertTrue(
            run(["git", "--git-dir", str(remote), "rev-parse", "--verify", "refs/tags/v1.2.3"], fixture.root).returncode
            == 0
        )
        self.assertEqual(
            "1",
            run(
                [
                    "git",
                    "--git-dir",
                    str(remote),
                    "rev-list",
                    "--count",
                    f"{reviewed_main}..refs/heads/main",
                ],
                fixture.root,
                check=True,
            ).stdout.strip(),
        )
        assert_success(self, fixture.run_release_check("release", "v1.2.3"))

    def test_release_cut_creates_release_candidate_release_commit_and_tag(self) -> None:
        fixture = self.add_fixture("release-cut-rc", "1.2.3")
        fixture.init_git_with_remote()

        result = fixture.run_release_cut("v1.2.3-rc.1")

        assert_success(self, result)
        self.assertIn('version = "1.2.3-rc.1"', (fixture.root / "manifest.toml").read_text())
        assert_success(self, fixture.run_release_check("release", "v1.2.3-rc.1"))

    def test_release_cut_atomic_push_leaves_remote_refs_unchanged_on_tag_rejection(self) -> None:
        fixture = self.add_fixture("release-cut-atomic", "1.2.2")
        remote = fixture.init_git_with_remote()
        run(["git", "--git-dir", str(remote), "tag", "v1.2.3", "main"], fixture.root, check=True)

        result = fixture.run_release_cut("v1.2.3")

        assert_failure_contains(self, result, "atomic push failed")
        self.assertEqual(
            run(["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"], fixture.root, check=True).stdout,
            run(["git", "--git-dir", str(remote), "rev-parse", "v1.2.3"], fixture.root, check=True).stdout,
        )

    def test_release_cut_preserves_pre_existing_local_tag(self) -> None:
        fixture = self.add_fixture("release-cut-existing-local-tag", "1.2.2")
        fixture.init_git_with_remote()
        run(["git", "tag", "v1.2.3", "HEAD"], fixture.root, check=True)
        before = run(["git", "rev-parse", "v1.2.3^{commit}"], fixture.root, check=True).stdout

        result = fixture.run_release_cut("v1.2.3")

        assert_failure_contains(self, result, "local tag v1.2.3 already exists")
        self.assertEqual(
            before,
            run(["git", "rev-parse", "v1.2.3^{commit}"], fixture.root, check=True).stdout,
        )

    def test_release_cut_rejects_clean_main_with_local_commits_ahead_of_origin(self) -> None:
        fixture = self.add_fixture("release-cut-local-ahead-main", "1.2.2")
        remote = fixture.init_git_with_remote()
        remote_before = run(
            ["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"],
            fixture.root,
            check=True,
        ).stdout
        fixture.write("README.md", "# Groundwork\n\nLocal unreleased work.\n")
        run(["git", "add", "README.md"], fixture.root, check=True)
        run(["git", "commit", "-q", "-m", "test: local unreviewed work"], fixture.root, check=True)
        local_before = run(["git", "rev-parse", "HEAD"], fixture.root, check=True).stdout

        result = fixture.run_release_cut("v1.2.3")

        assert_failure_contains(self, result, "main is 1 commit ahead of origin/main")
        self.assertEqual(local_before, run(["git", "rev-parse", "HEAD"], fixture.root, check=True).stdout)
        self.assertEqual("", run(["git", "status", "--short"], fixture.root, check=True).stdout)
        self.assertEqual(
            remote_before,
            run(["git", "--git-dir", str(remote), "rev-parse", "refs/heads/main"], fixture.root, check=True).stdout,
        )
        self.assertNotEqual(
            0,
            run(["git", "show-ref", "--verify", "--quiet", "refs/tags/v1.2.3"], fixture.root).returncode,
        )


class ReleaseRepositoryContractTests(unittest.TestCase):
    def read(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_manifest_declares_current_methodology_version(self) -> None:
        self.assertIn('version = "0.1.2-rc.1"', self.read("manifest.toml"))

    def test_release_workflow_verifies_annotated_tags_and_has_no_path_filter(self) -> None:
        workflow = self.read(".github/workflows/release.yml")

        self.assertIn("git fetch --tags --force origin", workflow)
        self.assertIn('restored_commit=$(git rev-parse "refs/tags/$GITHUB_REF_NAME^{commit}")', workflow)
        self.assertIn('if [ "$restored_commit" != "$GITHUB_SHA" ]; then', workflow)
        self.assertIn("refs/tags/$GITHUB_REF_NAME", workflow)
        self.assertIn("./scripts/release-check release \"$GITHUB_REF_NAME\"", workflow)
        self.assertIn("./scripts/release-check notes \"$GITHUB_REF_NAME\"", workflow)
        self.assertNotIn("paths:", workflow)

    def test_release_workflow_marks_only_documented_rc_tags_as_prereleases(self) -> None:
        workflow = self.read(".github/workflows/release.yml")

        self.assertIn("^v[0-9]+[.][0-9]+[.][0-9]+-rc[.][1-9][0-9]*$", workflow)
        self.assertNotIn("[[ \"$GITHUB_REF_NAME\" == *-* ]]", workflow)

    def test_release_metadata_workflow_is_split_from_tag_publication(self) -> None:
        workflow = self.read(".github/workflows/release-metadata.yml")

        self.assertIn("name: Release Metadata", workflow)
        self.assertIn("pull_request:", workflow)
        self.assertIn("paths:", workflow)
        self.assertIn("./scripts/release-check metadata", workflow)

    def test_releasing_documentation_matches_verifier_contract(self) -> None:
        releasing = self.read("RELEASING.md")

        self.assertIn("manifest.toml", releasing)
        self.assertIn("scripts/release-cut vX.Y.Z[-rc.N]", releasing)
        self.assertIn("ADR-0012", releasing)
        self.assertIn("Only `vX.Y.Z-rc.N` tags are published as GitHub prereleases.", releasing)


if __name__ == "__main__":
    unittest.main()
