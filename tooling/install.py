"""Methodology self-install for runtime-driven deployments.

Serves deployments where a protocol runtime executes the methodology
through the methodology interface contract: protocol instruction content
is the contract channel's to deliver, so this installer carries none of
it. It owns exactly what that channel does not deliver:

- **Skills, verbatim** — every ``skills/<name>/`` carrying a ``SKILL.md``
  installs unmodified into the agent harnesses' native skill-discovery
  locations. No projection, no transformation of any shipped file.
- **The methodology runtime** — ``~/.groundwork`` with ``manifest.toml``,
  every manifest-declared artifact schema, and every manifest-declared
  protocol instruction file.
- **The principles corpus** — an operator input recorded into the
  deployment-owned config (ADR-0005) and materialized at
  ``~/.groundwork/principles`` through the existing resolution layer.

Deliberately stdlib-only, like the rest of ``tooling/``: the install path
runs in deployments that carry no third-party packages.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tooling.corpus_resolution import CorpusResolutionError, check_resolvable, materialize
from tooling.principles_config import (
    PrinciplesConfigError,
    PrinciplesCorpusConfig,
    default_config_path,
    load_principles_config,
    parse_principles_config,
    resolved_corpus_path,
    write_principles_config,
)

PROGRAM = "install"

# Ownership identity. Deliberately distinct from the legacy interactive
# installer (`.groundwork-install`, `managed-by=groundwork-install`) so
# neither installer can mistake the other's entries for its own.
MARKER_NAME = ".groundwork-managed"
MANAGED_BY = "groundwork scripts/install"
STATE_FILE_NAME = "install.tsv"

# The legacy interactive installer's marker. Entries it placed are never
# adopted — the operator is directed to its own uninstall instead.
LEGACY_MARKER_NAME = ".groundwork-install"


class InstallError(Exception):
    """A named, loud installation failure."""


@dataclass(frozen=True)
class Options:
    mode: str
    source: Path
    home: Path
    state_dir: Path
    config_path: Path
    corpus_input: PrinciplesCorpusConfig | None


def parse_args(argv: list[str], environment: dict[str, str]) -> Options:
    mode = "install"
    arguments = list(argv)
    if arguments and arguments[0] in ("install", "uninstall"):
        mode = arguments.pop(0)

    source = Path(".")
    home = Path(environment["HOME"]) if environment.get("HOME") else None
    home_from_argument = False
    state_dir: Path | None = None
    corpus_flags: dict[str, str | bool] = {}
    index = 0
    while index < len(arguments):
        flag = arguments[index]
        if flag.startswith("--") and flag != "--corpus-embedded" and index + 1 >= len(arguments):
            raise InstallError(f"{flag} requires a value")
        if flag == "--source":
            source = Path(arguments[index + 1])
            index += 2
        elif flag == "--home":
            home = Path(arguments[index + 1])
            home_from_argument = True
            index += 2
        elif flag == "--state-dir":
            state_dir = Path(arguments[index + 1])
            index += 2
        elif flag == "--corpus-git":
            corpus_flags["git"] = arguments[index + 1]
            index += 2
        elif flag == "--corpus-ref":
            corpus_flags["ref"] = arguments[index + 1]
            index += 2
        elif flag == "--corpus-path":
            corpus_flags["path"] = arguments[index + 1]
            index += 2
        elif flag == "--corpus-embedded":
            corpus_flags["embedded"] = True
            index += 1
        else:
            raise InstallError(f"unknown argument: {flag}")
    if home is None:
        raise InstallError("HOME is not set; pass --home")
    corpus_input = parse_corpus_input(corpus_flags)
    home = home.resolve()
    if state_dir is None:
        xdg_state_home = None if home_from_argument else environment.get("XDG_STATE_HOME")
        state_root = Path(xdg_state_home) if xdg_state_home else home / ".local" / "state"
        state_dir = state_root / "groundwork"
    config_environment = dict(environment)
    if home_from_argument:
        config_environment.pop("XDG_CONFIG_HOME", None)
    config_environment["HOME"] = str(home)
    return Options(
        mode=mode,
        source=source.resolve(),
        home=home,
        state_dir=state_dir.resolve(),
        config_path=default_config_path(config_environment),
        corpus_input=corpus_input,
    )


def parse_corpus_input(corpus_flags: dict[str, str | bool]) -> PrinciplesCorpusConfig | None:
    """Operator corpus input as a validated config — ADR-0005's discriminated
    union expressed as mutually exclusive flags."""
    sources = [key for key in ("git", "path", "embedded") if key in corpus_flags]
    if len(sources) > 1:
        raise InstallError(
            "--corpus-git, --corpus-path, and --corpus-embedded are mutually exclusive"
        )
    if "ref" in corpus_flags and "git" not in corpus_flags:
        raise InstallError("--corpus-ref requires --corpus-git")
    if not sources:
        return None
    corpus: dict[str, str] = {"source": sources[0]}
    if "git" in corpus_flags:
        corpus["url"] = str(corpus_flags["git"])
        if "ref" in corpus_flags:
            corpus["ref"] = str(corpus_flags["ref"])
    elif "path" in corpus_flags:
        corpus["path"] = str(corpus_flags["path"])
    return parse_principles_config({"corpus": corpus})


def git(source: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(source), *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise InstallError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def source_sha(source: Path) -> str:
    return git(source, "rev-parse", "HEAD").strip()


def validate_source(source: Path) -> str:
    """The source must be a clean checkout root carrying skills; content
    derives from HEAD, so a dirty tree would install bytes the operator is
    not looking at. Returns the commit the installation derives from."""
    if not source.is_dir():
        raise InstallError(f"source not found: {source}")
    toplevel = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
    )
    if toplevel.returncode != 0 or Path(toplevel.stdout.strip()).resolve() != source:
        raise InstallError(f"source must be the groundwork checkout root: {source}")
    if git(source, "status", "--porcelain").strip():
        raise InstallError("source checkout is dirty; install from a clean checkout")
    sha = source_sha(source)
    probe = subprocess.run(
        ["git", "-C", str(source), "cat-file", "-e", f"{sha}:skills"],
        capture_output=True,
    )
    if probe.returncode != 0:
        raise InstallError(f"source has no skills directory at {sha}")
    return sha


def enumerate_skills(source: Path, sha: str) -> list[str]:
    """Skill names at the commit — enumerated from the tree, never hardcoded."""
    names = []
    for name in sorted(git(source, "ls-tree", "-d", "--name-only", f"{sha}:skills").splitlines()):
        probe = subprocess.run(
            ["git", "-C", str(source), "cat-file", "-e", f"{sha}:skills/{name}/SKILL.md"],
            capture_output=True,
        )
        if probe.returncode == 0:
            names.append(name)
    return names


def target_roots(home: Path) -> list[Path]:
    return [home / ".claude" / "skills", home / ".agents" / "skills"]


def extract_tree(source: Path, sha: str, tree_path: str, destination: Path) -> None:
    """Materialize ``<sha>:<tree_path>`` verbatim into ``destination``."""
    archive = subprocess.run(
        ["git", "-C", str(source), "archive", "--format=tar", f"{sha}:{tree_path}"],
        capture_output=True,
    )
    if archive.returncode != 0:
        raise InstallError(
            f"cannot read {tree_path} from source commit: {archive.stderr.decode().strip()}"
        )
    destination.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=BytesIO(archive.stdout)) as tar:
        tar.extractall(destination, filter="data")


def show_file(source: Path, sha: str, file_path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(source), "show", f"{sha}:{file_path}"],
        capture_output=True,
    )
    if result.returncode != 0:
        raise InstallError(f"cannot read {file_path} from source commit: {result.stderr.decode().strip()}")
    return result.stdout


def project_runtime_bundle(source: Path, sha: str, target: Path) -> None:
    """Build the methodology runtime bundle into ``target``."""
    manifest = show_file(source, sha, "manifest.toml")
    layout_paths = runtime_layout_paths(manifest)
    layout_payload = {relative: show_file(source, sha, relative) for relative in layout_paths}

    target.mkdir(parents=True, exist_ok=True)
    (target / "manifest.toml").write_bytes(manifest)
    for relative, content in layout_payload.items():
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)


def runtime_layout_paths(manifest: bytes) -> list[str]:
    """Runtime layout files derived from the methodology manifest."""
    try:
        document = tomllib.loads(manifest.decode("utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as error:
        raise InstallError(f"cannot parse manifest.toml: {error}") from error
    paths = []
    for entry in document.get("artifact_types", []):
        paths.append(f"schemas/{manifest_entry_name(entry, 'artifact_types')}.schema.json")
    for entry in document.get("protocols", []):
        paths.append(f"protocols/{manifest_entry_name(entry, 'protocols')}/PROTOCOL.md")
    return paths


def manifest_entry_name(entry: object, section: str) -> str:
    if isinstance(entry, dict) and isinstance(entry.get("name"), str):
        name = entry["name"]
        if is_safe_manifest_entry_name(name):
            return name
        raise InstallError(
            f"manifest.toml [[{section}]] name {name!r} must be a safe single path component"
        )
    raise InstallError(f"manifest.toml [[{section}]] entries must declare string name")


def is_safe_manifest_entry_name(name: str) -> bool:
    return (
        bool(name)
        and name != "."
        and "/" not in name
        and "\\" not in name
        and ".." not in name
    )


# The runtime-bundle children this installer manages under `~/.groundwork`.
# The resolved corpus (`principles/`) lives beside them and is converged
# separately — bundle convergence never rebuilds the whole root.
RUNTIME_BUNDLE_CHILDREN = ("manifest.toml", "schemas", "protocols", MARKER_NAME)
RETIRED_RUNTIME_BUNDLE_CHILDREN = ("mechanics", "lib", "bin")


def stage_runtime_bundle(options: Options, sha: str) -> Path:
    staging = Path(tempfile.mkdtemp(prefix=".groundwork.bundle.", dir=options.home))
    try:
        project_runtime_bundle(options.source, sha, staging)
        write_marker(staging, options.source, sha, "runtime", "groundwork")
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return staging


def converge_runtime_bundle(options: Options, staged: Path) -> None:
    runtime_root = options.home / ".groundwork"
    if (
        runtime_root.is_dir()
        and tree_payload(staged, include_marker=True) == bundle_payload(runtime_root)
        and not has_retired_runtime_children(runtime_root)
    ):
        return
    runtime_root.mkdir(parents=True, exist_ok=True)
    for child in (*RUNTIME_BUNDLE_CHILDREN, *RETIRED_RUNTIME_BUNDLE_CHILDREN):
        current = runtime_root / child
        if current.is_dir():
            shutil.rmtree(current)
        elif current.exists():
            current.unlink()
    for child in RUNTIME_BUNDLE_CHILDREN:
        staged_child = staged / child
        if staged_child.exists():
            staged_child.replace(runtime_root / child)


def has_retired_runtime_children(runtime_root: Path) -> bool:
    return any((runtime_root / child).exists() for child in RETIRED_RUNTIME_BUNDLE_CHILDREN)


def bundle_payload(runtime_root: Path) -> dict[str, bytes]:
    """The installed runtime bundle's payload, managed children only."""
    payload = {}
    for child in RUNTIME_BUNDLE_CHILDREN:
        path = runtime_root / child
        if path.is_file():
            payload[child] = path.read_bytes()
        elif path.is_dir():
            for rel, content in tree_payload(path, include_marker=True).items():
                payload[f"{child}/{rel}"] = content
    return payload


