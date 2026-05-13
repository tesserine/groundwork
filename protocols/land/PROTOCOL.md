---
name: land
description: >-
  One-word closeout: land this branch. Closing ceremony verifies completion and
  documentation before mechanical merge. Merge to main, sync, delete feature
  branch, close satisfied work-units, comment progress on partial work-units.
  Trigger on: 'land', 'land this', 'merge and close', 'ship it'.
---

# Land — Close, Verify, Merge

## Overview

Protocol for closing the session lifecycle: verify the work satisfies its
contract, review documentation coverage, merge the branch, close the
satisfied work-units, and deliver the `completion-record` that seals the
archival trail.

`land` operates in two phases:

- **Phase 0: Closing** — a ceremony that prepares the work for delivery. Four
  steps mirror `take`'s opening ceremony in reverse: gather context, verify
  acceptance, review documentation, seal the gate.
- **Phase 1: Mechanical** — the merge-and-close sequence, gated by Phase 0.

Phase 0 (gather, verify, review, seal) is to `land` what Phase 0 (orient,
observe, frame, banish) is to `take`. The opening ceremony prepares the agent
for work; the closing ceremony prepares the work for delivery.

Do not stop after merge — stopping leaves branches dangling and work-units unclosed. The full sequence is atomic: ceremony through close.

Do not ask for confirmation before landing. Invoking `land` IS the user's approval to execute the entire workflow.

---

## Preconditions

- Working tree must be clean before starting.
- Current branch must not be `main`.
- GitHub issue numbers are optional:
  - Prefer explicit user-provided GitHub issue number(s).
  - Else infer from branch name using one of:
    - `issue-<number>/<slug>` (single GitHub issue)
    - `issues-<number>-<number>-.../<slug>` (multi-GitHub-issue, unbounded)
  - If no GitHub issue numbers are available, continue with the no-GitHub-issue closeout path.
- Forge tooling (`gh`) is the primary path for PR lookup, PR merge,
  acceptance-criteria evaluation against tracker state, and work-unit
  closure. Where `gh` is unavailable, the protocol falls back to local
  merge (step 1c fallback) and records unclosed work-units in the
  `completion-record` for manual follow-up. The protocol does not
  hard-fail on `gh` absence.

---

## Procedure

### Phase 0: Closing

The closing ceremony equips the landing with everything the mechanical phase
needs: context about what was built and why, verification that acceptance
criteria are met, confirmation that documentation reflects reality, and a gate
that blocks merge until readiness is confirmed. Each step builds on the
previous — gather loads context, verify checks acceptance, review checks
documentation, seal confirms the gate.

Follows the closing sequence: gather → verify → review → seal.

#### 0a. Gather

Collect the full context of the work being landed.

```
◈ GATHER
Branch: [name] | Issues: [numbers or none]
Diff: [file count] files, [insertions]+/[deletions]-
Commits: [count] ([oneline summaries])
CHANGELOG: [present | missing — needs entry | not needed]
```

Implementation:
- Confirm the current branch is not `main` and the working tree is clean. Record the feature branch name.
- Extract GitHub issue numbers from the branch name:
  - `issue-42/fix-login` → GitHub issue 42
  - `issues-5-8/license-cleanup` → issues 5 and 8
  - If neither the user nor the branch name provides issue numbers, mark the landing as no-GitHub-issue.
- Summarize the branch diff: `git diff origin/main...HEAD --stat`.
- Summarize the commit log: `git log origin/main..HEAD --oneline`.
- Check whether `CHANGELOG.md` appears in the branch diff (`git diff origin/main...HEAD --name-only`). The changelog is how users discover what changed between versions. Evaluate whether the branch changes are significant enough to warrant an entry. New features, behavior changes, bug fixes, and breaking changes generally belong in the changelog. Internal refactoring, typo fixes, and CI tweaks generally don't. If the changes look user-visible but no entry exists, flag it to the user before proceeding.

#### 0b. Verify

Evaluate whether the branch changes satisfy acceptance criteria and all
verification checks pass. This step runs pre-merge while the branch diff is
available.

```
◈ VERIFY
Criteria: [all met | partial — list remaining]
```

Implementation: the `verify` protocol has already run upstream — its
`completion-evidence` artifact is available through runa's session context.
Phase 0b is a seal spot-check, not re-invocation of `verify`: confirm that
acceptance-criteria coverage against the current branch diff still matches
the upstream `completion-evidence` baseline, and stop there. If drift is
detected, the seal fails and `land` halts (per the Failure Policy); running
`verify` again is an upstream repair, not part of this phase. Where `gh` is
available and the branch is GitHub-issue-linked, fetch each target issue
(`gh issue view`) to cross-reference acceptance criteria against the diff.
Classify each work-unit as satisfied (all criteria met) or partial (some
remain). If no acceptance criteria can be extracted from the work-unit body,
classify as partial — a work-unit without explicit criteria may have
unstated requirements. If an issue fetch fails, treat that work-unit as
partial and log a warning. For no-GitHub-issue landings, skip the
tracker-evaluation branch and rely on the upstream `completion-evidence`.
Store classifications for Phase 1e.

