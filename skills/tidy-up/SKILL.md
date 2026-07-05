---
name: tidy-up
description: >-
  Return a repository to its canonical clean post-run state when a run ends
  through land, abandonment or regeneration, or halt.
metadata:
  version: "1.0.0"
  updated: "2026-07-05"
---

# Tidy-Up

Tidy-up is the closing worktree discipline for a Groundwork run. Define opens
the run on clean ground and a feature branch; tidy-up closes the run by making
the repository truthful for the next reader. It removes process residue only.
It never removes landed work or a halt disposition the operator still needs to
inspect.

The executable mechanics live in one place:

```
python3 skills/tidy-up/scripts/tidy_up.py <kind>
```

Resolve the script path from the methodology root and run it with the current
working directory inside the repository being tidied. `<kind>` is one of
`land`, `abandon`, `halt`, or `verify`. The script is the mechanics home; this
skill names the outcomes and the per-kind action sequence.

## The Canonical Clean State

The canonical clean state is the close-side complement to define's workspace
preparation. It consults
[`workspace.md` Outcome 1 "Clean ground"](../../protocols/define/references/workspace.md)
as the opening clean-worktree invariant and
[`workspace.md` Outcome 3 "Feature branch"](../../protocols/define/references/workspace.md)
as the run branch departure point that tidy-up returns from.

1. **Working tree porcelain-clean.** `git status --porcelain` reports no
   staged, unstaged, or untracked-unignored residue.
2. **HEAD rests on the canonical branch.** The checkout is not detached and
   does not remain on a leftover run branch; it rests on the repository's
   canonical branch, derived from `origin/HEAD` with `main` as fallback.
3. **No run-scoped residue outside ignored paths.** Run scratch files, build
   artifacts, and linked worktree residue introduced by the run are removed
   unless the repository declares them ignorable.
4. **Landed work is untouched.** A run that landed a change still contains
   that landed content byte-for-byte; tidy-up removes process scaffolding,
   not intended deliverables.

If any check cannot be reached, the script prints the named residual state to
stderr and exits nonzero. Do not proceed silently past a failed check; route
the obstacle through the `resolve` skill.

## Termination Kinds

### Land

Land starts after the approved change has been applied, reflected, closed out,
and recorded. The landed content is already on the canonical branch. Tidy-up
checks out the canonical branch, fetches and fast-forwards it to its remote
state, discards only process scaffolding from the worktree, removes
untracked-unignored residue while preserving ignored files, deletes the run
branch, prunes run-introduced worktrees, and verifies canonical-clean.

Run:

```
python3 skills/tidy-up/scripts/tidy_up.py land
```

### Abandonment and Regeneration

Abandonment and regeneration start from a run whose work must not remain in the
checkout. Tidy-up discards uncommitted residue, removes untracked-unignored
residue while preserving ignored files, returns to the canonical branch,
fast-forwards it to its remote state, deletes the run branch carrying
unlanded work, prunes run-introduced worktrees, and verifies canonical-clean
before a fresh derivation begins.

Run:

```
python3 skills/tidy-up/scripts/tidy_up.py abandon
```

### Halt

Halt starts from a run whose disposition still needs to be visible. Tidy-up
preserves all tracked and untracked-unignored work-in-progress as a
halt-marked commit on the run branch, creating a named halt branch first when
the run halted on a detached HEAD. It then returns the checkout to the
canonical branch, fast-forwards it to its remote state, preserves the run
branch as the inspectable halt disposition, prunes worktrees, and verifies
canonical-clean.

Run:

```
python3 skills/tidy-up/scripts/tidy_up.py halt
```

## Verification

Use verify mode when no cleanup action should run and only the postcondition
should be checked:

```
python3 skills/tidy-up/scripts/tidy_up.py verify
```

Verification runs the four canonical-clean checks above. A dirty worktree,
detached HEAD, non-canonical checkout, or worktree-prune failure is reported as
a named canonical-clean residual on stderr with a nonzero exit.

## Corruption Modes

- **Clean-by-discard.** Reaching a clean status by removing landed work or an
  intended halt disposition. Canonical-clean preserves intended deliverables.
- **Partial-success silence.** Reporting tidy-up complete after a failed reset,
  checkout, clean, branch deletion, or verification. Every failure is loud.
- **Mechanics duplication.** Copying git cleanup commands into land,
  contract, orient, or another termination surface. The script is the single
  mechanics home; other surfaces invoke this skill by reference.
- **Ignored-boundary breach.** Removing ignored files with an overbroad clean
  operation. Tidy-up removes untracked-unignored residue, not repository-
  declared ignored state.

## Cross-References

- `land` (protocol): invokes tidy-up after completion-record delivery.
- `contract` (skill): routes regenerated and abandoned runs through tidy-up
  before a fresh derivation begins.
- `orient` (skill): states the run-lifecycle rule, including halt.
- [`workspace.md`](../../protocols/define/references/workspace.md): owns the
  opening clean-ground and feature-branch outcomes tidy-up closes.
