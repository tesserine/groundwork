import json
import os
import re
import subprocess
import tempfile
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


def mechanic_for_forge(forge_tag: str, name: str) -> dict:
    matches = [mechanic for mechanic in mechanics_for_forge(forge_tag) if mechanic["name"] == name]
    if len(matches) != 1:
        raise AssertionError(f"expected one {forge_tag} mechanic named {name}, found {len(matches)}")
    return matches[0]


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def remote_ref_commit(remote: Path, ref: str, cwd: Path) -> str:
    rows = run_git(["ls-remote", str(remote), ref], cwd).splitlines()
    for row in rows:
        commit, remote_ref = row.split("\t", maxsplit=1)
        if remote_ref == ref:
            return commit
    return ""


def push_remote_ref(remote: Path, ref: str, commit: str, cwd: Path, *, force: bool = False) -> None:
    if ref.startswith("refs/proposals/"):
        source_prefix = "refs/groundwork/tests"
        source_ref = f"{source_prefix}/{ref.removeprefix('refs/proposals/')}"
        run_git(["update-ref", source_ref, commit], cwd)
        command = ["push"]
        if force:
            command.append("--force")
        command.extend([str(remote), f"{source_prefix}/*:refs/proposals/*"])
        run_git(command, cwd)
        run_git(["update-ref", "-d", source_ref], cwd)
        return

    command = ["push"]
    if force:
        command.append("--force")
    command.extend([str(remote), f"{commit}:{ref}"])
    run_git(command, cwd)


