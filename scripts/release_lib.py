from __future__ import annotations

import argparse
import datetime as _dt
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path


VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-rc\.[1-9][0-9]*)?$")
TAG_RE = re.compile(r"^v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-rc\.[1-9][0-9]*)?$")
RELEASE_HEADING_RE = re.compile(
    r"^## \[(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(-rc\.[1-9][0-9]*)?\] — [0-9]{4}-[0-9]{2}-[0-9]{2}$"
)


class ReleaseError(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    stdout: str
    stderr: str


@dataclass(frozen=True)
class WorkflowCommand:
    line_number: int
    step_index: int
    text: str


def die(message: str) -> None:
    raise ReleaseError(message)


def repo_root_from_script(script_file: str) -> Path:
    return Path(script_file).resolve().parents[1]


def version_from_tag(tag: str) -> str:
    match = TAG_RE.fullmatch(tag)
    if not match:
        die(f"release tag must look like vX.Y.Z or vX.Y.Z-rc.N per ADR-0012: {tag}")
    return tag[1:]


def check_version_shape(version: str) -> None:
    if not VERSION_RE.fullmatch(version):
        die(f"version must look like X.Y.Z or X.Y.Z-rc.N per ADR-0012: {version}")


def read_manifest(root: Path) -> dict:
    manifest = root / "manifest.toml"
    if not manifest.is_file():
        die("manifest.toml not found")
    try:
        return tomllib.loads(manifest.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as error:
        die(f"manifest.toml is invalid TOML: {error}")


def manifest_version(root: Path) -> str:
    manifest = read_manifest(root)
    version = manifest.get("version")
    if not isinstance(version, str) or not version:
        die("manifest.toml top-level version not found")
    check_version_shape(version)
    return version


def changelog_path(root: Path) -> Path:
    path = root / "CHANGELOG.md"
    if not path.is_file():
        die("CHANGELOG.md not found")
    return path


def release_heading_for(version: str) -> str | None:
    prefix = f"## [{version}] — "
    return prefix


def check_changelog_structure(root: Path) -> None:
    changelog = changelog_path(root)
    lines = changelog.read_text(encoding="utf-8").splitlines()
    unreleased_count = sum(1 for line in lines if line == "## [Unreleased]")
    if unreleased_count != 1:
        die("CHANGELOG.md must contain exactly one ## [Unreleased] heading")

    seen_release = False
    seen_versions: set[str] = set()
    for line in lines:
        if not line.startswith("## "):
            continue
        if line == "## [Unreleased]":
            if seen_release:
                die("CHANGELOG.md places ## [Unreleased] after a release heading")
            continue
        if not RELEASE_HEADING_RE.fullmatch(line):
            die(f"CHANGELOG.md release heading is malformed: {line}")
        version = line[len("## [") : line.index("]")]
        if version in seen_versions:
            die(f"CHANGELOG.md has duplicate release heading for [{version}]")
        seen_versions.add(version)
        seen_release = True


def require_release_heading(root: Path, version: str) -> None:
    prefix = release_heading_for(version)
    for line in changelog_path(root).read_text(encoding="utf-8").splitlines():
        if prefix and line.startswith(prefix):
            date = line[len(prefix) :]
            if re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date):
                return
    die(f"CHANGELOG.md has no release heading for [{version}]")


def require_unreleased_empty(root: Path) -> None:
    lines = changelog_path(root).read_text(encoding="utf-8").splitlines()
    start = lines.index("## [Unreleased]") + 1
    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break

    for line in lines[start:end]:
        if line == "" or line.startswith("### "):
            continue
        die("Unreleased contains entries; roll them into the release section before tagging")


def emit_notes(root: Path, version: str) -> str:
    prefix = release_heading_for(version)
    lines = changelog_path(root).read_text(encoding="utf-8").splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if prefix and line.startswith(prefix):
            start = index + 1
            break
    if start is None:
        die(f"CHANGELOG.md has no release heading for [{version}]")

    end = len(lines)
    for index in range(start, len(lines)):
        if lines[index].startswith("## "):
            end = index
            break

    section = lines[start:end]
    while section and section[0] == "":
        section.pop(0)
    while section and section[-1] == "":
        section.pop()
    return "\n".join(section) + ("\n" if section else "")


def check_methodology_integrity(root: Path) -> None:
    manifest = read_manifest(root)
    artifact_types = manifest.get("artifact_types")
    protocols = manifest.get("protocols")
    if not isinstance(artifact_types, list):
        die("manifest.toml artifact_types must be an array")
    if not isinstance(protocols, list):
        die("manifest.toml protocols must be an array")

    artifacts: set[str] = set()
    for entry in artifact_types:
        name = entry.get("name") if isinstance(entry, dict) else None
        if not isinstance(name, str) or not name:
            die("manifest.toml artifact_types entries must declare name")
        artifacts.add(name)
        schema = root / "schemas" / f"{name}.schema.json"
        if not schema.is_file():
            die(f"artifact type {name} has no schema at schemas/{name}.schema.json")
        try:
            json.loads(schema.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            die(f"schema schemas/{name}.schema.json is not valid JSON: {error}")

    for entry in protocols:
        if not isinstance(entry, dict):
            die("manifest.toml protocols entries must be tables")
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            die("manifest.toml protocols entries must declare name")
        protocol_file = root / "protocols" / name / "PROTOCOL.md"
        if not protocol_file.is_file():
            die(f"protocol {name} has no file at protocols/{name}/PROTOCOL.md")
        for field in ["requires", "accepts", "produces", "may_produce"]:
            values = entry.get(field, [])
            if not isinstance(values, list) or not all(isinstance(value, str) for value in values):
                die(f"protocol {name} field {field} must be an array of artifact names")
            for artifact in values:
                if artifact not in artifacts:
                    die(f"protocol {name} references undeclared artifact {artifact} in {field}")
        trigger = entry.get("trigger")
        if isinstance(trigger, dict) and trigger.get("type") == "on_artifact":
            artifact = trigger.get("name")
            if artifact not in artifacts:
                die(f"protocol {name} trigger references undeclared artifact {artifact}")

    skills_dir = root / "skills"
    if skills_dir.is_dir():
        for skill in sorted(path for path in skills_dir.iterdir() if path.is_dir()):
            if not (skill / "SKILL.md").is_file():
                die(f"skill {skill.name} has no SKILL.md")


def check_release_surface_files(root: Path) -> None:
    for relative in [
        "RELEASING.md",
        "scripts/release-check",
        "scripts/release-cut",
        ".github/workflows/release.yml",
        ".github/workflows/release-metadata.yml",
    ]:
        if not (root / relative).is_file():
            die(f"{relative} not found")


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _trim(value: str) -> str:
    return value.strip()


def _unquote(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _strip_shell_comment(value: str) -> str:
    return re.sub(r"(^|\s)#.*", "", value)


def _starts_workflow_step(stripped: str) -> bool:
    return re.match(r"^-\s*(?:name|run|uses):(?:\s|$)", stripped) is not None


def _emit_workflow_command(commands: list[WorkflowCommand], line_number: int, step_index: int, command: str) -> None:
    command = _trim(_strip_shell_comment(command))
    if command:
        commands.append(WorkflowCommand(line_number, step_index, command))


def workflow_executable_lines(workflow: Path) -> list[WorkflowCommand]:
    commands: list[WorkflowCommand] = []
    in_run_block = False
    run_indent = 0
    current_step_index = -1

    for line_number, raw_line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.rstrip("\r")
        indent = _indent_of(line)
        stripped = _trim(line)

        if in_run_block:
            if stripped and indent <= run_indent:
                in_run_block = False
            else:
                _emit_workflow_command(commands, line_number, current_step_index, line)
                continue

        if stripped.startswith("#"):
            continue
        if _starts_workflow_step(stripped):
            current_step_index += 1

        match = re.match(r"^\s*(?:-\s*)?run:\s*(.*)$", line)
        if not match:
            continue

        value = _trim(match.group(1))
        if value.startswith("|") or value.startswith(">"):
            in_run_block = True
            run_indent = indent
            continue

        _emit_workflow_command(commands, line_number, current_step_index, _unquote(value))

    return commands


def workflow_uses_lines(workflow: Path) -> list[WorkflowCommand]:
    commands: list[WorkflowCommand] = []
    current_step_index = -1
    for line_number, raw_line in enumerate(workflow.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.rstrip("\r")
        stripped = _trim(line)
        if stripped.startswith("#"):
            continue
        if _starts_workflow_step(stripped):
            current_step_index += 1

        match = re.match(r"^\s*(?:-\s*)?uses:\s*(.*)$", line)
        if not match:
            continue

        value = _trim(re.sub(r"\s+#.*", "", match.group(1)))
        if value:
            commands.append(WorkflowCommand(line_number, current_step_index, _unquote(value)))
    return commands


def _first_line(commands: list[WorkflowCommand], predicate) -> int | None:
    for command in commands:
        if predicate(command.text):
            return command.line_number
    return None


def _event_identity_lines(commands: list[WorkflowCommand]) -> tuple[int | None, int | None, bool]:
    assignment_command: WorkflowCommand | None = None
    saw_split_identity = False
    for command in commands:
        if command.text == 'restored_commit=$(git rev-parse "refs/tags/$GITHUB_REF_NAME^{commit}")':
            assignment_command = command
            continue
        if assignment_command is not None:
            if (
                command.step_index == assignment_command.step_index
                and command.text == 'if [ "$restored_commit" != "$GITHUB_SHA" ]; then'
            ):
                return assignment_command.line_number, command.line_number, False
            if command.step_index == assignment_command.step_index:
                assignment_command = None
                continue
            saw_split_identity = True
            assignment_command = None
    return None, None, saw_split_identity


def _is_local_script_invocation(text: str) -> bool:
    if text.startswith("./scripts/"):
        return True
    for wrapper in ("bash", "sh"):
        if text.startswith(f"{wrapper} ./scripts/"):
            return True
    return False


def check_release_workflow_surface(root: Path) -> None:
    workflow = root / ".github" / "workflows" / "release.yml"
    if not workflow.is_file():
        die(".github/workflows/release.yml not found")

    # This line scanner validates the current single-job release workflow shape;
    # multi-job trust ordering is deferred to tesserine/commons#36.
    executable_lines = workflow_executable_lines(workflow)
    uses_lines = workflow_uses_lines(workflow)

    checkout_line = _first_line(uses_lines, lambda text: re.match(r"^actions/checkout(@|$)", text) is not None)
    tag_ref_restore_line = _first_line(executable_lines, lambda text: text == "git fetch --tags --force origin")
    event_assignment_line, event_if_line, split_event_identity = _event_identity_lines(executable_lines)
    annotated_tag_line = _first_line(
        executable_lines,
        lambda text: text == 'test "$(git cat-file -t "refs/tags/$GITHUB_REF_NAME")" = tag',
    )
    main_ancestry_line = _first_line(
        executable_lines,
        lambda text: text == 'git merge-base --is-ancestor "$tag_commit" refs/remotes/origin/main',
    )
    repository_code_line = _first_line(
        executable_lines,
        _is_local_script_invocation,
    )

    if tag_ref_restore_line is None:
        die(".github/workflows/release.yml must restore annotated tag refs before checking tag type")
    if checkout_line is None or checkout_line >= tag_ref_restore_line:
        die(".github/workflows/release.yml must restore annotated tag refs after checkout and before checking tag type")
    if annotated_tag_line is not None and tag_ref_restore_line >= annotated_tag_line:
        die(".github/workflows/release.yml must restore annotated tag refs before checking tag type")

    if event_assignment_line is None or event_if_line is None:
        if split_event_identity:
            die(
                ".github/workflows/release.yml event identity commands must run in one workflow step; "
                "GitHub Actions shell-state isolation prevents variables from crossing steps"
            )
        die(".github/workflows/release.yml must verify the restored tag matches the triggering event before checking tag type")
    if tag_ref_restore_line >= event_assignment_line or tag_ref_restore_line >= event_if_line:
        die(".github/workflows/release.yml must capture the restored tag target after restoring annotated tag refs")
    if annotated_tag_line is not None and (
        event_assignment_line >= annotated_tag_line or event_if_line >= annotated_tag_line
    ):
        die(".github/workflows/release.yml must compare the restored tag target before checking tag type")

    if (
        annotated_tag_line is None
        or main_ancestry_line is None
        or repository_code_line is None
        or annotated_tag_line >= repository_code_line
        or main_ancestry_line >= repository_code_line
    ):
        die(".github/workflows/release.yml must establish tag trust before running repository code")


def run_metadata(root: Path) -> None:
    manifest_version(root)
    check_changelog_structure(root)
    check_methodology_integrity(root)
    check_release_surface_files(root)
    check_release_workflow_surface(root)


def run_release(root: Path, tag: str) -> None:
    version = version_from_tag(tag)
    run_metadata(root)
    current = manifest_version(root)
    if current != version:
        die(f"manifest version {current} does not match tag version {version}")
    require_release_heading(root, version)
    require_unreleased_empty(root)


def replace_manifest_version(root: Path, version: str) -> None:
    manifest = root / "manifest.toml"
    text = manifest.read_text(encoding="utf-8")
    pattern = re.compile(r'(?m)^version\s*=\s*"[^"]+"\s*$')
    replacement = f'version = "{version}"'
    if pattern.search(text):
        text = pattern.sub(replacement, text, count=1)
    else:
        name_match = re.search(r'(?m)^name\s*=\s*"[^"]+"\s*$', text)
        if not name_match:
            die("manifest.toml must declare name before release-cut can insert version")
        insert_at = name_match.end()
        text = text[:insert_at] + "\n" + replacement + text[insert_at:]
    manifest.write_text(text, encoding="utf-8")


def roll_changelog(root: Path, version: str) -> None:
    changelog = changelog_path(root)
    lines = changelog.read_text(encoding="utf-8").splitlines()
    try:
        unreleased = lines.index("## [Unreleased]")
    except ValueError:
        die("CHANGELOG.md must contain ## [Unreleased]")

    next_heading = len(lines)
    for index in range(unreleased + 1, len(lines)):
        if lines[index].startswith("## "):
            next_heading = index
            break

    unreleased_body = lines[unreleased + 1 : next_heading]
    while unreleased_body and unreleased_body[0] == "":
        unreleased_body.pop(0)
    while unreleased_body and unreleased_body[-1] == "":
        unreleased_body.pop()

    today = _dt.date.today().isoformat()
    release_section = [f"## [{version}] — {today}"]
    if unreleased_body:
        release_section.extend(["", *unreleased_body])

    new_lines = lines[: unreleased + 1] + [""] + release_section
    if next_heading < len(lines):
        new_lines.extend(["", *lines[next_heading:]])
    changelog.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")


def git(root: Path, *args: str, check: bool = True) -> CommandResult:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if check and result.returncode != 0:
        die(f"git {' '.join(args)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return CommandResult(result.stdout, result.stderr)


def require_clean_main(root: Path) -> None:
    branch = git(root, "branch", "--show-current").stdout.strip()
    if branch != "main":
        die(f"release-cut must run on main, not {branch or 'detached HEAD'}")
    status = git(root, "status", "--short").stdout.strip()
    if status:
        die("release-cut requires a clean working tree")
    git(root, "fetch", "origin", "main")
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    origin_main = git(root, "rev-parse", "FETCH_HEAD").stdout.strip()
    if head == origin_main:
        return

    behind, ahead = (
        int(count)
        for count in git(root, "rev-list", "--left-right", "--count", "FETCH_HEAD...HEAD").stdout.split()
    )

    def commits(count: int) -> str:
        return f"{count} commit" if count == 1 else f"{count} commits"

    if ahead and behind:
        divergence = f"main has diverged from origin/main ({commits(ahead)} ahead, {commits(behind)} behind)"
    elif ahead:
        divergence = f"main is {commits(ahead)} ahead of origin/main"
    elif behind:
        divergence = f"main is {commits(behind)} behind origin/main"
    else:
        divergence = "main does not match origin/main"
    die(f"release-cut requires main to equal origin/main; {divergence}")


def local_tag_exists(root: Path, tag: str) -> bool:
    result = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"],
        cwd=root,
    )
    return result.returncode == 0


def release_cut(root: Path, tag: str) -> None:
    version = version_from_tag(tag)
    require_clean_main(root)
    if local_tag_exists(root, tag):
        die(f"local tag {tag} already exists")
    run_metadata(root)

    before = git(root, "rev-parse", "HEAD").stdout.strip()
    created_tag = False
    try:
        replace_manifest_version(root, version)
        roll_changelog(root, version)
        run_release(root, tag)
        git(root, "add", "manifest.toml", "CHANGELOG.md")
        git(root, "commit", "-m", f"chore(release): {version}", "-m", f"Release {tag}.")
        git(root, "tag", "-a", tag, "-m", f"groundwork {tag}")
        created_tag = True
        push = subprocess.run(
            ["git", "push", "--atomic", "origin", "main", tag],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if push.returncode != 0:
            raise ReleaseError(f"atomic push failed: {push.stderr.strip() or push.stdout.strip()}")
    except Exception:
        if created_tag:
            subprocess.run(["git", "tag", "-d", tag], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "reset", "--hard", before], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        raise


def release_check_main(root: Path, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="release-check")
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("metadata")
    notes = subcommands.add_parser("notes")
    notes.add_argument("tag")
    release = subcommands.add_parser("release")
    release.add_argument("tag")
    args = parser.parse_args(argv)

    if args.command == "metadata":
        run_metadata(root)
    elif args.command == "notes":
        sys.stdout.write(emit_notes(root, version_from_tag(args.tag)))
    elif args.command == "release":
        run_release(root, args.tag)
    return 0


def release_cut_main(root: Path, argv: list[str]) -> int:
    parser = argparse.ArgumentParser(prog="release-cut")
    parser.add_argument("tag")
    args = parser.parse_args(argv)
    release_cut(root, args.tag)
    return 0