def marker_content(source: Path, sha: str, kind: str, name: str) -> str:
    return (
        f"managed-by={MANAGED_BY}\n"
        f"source={source}\n"
        f"source-sha={sha}\n"
        f"name={name}\n"
        f"kind={kind}\n"
    )


def write_marker(target: Path, source: Path, sha: str, kind: str, name: str) -> None:
    (target / MARKER_NAME).write_text(marker_content(source, sha, kind, name), encoding="utf-8")


def marker_matches(target: Path, source: Path, sha: str, kind: str, name: str) -> bool:
    marker = target / MARKER_NAME
    if not marker.is_file():
        return False
    return marker.read_text(encoding="utf-8") == marker_content(source, sha, kind, name)


def marker_is_ours(target: Path) -> bool:
    """Ownership authority, independent of which commit the marker records.

    A managed entry stays ours across version changes and across a run that
    updated the marker but failed before recording state — so ownership is
    the `managed-by` line alone, never the recorded source-sha."""
    marker = target / MARKER_NAME
    if not marker.is_file():
        return False
    return f"managed-by={MANAGED_BY}\n" in marker.read_text(encoding="utf-8")


def tree_payload(directory: Path, *, include_marker: bool = False) -> dict[str, bytes]:
    """Relative path → bytes for every file under ``directory``; the
    ownership marker is excluded unless asked for."""
    payload = {}
    for path in sorted(directory.rglob("*")):
        if path.is_file() and (include_marker or path.name != MARKER_NAME):
            payload[str(path.relative_to(directory))] = path.read_bytes()
    return payload