class ReferenceArcTopologyTests(unittest.TestCase):
    def run_mechanic_invocation(
        self, invocation: str, replacements: dict[str, str], bin_dir: Path, cwd: Path | None = None
    ) -> subprocess.CompletedProcess:
        environment = os.environ.copy()
        environment.update(replacements)
        environment["PATH"] = f"{bin_dir}{os.pathsep}{environment['PATH']}"
        return subprocess.run(
            invocation,
            shell=True,
            executable="/bin/sh",
            cwd=cwd or ROOT,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

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

    def test_reference_arc_mechanics_are_bound_once_per_forge_in_manifest_and_c3(self) -> None:
        operations = {
            "deliver-change-proposal",
            "apply-approved-change",
            "reflect-disposition",
            "close-out",
        }
        manifest_mechanics = {entry["name"]: entry for entry in manifest()["mechanics"]}

        for forge_tag in {"github", "sourcehut"}:
            forge_mechanics = mechanics_for_forge(forge_tag)
            for operation in operations:
                self.assertIn(forge_tag, manifest_mechanics[operation]["forge_tags"])
                self.assertEqual(1, sum(1 for mechanic in forge_mechanics if mechanic["name"] == operation))

    def test_reference_arc_mechanics_declare_deployment_resolved_parameters(self) -> None:
        expected = {
            ("github", "deliver-change-proposal"): {"repository": "repository"},
            ("github", "apply-approved-change"): {"repository": "repository"},
            ("github", "reflect-disposition"): {"repository": "repository"},
            ("github", "close-out"): {"repository": "repository"},
            ("sourcehut", "deliver-change-proposal"): {
                "ssh_remote": "ssh_remote",
            },
            ("sourcehut", "apply-approved-change"): {"ssh_remote": "ssh_remote"},
            ("sourcehut", "reflect-disposition"): {
                "tracker_id": "tracker_id",
                "todo_query_url": "todo_query_url",
            },
            ("sourcehut", "close-out"): {
                "tracker_id": "tracker_id",
                "todo_query_url": "todo_query_url",
            },
        }

        for (forge_tag, operation), deployment_values in expected.items():
            with self.subTest(forge_tag=forge_tag, operation=operation):
                mechanic = mechanic_for_forge(forge_tag, operation)
                parameters = {parameter["name"]: parameter for parameter in mechanic["parameters"]}
                for parameter_name, deployment_value in deployment_values.items():
                    self.assertEqual(deployment_value, parameters[parameter_name].get("deployment_value"))
                    self.assertTrue(parameters[parameter_name]["required"])

    def test_sourcehut_apply_mechanic_uses_proposal_ref_and_commit_identity(self) -> None:
        apply = mechanic_for_forge("sourcehut", "apply-approved-change")
        invocation = apply["default_invocation"]

        self.assertIn('git fetch "$ssh_remote" "$proposal_ref"', invocation)
        self.assertIn("git rev-parse FETCH_HEAD", invocation)
        self.assertIn('approved_resolved=$(git rev-parse "${approved_commit}^{commit}")', invocation)
        self.assertIn('"$approved_resolved:$target_ref"', invocation)
        self.assertIn("resolved by work_unit and against_version", apply["purpose"])
        self.assertNotIn('git am', invocation)
        self.assertNotIn("expected_tree", invocation)
        self.assertNotIn("HEAD^{tree}", invocation)
        self.assertNotIn("GIT_COMMITTER_DATE", invocation)
        self.assertNotIn("| cut", invocation)

    def test_sourcehut_deliver_mechanic_records_distinct_branch_and_proposal_ref_without_mail_carrier(self) -> None:
        deliver = mechanic_for_forge("sourcehut", "deliver-change-proposal")
        invocation = deliver["default_invocation"]
        parameters = {parameter["name"] for parameter in deliver["parameters"]}
        combined = " ".join(
            [
                deliver["purpose"],
                invocation,
                deliver["outcome"]["description"],
                *deliver["examples"],
            ]
        )

        self.assertIn('git push --force-with-lease="$proposal_ref:" "$ssh_remote"', invocation)
        self.assertIn("branch", parameters)
        self.assertIn("proposal_ref", parameters)
        self.assertNotIn("m" + "box_file", parameters)
        self.assertNotIn("artifact_tag", parameters)
        self.assertNotIn("m" + "box_filename", parameters)
        self.assertNotIn("repo_id", parameters)
        self.assertNotIn("git_query_url", parameters)
        self.assertNotIn("token", parameters)
        self.assertIn('branch_ref="refs/heads/${branch}"', invocation)
        self.assertIn('git push "$ssh_remote" "$commit_resolved:$branch_ref"', invocation)
        self.assertIn('"$proposal_source_prefix/*:refs/proposals/*"', invocation)
        self.assertIn("awk -v ref=", invocation)
        self.assertNotIn("| cut", invocation)
        self.assertLess(invocation.index('branch_ref="refs/heads/${branch}"'), invocation.index('--force-with-lease="$proposal_ref:"'))
        self.assertNotIn("git format-patch", combined)
        self.assertNotIn("uploadArtifact", combined)
        self.assertNotIn("refs/tags", combined)
        self.assertNotIn("handle." + "m" + "box", combined)
        self.assertIn("change-proposal.branch", combined)
        self.assertIn("handle.proposal_ref", combined)
        self.assertIn("no lists.sr.ht", combined)
        self.assertNotIn("git send-email", combined)

    def test_sourcehut_deliver_and_apply_use_full_proposal_ref_namespace(self) -> None:
        proposal = load_fixture("valid-change-proposal-sourcehut-v2.json")
        proposal_ref = proposal["handle"]["proposal_ref"]
        self.assertTrue(proposal_ref.startswith("refs/proposals/"))
        self.assertFalse(proposal["branch"].startswith("refs/"))

        deliver_invocation = mechanic_for_forge("sourcehut", "deliver-change-proposal")["default_invocation"]
        apply_invocation = mechanic_for_forge("sourcehut", "apply-approved-change")["default_invocation"]

        self.assertIn("$commit_resolved:$branch_ref", deliver_invocation)
        self.assertIn("refs/proposals/*", deliver_invocation)
        self.assertIn('git fetch "$ssh_remote" "$proposal_ref"', apply_invocation)
        self.assertNotIn("refs/heads/${proposal_ref}", deliver_invocation)
        self.assertNotIn('refs/heads/$proposal_ref', apply_invocation)

    def test_sourcehut_proposal_ref_pushes_and_fetches_end_to_end(self) -> None:
        proposal_ref = load_fixture("valid-change-proposal-sourcehut-v2.json")["handle"]["proposal_ref"]

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            remote = root / "remote.git"
            source = root / "source"
            consumer = root / "consumer"

            run_git(["init", "--bare", str(remote)], root)
            run_git(["init", str(source)], root)
            run_git(["config", "user.name", "Groundwork Tests"], source)
            run_git(["config", "user.email", "groundwork-tests@example.invalid"], source)
            (source / "proposal.txt").write_text("proposal\n", encoding="utf-8")
            run_git(["add", "proposal.txt"], source)
            run_git(["commit", "-m", "test: proposal"], source)
            commit = run_git(["rev-parse", "HEAD"], source)

            push_remote_ref(remote, proposal_ref, commit, source)

            run_git(["init", str(consumer)], root)
            run_git(["fetch", str(remote), proposal_ref], consumer)

            fetched_commit = run_git(["rev-parse", "FETCH_HEAD"], consumer)
            self.assertEqual(commit, fetched_commit)

    def test_sourcehut_apply_refuses_proposal_ref_at_unapproved_commit_before_pushing_target(self) -> None:
        apply = mechanic_for_forge("sourcehut", "apply-approved-change")
        proposal_ref = load_fixture("valid-change-proposal-sourcehut-v2.json")["handle"]["proposal_ref"]

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            remote = root / "remote.git"
            source = root / "source"
            consumer = root / "consumer"

            run_git(["init", "--bare", str(remote)], root)
            run_git(["init", str(source)], root)
            run_git(["config", "user.name", "Groundwork Tests"], source)
            run_git(["config", "user.email", "groundwork-tests@example.invalid"], source)
            (source / "base.txt").write_text("base\n", encoding="utf-8")
            run_git(["add", "base.txt"], source)
            run_git(["commit", "-m", "test: base"], source)
            base = run_git(["rev-parse", "HEAD"], source)

            (source / "proposal.txt").write_text("approved\n", encoding="utf-8")
            run_git(["add", "proposal.txt"], source)
            run_git(["commit", "-m", "test: approved proposal"], source)
            approved_commit = run_git(["rev-parse", "HEAD"], source)
            push_remote_ref(remote, proposal_ref, approved_commit, source)
            push_remote_ref(remote, "refs/heads/main", base, source)

            run_git(["init", str(consumer)], root)
            run_git(["config", "user.name", "Groundwork Tests"], consumer)
            run_git(["config", "user.email", "groundwork-tests@example.invalid"], consumer)
            run_git(["fetch", str(remote), "refs/heads/main"], consumer)
            run_git(["checkout", "-B", "main", "FETCH_HEAD"], consumer)
            run_git(["fetch", str(remote), proposal_ref], consumer)

            run_git(["checkout", "--detach", base], source)
            (source / "drift.txt").write_text("force-updated\n", encoding="utf-8")
            run_git(["add", "drift.txt"], source)
            run_git(["commit", "-m", "test: force-updated proposal"], source)
            drift_commit = run_git(["rev-parse", "HEAD"], source)
            push_remote_ref(remote, proposal_ref, drift_commit, source, force=True)

            result = self.run_mechanic_invocation(
                apply["default_invocation"],
                {
                    "ssh_remote": str(remote),
                    "proposal_ref": proposal_ref,
                    "approved_commit": approved_commit,
                    "target_ref": "refs/heads/dogfood/force-updated-proposal",
                },
                root,
                consumer,
            )

            target_ref = run_git(["ls-remote", str(remote), "refs/heads/dogfood/force-updated-proposal"], consumer)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("SourceHut proposal ref resolved to", result.stderr)
        self.assertEqual("", target_ref)

    def test_sourcehut_reflect_mechanic_uses_configured_tracker_endpoint(self) -> None:
        reflect = mechanic_for_forge("sourcehut", "reflect-disposition")
        invocation = reflect["default_invocation"]

        self.assertIn('"$todo_query_url"', invocation)
        self.assertNotIn("https://todo.sr.ht/query", invocation)

    def test_sourcehut_deliver_ignores_tail_matching_branch_when_detecting_existing_proposal_ref(self) -> None:
        deliver = mechanic_for_forge("sourcehut", "deliver-change-proposal")

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            remote = root / "remote.git"
            source = root / "source"
            proposal_ref = "refs/proposals/issue-376/1"
            branch = "issue-376/sourcehut-change-proposal-handle"
            tail_matching_branch = f"refs/heads/{proposal_ref}"

            run_git(["init", "--bare", str(remote)], root)
            run_git(["init", str(source)], root)
            run_git(["config", "user.name", "Groundwork Tests"], source)
            run_git(["config", "user.email", "groundwork-tests@example.invalid"], source)
            (source / "proposal.txt").write_text("proposal\n", encoding="utf-8")
            run_git(["add", "proposal.txt"], source)
            run_git(["commit", "-m", "test: proposal"], source)
            commit = run_git(["rev-parse", "HEAD"], source)
            run_git(["push", str(remote), f"{commit}:{tail_matching_branch}"], source)

            result = self.run_mechanic_invocation(
                deliver["default_invocation"],
                {
                    "branch": branch,
                    "commit": commit,
                    "proposal_ref": proposal_ref,
                    "ssh_remote": str(remote),
                },
                root,
                source,
            )

            proposal_commit = remote_ref_commit(remote, proposal_ref, source)
            branch_commit = remote_ref_commit(remote, f"refs/heads/{branch}", source)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(proposal_ref, result.stdout.strip())
        self.assertEqual(commit, proposal_commit)
        self.assertEqual(commit, branch_commit)

    def test_sourcehut_deliver_idempotent_proposal_ref_still_publishes_absent_or_stale_branch(self) -> None:
        deliver = mechanic_for_forge("sourcehut", "deliver-change-proposal")

        for initial_branch_state in ["absent", "stale"]:
            with self.subTest(initial_branch_state=initial_branch_state):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    remote = root / "remote.git"
                    source = root / "source"
                    proposal_ref = "refs/proposals/issue-376/1"
                    branch = "issue-376/sourcehut-change-proposal-handle"

                    run_git(["init", "--bare", str(remote)], root)
                    run_git(["init", str(source)], root)
                    run_git(["config", "user.name", "Groundwork Tests"], source)
                    run_git(["config", "user.email", "groundwork-tests@example.invalid"], source)
                    (source / "base.txt").write_text("base\n", encoding="utf-8")
                    run_git(["add", "base.txt"], source)
                    run_git(["commit", "-m", "test: base"], source)
                    base = run_git(["rev-parse", "HEAD"], source)
                    (source / "proposal.txt").write_text("proposal\n", encoding="utf-8")
                    run_git(["add", "proposal.txt"], source)
                    run_git(["commit", "-m", "test: proposal"], source)
                    commit = run_git(["rev-parse", "HEAD"], source)
                    push_refs = [f"{commit}:{proposal_ref}"]
                    if initial_branch_state == "stale":
                        push_refs.append(f"{base}:refs/heads/{branch}")
                    for refspec in push_refs:
                        commit_to_push, ref_to_push = refspec.split(":", maxsplit=1)
                        push_remote_ref(remote, ref_to_push, commit_to_push, source)

                    result = self.run_mechanic_invocation(
                        deliver["default_invocation"],
                        {
                            "branch": branch,
                            "commit": commit,
                            "proposal_ref": proposal_ref,
                            "ssh_remote": str(remote),
                        },
                        root,
                        source,
                    )

                    moved_ref = remote_ref_commit(remote, proposal_ref, source)
                    branch_ref = remote_ref_commit(remote, f"refs/heads/{branch}", source)

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(proposal_ref, result.stdout.strip())
                self.assertEqual(commit, moved_ref)
                self.assertEqual(commit, branch_ref)

    def test_sourcehut_deliver_same_commit_existing_pin_and_branch_is_no_op(self) -> None:
        deliver = mechanic_for_forge("sourcehut", "deliver-change-proposal")

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            remote = root / "remote.git"
            source = root / "source"
            proposal_ref = "refs/proposals/issue-376/1"
            branch = "issue-376/sourcehut-change-proposal-handle"

            run_git(["init", "--bare", str(remote)], root)
            run_git(["init", str(source)], root)
            run_git(["config", "user.name", "Groundwork Tests"], source)
            run_git(["config", "user.email", "groundwork-tests@example.invalid"], source)
            (source / "proposal.txt").write_text("proposal\n", encoding="utf-8")
            run_git(["add", "proposal.txt"], source)
            run_git(["commit", "-m", "test: proposal"], source)
            commit = run_git(["rev-parse", "HEAD"], source)
            push_remote_ref(remote, proposal_ref, commit, source)
            push_remote_ref(remote, f"refs/heads/{branch}", commit, source)

            result = self.run_mechanic_invocation(
                deliver["default_invocation"],
                {
                    "branch": branch,
                    "commit": commit,
                    "proposal_ref": proposal_ref,
                    "ssh_remote": str(remote),
                },
                root,
                source,
            )

            proposal_commit = remote_ref_commit(remote, proposal_ref, source)
            branch_commit = remote_ref_commit(remote, f"refs/heads/{branch}", source)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(proposal_ref, result.stdout.strip())
        self.assertEqual(commit, proposal_commit)
        self.assertEqual(commit, branch_commit)

    def test_sourcehut_deliver_succeeds_when_branch_descends_from_existing_pin(self) -> None:
        deliver = mechanic_for_forge("sourcehut", "deliver-change-proposal")

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            remote = root / "remote.git"
            source = root / "source"
            proposal_ref = "refs/proposals/issue-376/1"
            branch = "issue-376/sourcehut-change-proposal-handle"

            run_git(["init", "--bare", str(remote)], root)
            run_git(["init", str(source)], root)
            run_git(["config", "user.name", "Groundwork Tests"], source)
            run_git(["config", "user.email", "groundwork-tests@example.invalid"], source)
            (source / "proposal.txt").write_text("proposal\n", encoding="utf-8")
            run_git(["add", "proposal.txt"], source)
            run_git(["commit", "-m", "test: proposal"], source)
            commit = run_git(["rev-parse", "HEAD"], source)
            (source / "branch.txt").write_text("branch descendant\n", encoding="utf-8")
            run_git(["add", "branch.txt"], source)
            run_git(["commit", "-m", "test: branch descendant"], source)
            branch_descendant = run_git(["rev-parse", "HEAD"], source)
            push_remote_ref(remote, proposal_ref, commit, source)
            push_remote_ref(remote, f"refs/heads/{branch}", branch_descendant, source)

            result = self.run_mechanic_invocation(
                deliver["default_invocation"],
                {
                    "branch": branch,
                    "commit": commit,
                    "proposal_ref": proposal_ref,
                    "ssh_remote": str(remote),
                },
                root,
                source,
            )

            proposal_commit = remote_ref_commit(remote, proposal_ref, source)
            branch_commit = remote_ref_commit(remote, f"refs/heads/{branch}", source)

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(proposal_ref, result.stdout.strip())
        self.assertEqual(commit, proposal_commit)
        self.assertEqual(branch_descendant, branch_commit)

    def test_sourcehut_deliver_rejects_existing_descendant_proposal_ref_without_moving_it(self) -> None:
        deliver = mechanic_for_forge("sourcehut", "deliver-change-proposal")

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            remote = root / "remote.git"
            source = root / "source"
            proposal_ref = "refs/proposals/issue-376/1"
            branch = "issue-376/sourcehut-change-proposal-handle"

            run_git(["init", "--bare", str(remote)], root)
            run_git(["init", str(source)], root)
            run_git(["config", "user.name", "Groundwork Tests"], source)
            run_git(["config", "user.email", "groundwork-tests@example.invalid"], source)
            (source / "proposal.txt").write_text("proposal\n", encoding="utf-8")
            run_git(["add", "proposal.txt"], source)
            run_git(["commit", "-m", "test: proposal"], source)
            approved_commit = run_git(["rev-parse", "HEAD"], source)
            (source / "proposal.txt").write_text("descendant\n", encoding="utf-8")
            run_git(["add", "proposal.txt"], source)
            run_git(["commit", "-m", "test: descendant proposal"], source)
            descendant_commit = run_git(["rev-parse", "HEAD"], source)
            push_remote_ref(remote, proposal_ref, descendant_commit, source)

            result = self.run_mechanic_invocation(
                deliver["default_invocation"],
                {
                    "branch": branch,
                    "commit": approved_commit,
                    "proposal_ref": proposal_ref,
                    "ssh_remote": str(remote),
                },
                root,
                source,
            )

            unmoved_ref = remote_ref_commit(remote, proposal_ref, source)
            branch_ref = run_git(["ls-remote", str(remote), f"refs/heads/{branch}"], source)

        self.assertNotEqual(0, result.returncode)
        self.assertIn("already resolves to", result.stderr)
        self.assertEqual(descendant_commit, unmoved_ref)
        self.assertEqual("", branch_ref)

    def test_sourcehut_reflect_fails_when_either_todo_mutation_returns_graphql_errors_with_http_success(self) -> None:
        reflect = mechanic_for_forge("sourcehut", "reflect-disposition")

        cases = [
            (
                '{"errors":[{"message":"comment rejected"}],"data":{"submitComment":null}}',
                '{"data":{"updateTicketStatus":{"id":26}}}',
                "data.submitComment",
            ),
            (
                '{"data":{"submitComment":{"id":7}}}',
                '{"errors":[{"message":"status rejected"}],"data":{"updateTicketStatus":null}}',
                "data.updateTicketStatus",
            ),
        ]

        for comment_response, status_response, expected_stderr in cases:
            with self.subTest(expected_stderr=expected_stderr):
                with tempfile.TemporaryDirectory() as temporary_directory:
                    root = Path(temporary_directory)
                    bin_dir = root / "bin"
                    bin_dir.mkdir()
                    comment_payload = root / "comment.json"
                    status_payload = root / "status.json"
                    comment_payload.write_text('{"query":"mutation { submitComment { id } }"}', encoding="utf-8")
                    status_payload.write_text('{"query":"mutation { updateTicketStatus { id } }"}', encoding="utf-8")
                    (bin_dir / "curl").write_text(
                        f"""#!/bin/sh
case "$*" in
  *{comment_payload}*) printf '%s\\n' '{comment_response}' ;;
  *{status_payload}*) printf '%s\\n' '{status_response}' ;;
  *) exit 1 ;;
esac
""",
                        encoding="utf-8",
                    )
                    (bin_dir / "curl").chmod(0o755)

                    result = self.run_mechanic_invocation(
                        reflect["default_invocation"],
                        {
                            "token": "test-token",
                            "comment_payload_file": str(comment_payload),
                            "status_payload_file": str(status_payload),
                            "todo_query_url": "https://todo.example.invalid/query",
                        },
                        bin_dir,
                    )

                self.assertNotEqual(0, result.returncode)
                self.assertIn(expected_stderr, result.stderr)

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
