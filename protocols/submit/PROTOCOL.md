---
name: submit
description: >-
  Package working changes into a PR: ensure feature branch, analyze and commit
  changes, push, then create or update a PR linked to GitHub issue(s).
  The middle phase of the session lifecycle between take and land.
  Trigger on: 'submit', 'submit pr', 'create pr', 'open pr',
  'send for review', 'package this up'.
---

# Submit — Commit, Push, PR

## Overview

Protocol for packaging verified, documented changes into a PR and delivering
the `patch` artifact. Fires when implementation is complete and reviewed
changes need to cross into the review stage.

`submit` means:
1. Resolve the working context (branch, changes, linked issues)
2. Ensure a feature branch exists (guard rail if on `main`)
3. Analyze changes and produce well-formed commits
4. Resolve whether delivery updates an existing PR or opens a new PR
5. Push to remote
6. Create a PR when needed
7. Deliver the `patch` artifact via the MCP tool
8. Report the result and suggest next steps

The session lifecycle is: `take` (initiate session) → implement → `submit`
(package for review) → review → `land` (merge and close). `submit` is the
transition from execution to review.

Do not stop after creating or updating the PR — the delivery and report steps
(7 and 8) are part of the protocol. Invoking `submit` IS the operator's
approval to execute the full sequence.

---

## Preconditions

- Deliverable local work means uncommitted changes OR committed work identified
  from the branch's tracking and PR state. If the working tree is clean and no
  deliverable commits exist, there is nothing new to submit. When an open PR
  exists, report its current state and recommend `land` if appropriate; when no
  open PR exists, report and stop.
- Producing the `patch` capstone requires a real PR reference, which in turn
  requires forge tooling (`gh` authenticated against the remote). Where forge
  tooling is absent, the protocol can commit and push locally but cannot
  deliver the `patch` artifact — see step 6 for the failure path.

---

## Procedure

### 1. Resolve context

Determine:
- Current branch name.
- Whether on `main` or a feature branch.
- Whether uncommitted changes exist (`git status`).
- Whether an open PR exists for the current branch (`gh pr list --head <branch>
  --state open --json url,number,headRefOid,headRefName,headRepository,headRepositoryOwner`)
  when `gh` is available. PR discovery handles result counts explicitly:
  0 results means no open PR; 1 result means that PR is the working PR; 2+
  results means disambiguate by head repository before recording any working
  PR. To disambiguate multiple results, filter candidates by PR head repository
  against local remotes using shared GitHub remote matching and each remote's
  effective push URL. If exactly one PR survives, use it as the working PR. If
  zero or 2+ candidates survive, stop with Ambiguous PR discovery before fetch,
  ancestry classification, push, or patch delivery.
- For the working PR, run `gh repo view --json nameWithOwner,url` in the same
  repository context as the PR listing, and record that value as the PR base
  repository identity. For the working PR, record the PR URL as the downstream
  PR reference, the PR number, the PR head SHA (`headRefOid`) for ancestry
  classification, the PR head branch (`headRefName`), the PR head repository
  (`<headRepositoryOwner.login>/<headRepository.name>`) for existing PR push
  delivery, and the PR base repository for PR-head fetch. Resolve a local remote
  matching the PR base repository, using that remote's fetch URL, and fetch the
  PR head into the local object database before post-commit deliverability
  classification:
  `git fetch <base-repo-remote> pull/<number>/head`. This is the GitHub PR
  refspec paired with `gh` discovery. Existing-PR delivery is a single
  GitHub-shaped commitment across `gh` discovery, the `pull/<number>/head`
  refspec, and shared GitHub remote matching; adapting the protocol to another
  forge requires changing all three together. After fetching, verify that
  `headRefOid` resolves as a commit before any operation consumes it.
- Shared GitHub remote matching uses one normalization rule for every consumer:
  accept SSH and HTTPS GitHub URLs, strip `.git`, compare the lowercase
  `<owner>/<repo>`, and treat non-GitHub URL forms as non-matches. Fetch
  resolution inspects `git remote get-url <remote>` against the PR base
  repository; push resolution and PR discovery disambiguation inspect
  `git remote get-url --push <remote>` against the PR head repository.
- GitHub issue number(s), resolved in priority order:
  1. Explicit operator-provided GitHub issue number(s).
  2. Branch name pattern: `issue-<N>/<slug>` (single) or
     `issues-<N>-<M>-.../<slug>` (multi).
  3. None — proceed without GitHub issue linkage.

