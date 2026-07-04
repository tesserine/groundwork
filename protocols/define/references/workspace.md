# Workspace Preparation

Reference for define Step 2. States the outcomes preparation must establish
and the repository-local conventions for reaching them. Command sequences
are illustrative; the outcomes are the contract.

## Outcomes

1. **Clean ground.** No unrelated uncommitted changes in the worktree.
   - Changes relevant to this work-unit: keep and note.
   - Stale or unrelated changes: stash or discard — confirm with the
     operator before any destructive action.
2. **Current base.** The local base branch matches the remote:
   `git checkout main && git fetch origin --prune && git merge --ff-only origin/main`.
3. **Feature branch.** All work happens on a branch named for the work-unit:
   - Tracker-linked work-unit: `issue-<N>/<slug>` where `<N>` is the
     tracker number when the connector display exposes one; otherwise use
     `issue/<slug>`.
   - No tracker linkage: `feat/<slug>`, `fix/<slug>`, or `chore/<slug>`.
   - `<slug>` is the work-unit title — lowercase, hyphenated, truncated to
     40 characters.
4. **Tracker claimed.** For tracker-backed work-units, the tracker reflects
   that this work-unit is in progress. Resolve the invariant
   `claim-work-unit` connector capability operation. The work-unit supplies
   the opaque connector `handle`.

## Failure Policy

- Referenced work-units missing from injected session context are a
  substrate failure: halt and report rather than retrieving through a
  side channel or proceeding degraded.
- If the base cannot be fast-forwarded or the branch cannot be created,
  resolve the obstacle structurally (see the `resolve` skill) before
  authoring the contract — a contract authored on broken ground will be
  delivered from broken ground.