#### 0c. Review

Confirm documentation reflects the changes being landed. This is mandatory —
documentation drift blocks the seal.

```
◈ REVIEW
Docs: [clean | fixed: list | tracked: work-unit refs]
```

Implementation: perform the documentation-review discipline that the
`document` protocol encodes against the current branch diff, confirming
coverage has not drifted since `document` ran. Check whether changed files
affect areas with documentation artifacts (README, ARCHITECTURE, API
docs). Fix drift directly and commit; file tracking work-units for
anything deeper. Record a coverage summary: each artifact checked, its
status, and any action taken.

#### 0d. Seal

Gate check before mechanical merge. All three conditions must hold:

1. Verification passed or all linked work-units classified (Phase 0b complete)
2. Documentation reviewed — drift fixed or tracked (Phase 0c complete)
3. CHANGELOG entry present if changes are user-visible (Phase 0a flagged)

```
◈ SEAL
[PASSED — proceed to Phase 1 | BLOCKED — list failures]
```

If the seal fails, fix the blocking GitHub issue(s) and re-evaluate. Do not proceed to
Phase 1 until the seal passes.

### Phase 1: Mechanical

Gated by Phase 0. Do not enter this phase until the seal passes.

#### 1a. Evaluate commit history for squash

Examine the branch's commit history to decide whether to squash on merge. Use `git log origin/main..HEAD` variants to inspect commit subjects and touched files.

**Decision framework** (apply judgment, not mechanical rules):

- **Squash when** the history is iterative refinement — a feature commit followed by fix-ups that revise the same change: majority of commits are fixes of the initial change, commits touch the same files, all share the same scope/component.
- **Preserve when** commits represent distinct work-units — single-commit branches, different components/scopes, multi-step features where each step is meaningful independently.

**When squashing**, draft a consolidated commit message: use the conventional-commit prefix/scope from the initial commit, summarize the consolidated change, don't enumerate squashed commits.

Record the squash decision. If squashing, also record the drafted commit message.

#### 1b. Discover PR number

Where `gh` is available, look up the open PR for the feature branch
(`gh pr list --head <branch> --state open`). This must happen before merge
because `gh pr merge` requires the PR number. If no PR is found — or if
`gh` is unavailable — fall back to local merge (step 1c fallback).

#### 1c. Merge via PR API

Merge through GitHub's PR API so the PR is recorded as "merged," not just "closed." This is the primary merge path.

1. Run `gh pr merge <number>` with the appropriate strategy flag: `--squash` if squashing (with `--subject` and `--body` for the drafted commit message), `--merge` if preserving history.
2. Include `--delete-branch` to let GitHub clean up the remote branch.
3. After the API merge completes, sync local state: `git checkout main`, `git fetch origin --prune`, `git merge --ff-only origin/main`.
4. Record the merge commit SHA from the local main HEAD for use in GitHub issue comments.

**Why not local merge:** A local `git merge` + `git push` lands the code on main but bypasses GitHub's PR merge tracking. GitHub sees the PR's commits already on main and auto-closes the PR as "closed" rather than "merged" when the branch is deleted. This loses PR merge metadata and breaks PR history.

##### 1c fallback: local merge (no PR exists)

