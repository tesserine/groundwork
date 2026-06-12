"""Setup-time materialization of the configured principles corpus.

Resolves the configured source (embedded | path | git) into the resolved
local corpus — the stable location reckon reads during reasoning. This
runs at install/setup only; nothing here executes during a reckon step,
and a remote source is fetched exactly once per resolution.

Every failure mode is loud and named: a present-but-invalid config, a
missing local source, an unreachable remote, or a corpus without a
readable index halts setup with a nonzero exit. A failed resolution never
replaces an existing resolved corpus (staging + atomic swap), and never
silently degrades to the default.

Deliberately stdlib-only, like ``tooling/forge_operations.py``: the
install path runs in deployments that carry no third-party packages.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if __package__ in (None, ""):  # invoked as a script by groundwork-install
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tooling.principles_config import (
    SOURCE_EMBEDDED,
    SOURCE_GIT,
    SOURCE_PATH,
    PrinciplesConfigError,
    PrinciplesCorpusConfig,
    load_principles_config,
)

# A corpus is structurally present when its root carries a readable index.
CORPUS_INDEX_CANDIDATES = ("PRINCIPLES.md", "README.md")


class CorpusResolutionError(Exception):
    pass


def corpus_index(directory: Path) -> Path | None:
    for name in CORPUS_INDEX_CANDIDATES:
        candidate = directory / name
        if candidate.is_file():
            return candidate
    return None


def check_resolvable(config: PrinciplesCorpusConfig, embedded_path: Path) -> None:
    """Mutation-free preflight: validates what can be validated without
    touching the network."""
    if config.source == SOURCE_EMBEDDED:
        _require_corpus_directory(embedded_path, "embedded corpus")
    elif config.source == SOURCE_PATH:
        assert config.path is not None
        _require_corpus_directory(config.path, "configured corpus path")
    # git: reachability is established by the fetch itself at materialization.


def materialize(config: PrinciplesCorpusConfig, embedded_path: Path, target: Path) -> None:
    """Resolve the configured source into ``target`` via staging + atomic swap."""
    target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f"{target.name}.resolve.", dir=target.parent))
    try:
        if config.source == SOURCE_EMBEDDED:
            _stage_directory(embedded_path, "embedded corpus", staging)
        elif config.source == SOURCE_PATH:
            assert config.path is not None
            _stage_directory(config.path, "configured corpus path", staging)
        else:
            _stage_git_clone(config, staging)

        index = corpus_index(staging)
        if index is None:
            raise CorpusResolutionError(
                f"resolved corpus has no readable index ({' or '.join(CORPUS_INDEX_CANDIDATES)}) "
                f"at its root — source: {_describe_source(config)}"
            )
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    if target.exists():
        shutil.rmtree(target)
    staging.replace(target)


def _require_corpus_directory(directory: Path, label: str) -> None:
    if not directory.is_dir():
        raise CorpusResolutionError(f"{label} does not exist or is not a directory: {directory}")
    if corpus_index(directory) is None:
        raise CorpusResolutionError(
            f"{label} has no readable index ({' or '.join(CORPUS_INDEX_CANDIDATES)}) at its root: {directory}"
        )


def _stage_directory(source: Path, label: str, staging: Path) -> None:
    if not source.is_dir():
        raise CorpusResolutionError(f"{label} does not exist or is not a directory: {source}")
    shutil.copytree(source, staging, dirs_exist_ok=True)


def _stage_git_clone(config: PrinciplesCorpusConfig, staging: Path) -> None:
    assert config.url is not None
    command = ["git", "clone", "--quiet", "--depth", "1"]
    if config.ref:
        command.extend(["--branch", config.ref])
    command.extend([config.url, str(staging / "clone")])
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()
        raise CorpusResolutionError(
            f"cannot fetch corpus repository {_describe_source(config)}: "
            f"{detail[-1] if detail else 'git clone failed'}"
        )
    clone = staging / "clone"
    shutil.rmtree(clone / ".git", ignore_errors=True)
    for entry in clone.iterdir():
        entry.rename(staging / entry.name)
    clone.rmdir()


def _describe_source(config: PrinciplesCorpusConfig) -> str:
    if config.source == SOURCE_EMBEDDED:
        return "embedded"
    if config.source == SOURCE_PATH:
        return f"path {config.path}"
    return f"{config.url}" + (f" (ref {config.ref})" if config.ref else "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Materialize the configured principles corpus into the resolved local location."
    )
    parser.add_argument("--config", required=True, help="Path to the deployment principles config file.")
    parser.add_argument("--embedded", required=True, help="Path to the embedded default corpus directory.")
    parser.add_argument("--target", required=True, help="Resolved local corpus directory to materialize into.")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Validate the configuration and local sources without materializing.",
    )
    args = parser.parse_args(argv)

    try:
        config = load_principles_config(args.config)
        if args.check_only:
            check_resolvable(config, Path(args.embedded))
        else:
            materialize(config, Path(args.embedded), Path(args.target))
    except (PrinciplesConfigError, CorpusResolutionError) as error:
        print(f"corpus-resolution: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
