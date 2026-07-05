#!/usr/bin/env python3
"""Return a run worktree to Groundwork's canonical clean state."""

from __future__ import annotations

import argparse
import subprocess
import sys
import time


class TidyUpError(Exception):
    """A named canonical-clean residual or cleanup obstacle."""


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        command = "git " + " ".join(args)
        detail = (result.stderr or result.stdout).strip()
        raise TidyUpError(f"{command} failed: {detail}")
    return result


def branch_exists(branch: str) -> bool:
    return git("show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False).returncode == 0


def remote_branch_exists(branch: str) -> bool:
    return (
        git("show-ref", "--verify", "--quiet", f"refs/remotes/origin/{branch}", check=False).returncode
        == 0
    )


def canonical_branch() -> str:
    origin_head = git("symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD", check=False)
    if origin_head.returncode == 0:
        name = origin_head.stdout.strip()
        if name.startswith("origin/") and len(name) > len("origin/"):
            return name.removeprefix("origin/")
    return "main"


def current_branch() -> str | None:
    result = git("symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def ensure_repository() -> None:
    result = git("rev-parse", "--is-inside-work-tree", check=False)
    if result.returncode != 0 or result.stdout.strip() != "true":
        raise TidyUpError("not inside a git worktree")


def fetch_origin() -> None:
    if git("remote", "get-url", "origin", check=False).returncode == 0:
        git("fetch", "origin", "--prune")


def checkout_canonical(canonical: str) -> None:
    if not branch_exists(canonical):
        if remote_branch_exists(canonical):
            git("checkout", "-B", canonical, f"origin/{canonical}")
        else:
            raise TidyUpError(f"canonical branch {canonical!r} does not exist")
    else:
        git("checkout", canonical)
    if remote_branch_exists(canonical):
        git("merge", "--ff-only", f"origin/{canonical}")


def hard_reset_and_clean() -> None:
    git("reset", "--hard")
    git("clean", "-fd")


def delete_branch(branch: str | None) -> None:
    if branch and branch_exists(branch):
        git("branch", "-D", branch)


def prune_worktrees() -> None:
    git("worktree", "prune")


def status_porcelain() -> str:
    return git("status", "--porcelain").stdout.strip()


def verify_canonical_clean() -> None:
    canonical = canonical_branch()
    residuals: list[str] = []

    status = status_porcelain()
    if status:
        residuals.append(f"working tree is not porcelain-clean: {status}")

    branch = current_branch()
    if branch is None:
        residuals.append("HEAD is detached")
    elif branch != canonical:
        residuals.append(f"HEAD is on {branch!r}, expected canonical branch {canonical!r}")

    clean_check = git("ls-files", "--others", "--exclude-standard", check=False)
    if clean_check.returncode != 0:
        residuals.append(f"could not inspect untracked residue: {clean_check.stderr.strip()}")
    elif clean_check.stdout.strip():
        residuals.append(f"run-scoped residue remains outside ignored paths: {clean_check.stdout.strip()}")

    prune = git("worktree", "prune", "--dry-run", check=False)
    if prune.returncode != 0:
        residuals.append(f"could not inspect linked worktree residue: {prune.stderr.strip()}")

    if residuals:
        raise TidyUpError("; ".join(residuals))


def run_branch_before_cleanup(canonical: str) -> str | None:
    branch = current_branch()
    if branch == canonical:
        return None
    return branch


def tidy_land() -> None:
    canonical = canonical_branch()
    run_branch = run_branch_before_cleanup(canonical)
    fetch_origin()
    checkout_canonical(canonical)
    hard_reset_and_clean()
    delete_branch(run_branch)
    prune_worktrees()
    verify_canonical_clean()


def tidy_abandon() -> None:
    canonical = canonical_branch()
    run_branch = run_branch_before_cleanup(canonical)
    hard_reset_and_clean()
    fetch_origin()
    checkout_canonical(canonical)
    delete_branch(run_branch)
    prune_worktrees()
    verify_canonical_clean()


def ensure_halt_branch(canonical: str) -> str:
    branch = current_branch()
    if branch and branch != canonical:
        return branch

    stamp = time.strftime("%Y%m%d%H%M%S")
    branch = f"halt/{stamp}"
    suffix = 1
    candidate = branch
    while branch_exists(candidate):
        suffix += 1
        candidate = f"{branch}-{suffix}"
    git("checkout", "-b", candidate)
    return candidate


def preserve_halt_commit(branch: str) -> None:
    git("add", "-A")
    staged = git("diff", "--cached", "--name-only").stdout.strip()
    if not staged:
        return
    git(
        "-c",
        "user.name=Groundwork Tidy Up",
        "-c",
        "user.email=groundwork-tidy-up@example.invalid",
        "commit",
        "-m",
        f"halt: preserve work-in-progress on {branch}",
    )


def tidy_halt() -> None:
    canonical = canonical_branch()
    halt_branch = ensure_halt_branch(canonical)
    preserve_halt_commit(halt_branch)
    fetch_origin()
    checkout_canonical(canonical)
    git("reset", "--hard")
    git("clean", "-fd")
    prune_worktrees()
    verify_canonical_clean()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["land", "abandon", "halt", "verify"])
    args = parser.parse_args()

    try:
        ensure_repository()
        if args.kind == "land":
            tidy_land()
        elif args.kind == "abandon":
            tidy_abandon()
        elif args.kind == "halt":
            tidy_halt()
        else:
            verify_canonical_clean()
    except TidyUpError as error:
        print(f"canonical-clean residual: {error}", file=sys.stderr)
        return 1

    print("canonical-clean verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