If GitHub issue number(s) are available and `gh` is installed, fetch issue
title(s) and body(ies) via `gh issue view` for use in steps 3 and 6.

### 2. Ensure feature branch

If already on a feature branch: record the branch name and continue.

If on `main` (or detached HEAD):
1. Derive a branch name:
   - If GitHub issue number(s) known: `issue-<N>/<slug>` (single) or
     `issues-<N>-<M>/<slug>` (multi), where slug is the GitHub issue title —
     lowercase, hyphenated, truncated to 40 chars.
   - If no linked GitHub issue: `feat/<slug>`, `fix/<slug>`, or `chore/<slug>` based on
     change classification, where slug summarizes the changes.
2. Create and switch to the branch: `git checkout -b <branch>`.

### 3. Analyze changes and commit

This step is the protocol's core analytical value: understanding changes
well enough to produce meaningful commit structure, not just staging
everything at once.

This shared step applies before either PR delivery path. The same commit
analysis discipline applies whether the deliverable is a new PR or an existing
PR update.

If the working tree has no uncommitted changes, skip to step 4; committed-work
deliverability is classified there against the final submission `HEAD`.

**3a. Understand intent.** Examine all uncommitted modifications
(`git diff`, `git diff --staged`). If GitHub issue context is available,
cross-reference changes against acceptance criteria.

**3b. Identify logical groups.** Find related changes that belong in the same
atomic commit. Apply the Complete Feature Rule: implementation, documentation,
and tests for one feature belong in one commit — never split docs from the code
they document.

**3c. Plan commits.** Design atomic commits, each serving a single purpose.
Use conventional commit format: `type(scope): description` where type is
`feat`, `fix`, `refactor`, `docs`, `test`, or `chore`. If GitHub issue number(s) are
known, reference them in the commit body (not the title): `Refs #N`. Commit
messages explain **why**, not just what.

**3d. Execute commits.** Stage and commit each logical group using
`git add <paths>`. When a single file contains changes for different commits,
stage it with the dominant change set and note the grouping compromise in the
commit message — intra-file splitting (`git add -p`) requires interactive input
and may not be available in agent environments. Verify each commit leaves the
working tree in a valid state.

If analysis produces no clear grouping (one tangled change), fall back to a
single commit with a comprehensive message. A single honest commit is better
than artificial splitting.

### 4. Resolve PR delivery path

After commit analysis has completed, classify current `HEAD` and select exactly
one delivery path. This classification is post-commit: if step 3 created a
commit from uncommitted changes, that new commit is part of the `HEAD` being
classified. Step 4 consumes PR discovery substrate captured in step 1, then
reads branch substrate that may have changed during step 2 or step 3 from the
classification-time branch state. Run `git rev-parse HEAD` to capture the
post-commit `HEAD`. When no open PR exists, determine whether upstream tracking
exists by running
`git rev-parse --abbrev-ref --symbolic-full-name @{upstream}` at this point.
A failing upstream lookup means no upstream exists.

- **Open PR exists:** regardless of whether the branch has upstream tracking,
  classify current `HEAD` by ancestry. To classify local `HEAD`, run
  `git rev-parse HEAD` after commit analysis and compare it against the PR head
  SHA (`headRefOid`) using `git merge-base --is-ancestor` in both directions.
  The upstream tracking ref plays no role in deliverability when a PR exists;
  the fetched PR head is the ground truth.
  - If `HEAD` and `headRefOid` are the same SHA, no committed local work is
    deliverable and the existing PR state should be reported.
  - If `HEAD` is an ancestor of `headRefOid`, the local checkout is behind the
    PR. No committed local work is deliverable; report the existing PR state
    and stop.
  - If `headRefOid` is an ancestor of `HEAD`, open PR exists and deliverable
    local work exists: local commits are deliverable through the existing PR
    update path, so push to the existing PR branch. This is the normal
    review-fix path after a PR already exists.
  - If neither commit is an ancestor of the other, the local branch and PR head
    have diverged. Report the divergence and stop; do not force-push or rebase
    automatically.
- **No open PR and upstream exists:** run `git log main..HEAD` to verify that
  local commits exist ahead of the base branch. If no commits exist, no
  committed local work is deliverable; report `clean-branch-no-changes` and
  stop. If commits exist, the branch is deliverable by opening a new PR. Then
  inspect commits ahead of the branch's remote tracking ref
  (`git log @{upstream}..HEAD`). Upstream-ahead commits decide whether a push is
  needed, not whether PR creation is allowed. If upstream-ahead commits exist,
  deliver through the new PR path after pushing the branch. If no
  upstream-ahead commits exist, the already-pushed branch still needs a PR;
  deliver through the new PR path without pushing again.