def source_payload(source: Path, sha: str, tree_path: str) -> dict[str, bytes]:
    """Relative path → bytes for ``<sha>:<tree_path>`` straight from git."""
    archive = subprocess.run(
        ["git", "-C", str(source), "archive", "--format=tar", f"{sha}:{tree_path}"],
        capture_output=True,
    )
    if archive.returncode != 0:
        raise InstallError(
            f"cannot read {tree_path} from source commit: {archive.stderr.decode().strip()}"
        )
    payload = {}
    with tarfile.open(fileobj=BytesIO(archive.stdout)) as tar:
        for member in tar.getmembers():
            if member.isfile():
                extracted = tar.extractfile(member)
                assert extracted is not None
                payload[member.name] = extracted.read()
    return payload


def read_state(state_file: Path) -> list[tuple[str, str, str, str, str]]:
    if not state_file.is_file():
        return []
    rows = []
    for line in state_file.read_text(encoding="utf-8").splitlines():
        target, name, kind, sha, root = line.split("\t")
        rows.append((target, name, kind, sha, root))
    return rows


def write_state(options: Options, sha: str, skills: list[str]) -> None:
    """Record the managed skill entries; a byte-identical state file is
    left untouched."""
    lines = []
    for root in target_roots(options.home):
        for name in skills:
            lines.append(f"{root / name}\t{name}\tskill\t{sha}\t{root}")
    content = "".join(f"{line}\n" for line in lines)
    state_file = options.state_dir / STATE_FILE_NAME
    if state_file.is_file() and state_file.read_text(encoding="utf-8") == content:
        return
    options.state_dir.mkdir(parents=True, exist_ok=True)
    temporary = state_file.with_name(state_file.name + ".tmp")
    temporary.write_text(content, encoding="utf-8")
    temporary.replace(state_file)


