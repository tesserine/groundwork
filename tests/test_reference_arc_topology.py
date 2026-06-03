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

    def run_sourcehut_early_arc_response(self, operation: str, response_payload: dict) -> subprocess.CompletedProcess:
        mechanic = mechanic_for_forge("sourcehut", operation)
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            bin_dir = temp / "bin"
            bin_dir.mkdir()
            curl = bin_dir / "curl"
            curl.write_text('#!/bin/sh\nprintf "%s\\n" "$GROUNDWORK_TEST_SOURCEHUT_RESPONSE"\n', encoding="utf-8")
            curl.chmod(0o755)
            payload_file = temp / "payload.json"
            payload_file.write_text("{}", encoding="utf-8")

            return self.run_mechanic_invocation(
                mechanic["default_invocation"],
                {
                    "tracker_id": "4",
                    "ticket_id": "7",
                    "payload_file": str(payload_file),
                    "todo_query_url": "https://todo.weforge.build/query",
                    "token": "test-token",
                    "GROUNDWORK_TEST_SOURCEHUT_RESPONSE": json.dumps(response_payload),
                },
                bin_dir,
            )

    def sourcehut_early_arc_success_payload(self, operation: str, result: dict) -> dict:
        if operation == "read-ticket":
            return {"data": {"tracker": {"ticket": result}}}
        if operation == "create-ticket":
            return {"data": {"submitTicket": result}}
        return {"data": {"submitComment": result}}

    def sourcehut_early_arc_null_payload(self, operation: str) -> dict:
        if operation == "read-ticket":
            return {"data": {"tracker": {"ticket": None}}}
        if operation == "create-ticket":
            return {"data": {"submitTicket": None}}
        return {"data": {"submitComment": None}}

    def sourcehut_early_arc_absent_payload(self, operation: str) -> dict:
        if operation == "read-ticket":
            return {"data": {"tracker": {}}}
        return {"data": {}}

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

    def test_early_arc_mechanics_are_bound_once_per_forge_in_manifest_and_c3(self) -> None:
        operations = {
            "create-ticket",
            "read-ticket",
            "claim-work-unit",
            "record-progress",
        }
        manifest_mechanics = {entry["name"]: entry for entry in manifest()["mechanics"]}

        for forge_tag in {"github", "sourcehut"}:
            forge_mechanics = mechanics_for_forge(forge_tag)
            for operation in operations:
                with self.subTest(forge_tag=forge_tag, operation=operation):
                    self.assertIn(operation, manifest_mechanics)
                    self.assertIn(forge_tag, manifest_mechanics[operation]["forge_tags"])
                    self.assertEqual(1, sum(1 for mechanic in forge_mechanics if mechanic["name"] == operation))

    def test_reference_arc_mechanics_declare_deployment_resolved_parameters(self) -> None:
        expected = {
            ("github", "deliver-change-proposal"): {"repository": "repository"},
            ("github", "apply-approved-change"): {"repository": "repository"},
            ("github", "reflect-disposition"): {"repository": "repository"},
            ("github", "close-out"): {"repository": "repository"},
            ("sourcehut", "deliver-change-proposal"): {
                "repo_id": "repo_id",
                "ssh_remote": "ssh_remote",
                "git_query_url": "git_query_url",
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

    def test_early_arc_mechanics_declare_deployment_resolved_parameters(self) -> None:
        expected = {
            ("github", "create-ticket"): {"repository": "repository"},
            ("github", "read-ticket"): {"repository": "repository"},
            ("github", "claim-work-unit"): {"repository": "repository"},
            ("github", "record-progress"): {"repository": "repository"},
            ("sourcehut", "create-ticket"): {
                "tracker_id": "tracker_id",
                "todo_query_url": "todo_query_url",
            },
            ("sourcehut", "read-ticket"): {
                "tracker_id": "tracker_id",
                "todo_query_url": "todo_query_url",
            },
            ("sourcehut", "claim-work-unit"): {
                "tracker_id": "tracker_id",
                "todo_query_url": "todo_query_url",
            },
            ("sourcehut", "record-progress"): {
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

    def test_sourcehut_early_arc_mechanics_keep_token_secret(self) -> None:
        for operation in {"create-ticket", "read-ticket", "claim-work-unit", "record-progress"}:
            with self.subTest(operation=operation):
                mechanic = mechanic_for_forge("sourcehut", operation)
                token = {parameter["name"]: parameter for parameter in mechanic["parameters"]}["token"]

                self.assertTrue(token["secret"])
                self.assertNotIn("WEFORGE_OPERATOR_PAT", mechanic["default_invocation"])

    def test_sourcehut_early_arc_mechanics_reject_null_operation_results(self) -> None:
        for operation in {"create-ticket", "read-ticket", "claim-work-unit", "record-progress"}:
            with self.subTest(operation=operation):
                result = self.run_sourcehut_early_arc_response(
                    operation,
                    self.sourcehut_early_arc_null_payload(operation),
                )

                self.assertNotEqual(0, result.returncode)
                self.assertIn("omitted data", result.stderr)

    def test_sourcehut_early_arc_mechanics_reject_absent_operation_results(self) -> None:
        for operation in {"create-ticket", "read-ticket", "claim-work-unit", "record-progress"}:
            with self.subTest(operation=operation):
                result = self.run_sourcehut_early_arc_response(
                    operation,
                    self.sourcehut_early_arc_absent_payload(operation),
                )

                self.assertNotEqual(0, result.returncode)
                self.assertIn("omitted data", result.stderr)

    def test_sourcehut_early_arc_mechanics_emit_well_formed_operation_results(self) -> None:
        expected = {
            "create-ticket": {"id": 42, "ref": "~operator/weforge#42"},
            "read-ticket": {"id": 7, "subject": "ticket"},
            "claim-work-unit": {"id": 1001},
            "record-progress": {"id": 1002},
        }

        for operation, operation_result in expected.items():
            with self.subTest(operation=operation):
                result = self.run_sourcehut_early_arc_response(
                    operation,
                    self.sourcehut_early_arc_success_payload(operation, operation_result),
                )

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual(operation_result, json.loads(result.stdout))

    def test_sourcehut_apply_mechanic_uses_proposal_ref_and_tree_equality_not_commit_identity(self) -> None:
        apply = mechanic_for_forge("sourcehut", "apply-approved-change")
        invocation = apply["default_invocation"]

        self.assertIn('git fetch "$ssh_remote" "refs/heads/$proposal_ref"', invocation)
        self.assertIn("git rev-parse FETCH_HEAD", invocation)
        self.assertIn('expected_tree=$(git rev-parse "${approved_commit}^{tree}")', invocation)
        self.assertIn('git am --3way "$mbox_file"', invocation)
        self.assertLess(invocation.index("git rev-parse FETCH_HEAD"), invocation.index('git am --3way "$mbox_file"'))
        self.assertIn("git rev-parse HEAD^{tree}", invocation)
        self.assertIn("resolved by work_unit and against_version", apply["purpose"])
        self.assertNotIn('git rev-parse HEAD)" = "$approved_commit', invocation)
        self.assertNotIn("GIT_COMMITTER_DATE", invocation)

    def test_sourcehut_deliver_mechanic_produces_mbox_and_proposal_ref_without_lists(self) -> None:
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

        self.assertIn('git format-patch --stdout "${base}..${commit}"', invocation)
        self.assertIn('git push "$ssh_remote" "${commit}:refs/heads/${proposal_ref}"', invocation)
        self.assertIn("artifact_tag", parameters)
        self.assertIn('git tag --force "$artifact_tag" "$commit"', invocation)
        self.assertIn("refs/tags/${artifact_tag}:refs/tags/${artifact_tag}", invocation)
        self.assertIn('refs/tags/${artifact_tag}', invocation)
        self.assertIn("uploadArtifact", invocation)
        self.assertLess(invocation.index("refs/tags/${artifact_tag}:refs/tags/${artifact_tag}"), invocation.index("uploadArtifact"))
        self.assertNotIn('"revspec":"${proposal_ref}"', invocation)
        self.assertNotIn('"revspec":"refs/heads/', combined)
        self.assertIn("change-proposal.branch", combined)
        self.assertIn("no lists.sr.ht", combined)
        self.assertNotIn("git send-email", combined)

    def test_sourcehut_deliver_and_apply_qualify_bare_branch_proposal_ref(self) -> None:
        proposal = load_fixture("valid-change-proposal-sourcehut-v2.json")
        proposal_ref = proposal["branch"]
        self.assertFalse(proposal_ref.startswith("refs/"))

        deliver_invocation = mechanic_for_forge("sourcehut", "deliver-change-proposal")["default_invocation"]
        apply_invocation = mechanic_for_forge("sourcehut", "apply-approved-change")["default_invocation"]

        self.assertIn("${commit}:refs/heads/${proposal_ref}", deliver_invocation)
        self.assertIn('git fetch "$ssh_remote" "refs/heads/$proposal_ref"', apply_invocation)
        self.assertNotIn("${commit}:${proposal_ref}", deliver_invocation)
        self.assertNotIn('git fetch "$ssh_remote" "$proposal_ref"', apply_invocation)

    def test_sourcehut_bare_branch_proposal_ref_pushes_and_fetches_end_to_end(self) -> None:
        proposal_ref = load_fixture("valid-change-proposal-sourcehut-v2.json")["branch"]

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

            deliver_destination = f"{commit}:refs/heads/{proposal_ref}"
            run_git(["push", str(remote), deliver_destination], source)

            run_git(["init", str(consumer)], root)
            run_git(["fetch", str(remote), f"refs/heads/{proposal_ref}"], consumer)

            fetched_commit = run_git(["rev-parse", "FETCH_HEAD"], consumer)
            self.assertEqual(commit, fetched_commit)

    def test_sourcehut_apply_refuses_force_updated_proposal_ref_before_applying_mbox(self) -> None:
        apply = mechanic_for_forge("sourcehut", "apply-approved-change")
        proposal_ref = load_fixture("valid-change-proposal-sourcehut-v2.json")["branch"]

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            remote = root / "remote.git"
            source = root / "source"
            consumer = root / "consumer"
            mbox_file = root / "approved.mbox"

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
            mbox_file.write_text(run_git(["format-patch", "--stdout", f"{base}..{approved_commit}"], source), encoding="utf-8")
            run_git(["push", str(remote), f"{approved_commit}:refs/heads/{proposal_ref}", f"{base}:refs/heads/main"], source)

            run_git(["init", str(consumer)], root)
            run_git(["config", "user.name", "Groundwork Tests"], consumer)
            run_git(["config", "user.email", "groundwork-tests@example.invalid"], consumer)
            run_git(["fetch", str(remote), "refs/heads/main"], consumer)
            run_git(["checkout", "-B", "main", "FETCH_HEAD"], consumer)
            run_git(["fetch", str(remote), f"refs/heads/{proposal_ref}"], consumer)

            run_git(["checkout", "--detach", base], source)
            (source / "drift.txt").write_text("force-updated\n", encoding="utf-8")
            run_git(["add", "drift.txt"], source)
            run_git(["commit", "-m", "test: force-updated proposal"], source)
            drift_commit = run_git(["rev-parse", "HEAD"], source)
            run_git(["push", "--force", str(remote), f"{drift_commit}:refs/heads/{proposal_ref}"], source)

            result = self.run_mechanic_invocation(
                apply["default_invocation"],
                {
                    "ssh_remote": str(remote),
                    "proposal_ref": proposal_ref,
                    "approved_commit": approved_commit,
                    "mbox_file": str(mbox_file),
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

    def test_sourcehut_deliver_fails_when_upload_artifact_returns_graphql_errors_with_http_success(self) -> None:
        deliver = mechanic_for_forge("sourcehut", "deliver-change-proposal")

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            (bin_dir / "git").write_text(
                """#!/bin/sh
case "$1" in
  format-patch) printf 'patch body\\n' ;;
  tag|push) exit 0 ;;
  *) exit 1 ;;
esac
""",
                encoding="utf-8",
            )
            (bin_dir / "curl").write_text(
                """#!/bin/sh
printf '%s\\n' '{"errors":[{"message":"artifact already exists"}],"data":{"uploadArtifact":null}}'
""",
                encoding="utf-8",
            )
            (bin_dir / "git").chmod(0o755)
            (bin_dir / "curl").chmod(0o755)

            result = self.run_mechanic_invocation(
                deliver["default_invocation"],
                {
                    "base": "main",
                    "commit": "HEAD",
                    "mbox_file": str(root / "proposal.mbox"),
                    "repo_id": "42",
                    "ssh_remote": "git@example.invalid:repo",
                    "proposal_ref": "issue-26/proposal",
                    "artifact_tag": "proposals/issue-26-v1",
                    "mbox_filename": "issue-26-v1.mbox",
                    "git_query_url": "https://git.example.invalid/query",
                    "token": "test-token",
                },
                bin_dir,
            )

        self.assertNotEqual(0, result.returncode)
        self.assertIn("data.uploadArtifact.id/filename", result.stderr)

    def test_sourcehut_deliver_outputs_durable_mbox_reference_not_artifact_url(self) -> None:
        deliver = mechanic_for_forge("sourcehut", "deliver-change-proposal")
        invocation = deliver["default_invocation"]

        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            bin_dir = root / "bin"
            bin_dir.mkdir()
            (bin_dir / "git").write_text(
                """#!/bin/sh
case "$1" in
  format-patch) printf 'patch body\\n' ;;
  tag|push) exit 0 ;;
  *) exit 1 ;;
esac
""",
                encoding="utf-8",
            )
            (bin_dir / "curl").write_text(
                """#!/bin/sh
printf '%s\\n' '{"data":{"uploadArtifact":{"id":987,"filename":"issue-26-v1.mbox","checksum":"sha256:abc","size":123,"url":"https://git.sr.ht/~tesserine/groundwork/blob/proposals/issue-26-v1/issue-26-v1.mbox"}}}'
""",
                encoding="utf-8",
            )
            (bin_dir / "git").chmod(0o755)
            (bin_dir / "curl").chmod(0o755)

            result = self.run_mechanic_invocation(
                invocation,
                {
                    "base": "main",
                    "commit": "HEAD",
                    "mbox_file": str(root / "proposal.mbox"),
                    "repo_id": "42",
                    "ssh_remote": "git@example.invalid:repo",
                    "proposal_ref": "issue-26/proposal",
                    "artifact_tag": "proposals/issue-26-v1",
                    "mbox_filename": "issue-26-v1.mbox",
                    "git_query_url": "https://git.example.invalid/query",
                    "token": "test-token",
                },
                bin_dir,
            )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(
            "sourcehut-artifact://repo/42/refs/tags/proposals/issue-26-v1/issue-26-v1.mbox?id=987",
            result.stdout.strip(),
        )
        self.assertNotIn("https://", result.stdout)

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