- **No open PR and no upstream:** run `git log main..HEAD` to verify that local
  commits exist ahead of the base branch. If commits exist, local commits on the
  feature branch are deliverable under first-push semantics by opening a new PR
  after pushing the branch. If no commits exist, no committed local work is
  deliverable; report `clean-branch-no-changes` and stop.

### 5. Push

Use the delivery path from step 4:

- **Existing PR update path:** resolve a local remote whose effective push URL
  points at the PR head repository recorded in step 1, using shared GitHub
  remote matching. For each remote, inspect `git remote get-url --push <remote>`.
  Push the submitted commits to the PR head branch:
  `git push <head-repo-remote> HEAD:<headRefName>`.
  Do not push the local branch name to `origin` and assume that it updates the
  open PR. This push is the delivery action; after it succeeds, report this path
  as `pushed to existing PR`.
- **New PR path:** push the feature branch to origin when the delivery
  classification requires a push. If no upstream is set, run
  `git push -u origin <branch>`; if upstream exists, run `git push` when
  upstream-ahead commits exist. If no upstream-ahead commits exist for an
  upstream-backed branch, open the new PR without a push.

### 6. Create or identify PR

The `patch` capstone requires a real PR reference. Where `gh` is available
and authenticated against the remote:
- Existing PR update path: reuse the open PR reference found in step 1.
- New PR path: create the PR via `gh pr create`.

Where forge tooling is absent, the protocol cannot complete — report what was
committed and pushed locally, note that no `patch` artifact was delivered, and
stop. Do not synthesize a PR reference.

**Title** (under 70 chars):
- Single GitHub issue: use the issue title, condensed if needed. Prefix with
  conventional commit type if not already present.
- Multi-GitHub-issue: synthesize a title capturing the combined scope.
- No linked GitHub issue: derive from commit message(s).

**Body:**

```
## Summary

[1-3 bullet points: what this PR does and why]

## Changes

[Grouped description derived from commit messages]

## GitHub Issue(s)

Closes #N
[or "Refs #N" for partial progress]

## Test plan

[How to verify — derived from acceptance criteria if available]
```

**Shell-safe transport (required):**
- Build multiline Markdown body content in a file and pass it with
  `--body-file <path>`.
- Acceptable file creation patterns:
  - direct write to a temporary file
  - single-quoted heredoc redirected to a file (no interpolation)
- Never pass multiline Markdown bodies inline with double quotes (for example:
  ``gh pr create --body "...\`cmd\`..."``) because shells can evaluate
  backticks as command substitution.

Safe examples:

```bash
# Create
cat > /tmp/pr-body.md <<'EOF'
## Summary
- ...
EOF
gh pr create --title "fix(propose): shell-safe PR body handling" --body-file /tmp/pr-body.md

# Edit
cat > /tmp/pr-body.md <<'EOF'
## Summary
- updated after review
EOF
gh pr edit <pr-number-or-url> --body-file /tmp/pr-body.md
```

**Flags:**
- Do NOT use `--draft` by default. The operator invoked `submit` because the
  work is ready for review. If the operator explicitly says "draft" or "submit
  as draft," use `--draft`.

### 7. Deliver `patch`

The capstone is delivery of the `patch` artifact via the `patch` MCP tool.
`patch` is the complete latest PR state snapshot after submission, with the
same shape for both a newly opened PR and an updated existing PR. The object
below is MCP tool input, not artifact body. `instance_id` is a tool parameter
that names the artifact instance; it is extracted before validating artifact
content, becomes the workspace filename, and must not appear in the artifact
body. Runa injects `work_unit` from session context; the agent does not supply
`work_unit`. Do not write the workspace JSON file directly:

```
patch({
  instance_id: "<slug>",
  pr_reference: "<PR URL from step 6>",
  branch: "<feature branch name>",
  commit: "<head commit SHA at submission>"
})
```

Runa validates the remaining artifact body fields against the patch schema,
persists the artifact, and records it in the artifact store. Do not emit a
partial update artifact that assumes the operator already knows the surrounding
PR context.

### 8. Report