This path is only for branches that never had a PR — not a fallback for when `gh pr merge` fails. If the API merge fails, the failure policy applies (stop, don't retry locally).

If no PR was found in step 1b, merge locally:

1. Fetch and fast-forward `main` to match origin (`git fetch origin --prune`, `git checkout main`, `git merge --ff-only origin/main`).
2. Merge the feature branch. If squashing: `git merge --squash`, then `git commit` with the drafted message. If preserving: `git merge --no-ff`.
3. Push `main` to origin.
4. Record the merge commit SHA.

#### 1d. Delete feature branch

Delete any remaining branch references:
- Remote: skip if `--delete-branch` was used in step 1c. Otherwise, `git push origin --delete <branch>` (tolerate failure if already gone).
- Local: `git branch -D <branch>`. The `-D` flag (force delete) is required because squash merges don't record merge parentage, so `-d` refuses even though the content is safely on `main`.
- Prune stale remote-tracking references: `git fetch origin --prune`.

#### 1e. Comment and close GitHub issue(s) (GitHub-issue-linked branches only)

If no linked work-units were provided or inferred, skip this step. Where
`gh` is unavailable, skip this step and record the would-have-been-closed
work-unit IDs in the `completion-record` for manual follow-up.

Apply the classifications from Phase 0b.

**For satisfied GitHub issues**, post a close comment and close the GitHub issue:

> Implemented and merged in PR #`<number>` (commit `<sha>`). Closing as complete.
>
> *(If no PR was found, omit the PR reference.)*

Then close: `gh issue close <number> --reason completed`.

**For partial GitHub issues**, post a progress comment but leave the GitHub issue open:

> Progress from PR #`<number>` (commit `<sha>`):
>
> **Delivered:**
> - criterion 1
> - criterion 2
>
> **Remaining:**
> - criterion 3

If any comment or close operation fails, continue processing remaining work-units, then report which operations failed.

#### 1f. Deliver `completion-record`

The capstone is delivery of the `completion-record` artifact — the terminal
archival record for the work-unit. Invoke the `completion-record` MCP tool. The
object below is MCP tool input, not artifact body. `instance_id` is a tool
parameter that names the artifact instance; it is extracted before validating
artifact content, becomes the workspace filename, and must not appear in the
artifact body. Runa injects `work_unit` from session context; the agent does
not supply `work_unit`. Do not write the workspace JSON file directly:

```
completion-record({
  instance_id: "<slug>",
  criterion_summary: "<how acceptance criteria were met>",
  gaps: ["<known gaps or deferred work — empty array if none>"],
  merge_reference: "<merge commit SHA or PR URL from step 1c>",
  documentation_status: "<summary of coverage from Phase 0c>"
})
```

Runa validates the remaining artifact body fields against the completion-record
schema, persists the artifact, and records it in the artifact store.

If work-units could not be closed in the tracker (e.g., `gh` unavailable
in step 1e), include those IDs and the reason in `gaps` so the manual
follow-up is discoverable from the archival record.

#### 1g. Verify and report

Confirm success conditions:
- Current branch is `main`
- Working tree is clean
- Feature branch absent on origin
- PR state is `MERGED` (not just `CLOSED`)
- For GitHub-issue-linked landings: every satisfied GitHub issue state is `CLOSED` (or recorded in `gaps` if `gh` was unavailable)
- For GitHub-issue-linked landings: every partial GitHub issue has a progress comment listing remaining criteria
- `completion-record` artifact delivered
- Documentation coverage summary reported

Report the final state including:
- GitHub issue disposition:
  - GitHub-issue-linked: satisfied (closed) and partial (open with remaining criteria)
  - No-GitHub-issue: explicitly report "no GitHub issue linked"
- `completion-record` instance_id
- Documentation coverage summary from Phase 0c
- Any warnings or failed operations from earlier steps

---

## Failure Policy

- **Seal failure blocks Phase 1.** If the seal (Phase 0d) fails, the operator resolves the blocking condition (GitHub issue, documentation drift, upstream verify drift, etc.) and directs runa to re-activate `land`; runa resumes the ceremony at the failed step. Do not proceed to mechanical merge until the seal passes.
- If `gh pr merge` fails: stop immediately, do not close the GitHub issue. If the failure is transient (network), retry once. If structural (merge conflict, check failure), report and stop. Do not fall back to local merge — the whole point of using the API is to preserve PR merge metadata.
- If branch deletion fails after successful merge: warn about the deletion failure and continue to GitHub issue close/comment steps. The code is safely on `main`; branch cleanup is not a prerequisite for issue closure.
- If GitHub issue comment/close API fails for one GitHub issue: continue processing remaining GitHub issues, then report failed GitHub issue number(s) explicitly.
- If acceptance criteria evaluation fails in Phase 0b (GitHub issue fetch error, criteria unparseable): the inline handling applies — treat the GitHub issue as partial, log a warning. Partial classification does not block the seal; it flows through to Phase 1e where the GitHub issue is left open with a progress comment.
- **Documentation drift blocks the seal.** Drift discovered in Phase 0c must be fixed directly or tracked via a work-unit before the seal can pass. Do not proceed with unresolved drift.
- If no GitHub issue numbers are available: do not prompt for GitHub issue IDs during `land`; proceed with merge/sync/cleanup and report a no-GitHub-issue landing.
- If commit history evaluation is uncertain: default to preserve (`--no-ff`). Squashing is an optimization; when in doubt, keep the original history.

---

## Cross-References

- `take`: the opening bookend — opening ceremony and session initiation before
  implementation. `take`'s opening ceremony (orient, observe, frame, banish)
  prepares the agent for work; `land`'s closing ceremony (gather, verify, review,
  seal) prepares the work for delivery. Parallel structure, inverse direction.
- `submit` for the preceding phase: commit, push, and PR creation
- `verify`: invoked during Phase 0b to evaluate
  acceptance criteria and verify completion evidence before merge
- `document`: invoked during Phase 0c for documentation-review — confirms
  documentation reflects the changes being landed
- `decompose` for work-unit lifecycle patterns and tracking work-units from doc review