def state_owns_target(
    state_rows: list[tuple[str, str, str, str, str]],
    target: Path,
) -> bool:
    """Owned iff state records this target path and it still carries our
    marker. The marker's recorded sha is deliberately not consulted — a
    partially-failed update can leave the marker ahead of the state row,
    and the entry is still ours."""
    return any(row[0] == str(target) for row in state_rows) and marker_is_ours(target)


def install_skill(source: Path, sha: str, name: str, target: Path) -> None:
    temporary = Path(tempfile.mkdtemp(prefix=f"{target.name}.tmp.", dir=target.parent))
    extract_tree(source, sha, f"skills/{name}", temporary)
    write_marker(temporary, source, sha, "skill", name)
    if target.exists():
        shutil.rmtree(target)
    temporary.replace(target)


def skill_is_current(
    options: Options,
    state_rows: list[tuple[str, str, str, str, str]],
    sha: str,
    name: str,
    root: Path,
    desired: dict[str, bytes],
) -> bool:
    target = root / name
    row = (str(target), name, "skill", sha, str(root))
    if row not in state_rows:
        return False
    if not target.is_dir():
        return False
    if not marker_matches(target, options.source, sha, "skill", name):
        return False
    return tree_payload(target) == desired


def preflight_conflicts(options: Options, skills: list[str]) -> None:
    """Every desired target that already exists must be owned by this
    installer; anything else is an unmanaged conflict named before any
    mutation happens."""
    state_rows = read_state(options.state_dir / STATE_FILE_NAME)
    conflicts = []
    for root in target_roots(options.home):
        for name in skills:
            target = root / name
            if target.exists() and not state_owns_target(state_rows, target):
                conflicts.append(target)
    runtime_root = options.home / ".groundwork"
    if runtime_root.exists() and not (runtime_root / MARKER_NAME).is_file():
        conflicts.append(runtime_root)
    if conflicts:
        raise InstallError("; ".join(_describe_conflict(target) for target in conflicts))


def _describe_conflict(target: Path) -> str:
    description = f"unmanaged conflict at {target}"
    if (target / LEGACY_MARKER_NAME).is_file():
        description += (
            " (installed by groundwork-install; run `scripts/groundwork-install uninstall` first)"
        )
    return description


def remove_obsolete_entries(options: Options, skills: list[str]) -> None:
    """Remove state-recorded entries no longer shipped by the tree.

    Deletion is gated on this installer's own marker: an obsolete entry
    that lost its marker fails loudly rather than risking content this
    installer does not own."""
    state_rows = read_state(options.state_dir / STATE_FILE_NAME)
    desired = set(skills)
    obsolete = [Path(row[0]) for row in state_rows if row[1] not in desired]
    unmarked = [
        target
        for target in obsolete
        if target.exists() and not (target / MARKER_NAME).is_file()
    ]
    if unmarked:
        raise InstallError(
            "missing marker on obsolete managed entry: "
            + ", ".join(str(target) for target in unmarked)
        )
    for target in obsolete:
        if target.is_dir():
            shutil.rmtree(target)