Output:
- PR URL.
- Branch name.
- Commit summary (count and brief subjects).
- GitHub issue linkage (which GitHub issues are referenced, close vs. ref).
- `patch` artifact instance_id.
- Delivery action: "opened new PR" or "pushed to existing PR."
- Next step: "Get review, then `land` when approved."

---

## Failure Policy

- **Forge tooling (`gh`) unavailable or unauthenticated:** The protocol can
  still commit and push (steps 1–5) but cannot create or identify a PR and
  therefore cannot deliver the `patch` capstone. Report what was committed and
  pushed, note the missing forge action, and stop. Do not synthesize a `patch`
  artifact without a real `pr_reference`. Remote-side failures are covered by
  the push bullets below.
- **Branch creation fails** (name collision, unresolvable dirty state): Stop
  and report. Do not force-create or silently choose an alternate name.
- **Push rejected** (remote diverged): Stop and report. Do not force-push. Do
  not rebase automatically. Commits are safely local; the operator decides how
  to reconcile.
- **Push network error:** Retry once. If still failing, report.
- **Ambiguous PR discovery:** Stop before PR head fetch, ancestry
  classification, push, or patch delivery. Report the candidate PR URLs, the
  candidate head repositories, the operator's local remotes with their
  normalized GitHub repository or sanitized non-match status, and that
  disambiguation requires exactly one local remote pointing at exactly one
  candidate PR head repository.
- **No local remote matches the PR base repository:** Stop before PR head fetch
  and ancestry classification. Report the PR URL, PR base repository, and that
  no matching local remote was found. Do not run `git merge-base` against an
  unfetched or unresolvable `headRefOid`.
- **No local remote matches the PR head repository:** Stop before push. Report
  the PR URL, PR head repository, and `headRefName`. Do not deliver a `patch`
  artifact because the PR was not updated.
- **PR head fetch or resolvability check fails:** Report the recorded PR URL and
  stop before ancestry classification. Do not run `git merge-base` against an
  unresolvable `headRefOid`.
- **`gh pr create` fails:**
  - Branch already has an open PR: treat as the existing PR update path if
    deliverable local work was pushed; otherwise report the existing PR URL and
    stop.
  - Permissions error: stop and report.
  - Other: report and stop. The branch is pushed; the operator resolves
    the cause and directs runa to re-activate `submit`. Manual forge
    intervention is outside the protocol surface.
- **PR body corruption from shell interpolation:** If generated content appears
  corrupted or command output is injected, rebuild the body in a file and
  repair using `gh pr edit --body-file <path>`. Do not retry with inline
  double-quoted multiline `--body`.
- **GitHub issue fetch fails:** Continue without GitHub issue context. Derive PR title/body
  from commits alone. Warn that GitHub issue linkage is manual.

---

## Corruption Modes

- `premature-submit`: invoking before verification. Recognition: tests not
  run, WIP markers in code (TODO, FIXME, incomplete stubs). `submit` is not a
  verification gate, but it should warn on obvious signs of incomplete work.
- `empty-submit`: nothing to submit. Recognition: clean tree, no unpushed
  commits. Report and stop.
- `split-avoidance`: dumping all changes into one commit to skip analysis.
  Recognition: single commit touching many unrelated files with a vague
  message. The analysis phase exists to prevent this.
- `orphan-pr`: no GitHub issue linkage when GitHub issues are clearly relevant. Recognition:
  branch name contains a GitHub issue number but the PR body omits it. Detect GitHub issue
  numbers from branch names automatically.
- `title-shrug`: uninformative PR title ("Update files", "Changes"). The title
  is the first thing reviewers see — it must communicate the change's purpose.
- `submit-as-land`: treating the PR as the end of the workflow. `submit` is
  the middle of the lifecycle. The report step suggests next actions explicitly.
- `shell-interpolation-corruption`: passing Markdown via inline double-quoted
  `--body` causes backtick command substitution or other shell interpolation.
  Recognition: unexpected command output in PR text, shell errors from tokens in
  the body, or missing literal Markdown. Remediation: regenerate body via file
  and use `--body-file`; repair with `gh pr edit --body-file`.

---

## Cross-References

- `take`: the opening bookend of the session lifecycle — consumes the
  selected work-unit, prepares the workspace, and produces the `claim`.
- `land`: the closing bookend — closing ceremony, merge, and work-unit
  closure after review.
- `verify`: runs before `submit`; its `completion-evidence` output is
  a required input (per `manifest.toml`).
- `document`: runs between `verify` and `submit`; its
  `documentation-record` output is a required input.