def converge_skills(options: Options, sha: str, skills: list[str]) -> None:
    state_rows = read_state(options.state_dir / STATE_FILE_NAME)
    for name in skills:
        desired = source_payload(options.source, sha, f"skills/{name}")
        for root in target_roots(options.home):
            root.mkdir(parents=True, exist_ok=True)
            target = root / name
            if skill_is_current(options, state_rows, sha, name, root, desired):
                continue
            if (
                state_owns_target(state_rows, target)
                and target.is_dir()
                and tree_payload(target) == desired
            ):
                write_marker(target, options.source, sha, "skill", name)
                continue
            install_skill(options.source, sha, name, target)


def embedded_corpus_path(source: Path) -> Path:
    return source / "principles"


def effective_corpus_config(options: Options) -> PrinciplesCorpusConfig:
    """The corpus source this run resolves: the operator input when given,
    else the existing deployment config, else the embedded default."""
    if options.corpus_input is not None:
        return options.corpus_input
    return load_principles_config(options.config_path)


def record_corpus_config(options: Options) -> None:
    """Record the operator corpus input in the deployment-owned config.

    Only an explicit input writes; a semantically equal existing file is
    left byte-untouched so a hand-written operator config survives."""
    if options.corpus_input is None:
        return
    if options.config_path.exists():
        try:
            existing_config = load_principles_config(options.config_path)
        except PrinciplesConfigError:
            existing_config = None
        if existing_config == options.corpus_input:
            return
    write_principles_config(options.corpus_input, options.config_path)


def stage_corpus(options: Options, config: PrinciplesCorpusConfig) -> Path:
    """Materialize the configured corpus into a staging location under home.

    Staging happens before any target mutation: an unreachable remote or an
    index-less corpus aborts the run with nothing changed."""
    staging_parent = Path(tempfile.mkdtemp(prefix=".groundwork.corpus.", dir=options.home))
    staged = staging_parent / "corpus"
    try:
        materialize(config, embedded_corpus_path(options.source), staged)
    except BaseException:
        shutil.rmtree(staging_parent, ignore_errors=True)
        raise
    return staged


def swap_corpus(options: Options, staged: Path) -> None:
    """Move the staged corpus into place; a byte-identical resolved corpus
    is left untouched."""
    target = resolved_corpus_path(options.home / ".groundwork")
    if target.is_dir() and tree_payload(target) == tree_payload(staged):
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        shutil.rmtree(target)
    staged.replace(target)


def install(options: Options) -> None:
    sha = validate_source(options.source)
    skills = enumerate_skills(options.source, sha)
    corpus_config = effective_corpus_config(options)
    check_resolvable(corpus_config, embedded_corpus_path(options.source))
    preflight_conflicts(options, skills)
    staged_corpus: Path | None = None
    staged_runtime: Path | None = None
    try:
        staged_corpus = stage_corpus(options, corpus_config)
        staged_runtime = stage_runtime_bundle(options, sha)
        record_corpus_config(options)
        remove_obsolete_entries(options, skills)
        converge_skills(options, sha, skills)
        converge_runtime_bundle(options, staged_runtime)
        swap_corpus(options, staged_corpus)
    finally:
        if staged_corpus is not None:
            shutil.rmtree(staged_corpus.parent, ignore_errors=True)
        if staged_runtime is not None:
            shutil.rmtree(staged_runtime, ignore_errors=True)
    write_state(options, sha, skills)
    print(f"{PROGRAM}: installed {sha}")


def uninstall(options: Options) -> None:
    """Marker-verified removal of every managed entry and the runtime root.

    The resolved corpus is materialized content this installer owns and
    leaves with the runtime root; the deployment-owned config file is
    recorded into, never deleted."""
    state_file = options.state_dir / STATE_FILE_NAME
    if not state_file.is_file():
        raise InstallError("not installed")
    state_rows = read_state(state_file)
    targets = [Path(row[0]) for row in state_rows]
    runtime_root = options.home / ".groundwork"
    if runtime_root.exists():
        targets.append(runtime_root)
    unmarked = [
        target
        for target in targets
        if target.exists() and not (target / MARKER_NAME).is_file()
    ]
    if unmarked:
        raise InstallError(
            "missing marker on managed entry: " + ", ".join(str(target) for target in unmarked)
        )
    for target in targets:
        if target.is_dir():
            shutil.rmtree(target)
    state_file.unlink()
    print(f"{PROGRAM}: uninstalled")


def main(argv: list[str] | None = None) -> int:
    try:
        options = parse_args(sys.argv[1:] if argv is None else argv, dict(os.environ))
        if options.mode == "uninstall":
            uninstall(options)
        else:
            install(options)
    except (InstallError, PrinciplesConfigError, CorpusResolutionError) as error:
        print(f"{PROGRAM}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
