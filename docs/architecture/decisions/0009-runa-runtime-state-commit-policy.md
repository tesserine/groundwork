# ADR-0009: Runa Runtime State Commit Policy

**Status:** Proposed — delivered for operator review with groundwork#238;
revised 2026-07-10 (wholesale-exclusion prohibition) \
**Date:** 2026-07-05

## Context

A project that runs groundwork's methodology under runa accumulates a
`.runa/` directory that runa creates and maintains. Its layout is owned by
the runtime, not this methodology — the authoritative description is runa's
[`ARCHITECTURE.md` §`.runa/` Directory Layout](https://github.com/tesserine/runa/blob/main/ARCHITECTURE.md).
The runtime creates four entries:

- **`config.toml`** — written by `runa init`: the *canonicalized* methodology
  path, plus optional logging, agent-command, transcript, and forge defaults.
- **`state.toml`** — written by `runa init`: `initialized_at` and the
  `runa_version` that initialized the project.
- **`workspace/`** — the artifact workspace. Agent-produced artifacts live at
  `workspace/{type_name}/{instance_id}.json`. This is the methodology's
  output: the contracts, plans, dispositions, and completion records a run
  produces.
- **`store/`** — the internal runtime cache. `store/{type_name}/{instance_id}.json`
  is artifact *state* (`ValidationStatus`, timestamps, content hash, schema
  hash) that `scan` reconciles *from* `workspace/`; `store/execution-records.json`
  is a singleton the runtime rewrites (atomically) after each successful run.

Groundwork had no stated policy for which of these a consuming project commits
and which it ignores, and the choice is not obvious from the layout alone. The
gap has three costs a policy resolves, and one that makes it load-bearing:

1. **Auditability** — committed artifacts are the best record of what the
   methodology produced, reasoned about, and escalated.
2. **Cross-session visibility** — committed artifacts are visible to humans
   between sessions without a forge round-trip.
3. **Merge-conflict avoidance** — `store/execution-records.json` is a singleton
   rewritten on every run; committing it guarantees a conflict on every
   parallel branch.
4. **Clean-safety** *(the load-bearing coupling)* — groundwork#518's `tidy-up`
   runs `git clean` at land termination. `git clean` (without `-x`) removes
   paths that are **untracked and unignored**, while leaving committed and
   ignored paths in place. Any `.runa/` entry the consuming repository has not
   *declared* — committed or ignored — is therefore destroyed as residue. The
   consuming repository's `.gitignore` is the single home of that declaration;
   `tidy-up` hard-codes no `.runa/` knowledge and defers to it. Until this
   policy is published and adopted, that declaration does not exist, and
   `tidy-up` is unsafe against the runtime store.

## Decision

**Commit the artifact workspace as durable project state; ignore the
machine-local runtime files and the regenerable cache — and declare *every*
`.runa/` entry so none is left as clean-able residue.** The disposition of
each entry follows one rule — *commit the generated state that matters; ignore
the regenerable or machine-local* (the generated-code pattern, `.vscode/`
selective-commit lineage) — applied to the grounded layout:

| Entry | Disposition | Why |
| --- | --- | --- |
| `workspace/` | **commit** | Durable, agent-produced project state. Not regenerable — it *is* the methodology's output. Serves auditability and cross-session visibility. |
| `store/` | **ignore** | Regenerable: reconciled from `workspace/` by `scan`; the `execution-records.json` singleton is merge-conflict-prone and its loss is non-destructive (the runtime falls back to timestamp freshness). |
| `config.toml` | **ignore** | Machine-local: the canonicalized methodology path does not resolve on another machine; agent-command and transcript settings are per-host. Recreated by `runa init`. |
| `state.toml` | **ignore** | Machine-local init metadata (`initialized_at`, `runa_version`). Recreated by `runa init`. |

The published, adoptable stanza — **complete over `.runa/`**, so that a
repository adopting it leaves no runtime entry untracked-and-unignored:

```gitignore
# runa runtime state (tesserine/runa) — policy: groundwork ADR-0009.
# Ignore the machine-local config/init files and the regenerable runtime cache.
.runa/config.toml
.runa/state.toml
.runa/store/
# .runa/workspace/ is committed as durable project state — do not ignore it.
```

This document is the single home of the policy and its rationale; the stanza
above is its canonical form. groundwork's own `.gitignore` adopts it (this
methodology is itself runa-managed when it dogfoods its own protocols); a
consuming project copies it.

**`.runa/` is never excluded wholesale — on any ignore surface.** The stanza
is deliberately entry-wise: a directory-wide `.runa/` pattern — whether in the
committed `.gitignore`, the machine-local `.git/info/exclude`, or a global
`core.excludesFile` — silently defeats the policy. It hides the committed
workspace from `git status` while the repository's declared policy reads as
adopted, so durable project state accumulates uncommitted and invisible, and
every property this policy exists for (auditability, cross-session
visibility, clean-safety) fails without a signal. This is the same
convention the wider ecosystem applies to dot-directories that carry project
state (`.github/`, `.cargo/`, selective `.vscode/`): they are preserved, not
reflexively ignored — ignore reflexes apply to caches, not to state. The
machine-local ignore surfaces are outside the repository's ability to
enforce, so the prohibition is normative: an operator or agent finding a
wholesale `.runa/` exclusion removes it as a policy defect rather than
working around it.

## Consequences

- **The completeness invariant is the property #518 depends on.** A stanza that
  declared only `store/` — the naive two-way reading — would leave `config.toml`
  and `state.toml` untracked-and-unignored, and `tidy-up`'s `git clean` would
  destroy them. The stanza declares all four, closing that class. What it does
  *not* close is a workspace artifact written *during* a run and not yet
  committed when `tidy-up` runs: a freshly-written, untracked file under a
  committed directory is still clean-able. Committing workspace artifacts
  *before* land's clean step is the land protocol's sequencing responsibility
  (groundwork#518), which defers to this policy's declaration that `workspace/`
  is committed project state; this ADR owns the declaration, not the sequencing.
- **The layout's single home is runa, and this policy is coupled to it across a
  repository boundary.** The four-entry model is grounded against runa's
  `ARCHITECTURE.md` and `libagent/src/store.rs`. If runa changes the `.runa/`
  layout — a new top-level entry, a moved file — this policy is stale and must
  be re-grounded against runa's current layout. The coupling is a cross-repo
  prose dependency, re-verified when runa's layout changes, not a CI gate: no
  cheap in-repo authority exists to consult, and a cross-repo drift gate is not
  worth its cost today (Dosed Compliance — the honest lever here is a named,
  pinned reference, not structural enforcement).
- **Idempotency is the coupled discipline.** Committing `workspace/` while
  ignoring `store/` presumes protocols are idempotent: re-running a protocol
  against committed workspace state must not depend on the discarded cache.
  groundwork#237 declares that discipline; together the two constitute
  groundwork's commitment about the artifact-store contract it expects
  consumers to honor.
- **A `runa init` that writes this stanza is a runtime follow-on, not this
  unit.** `runa init` already creates `.runa/config.toml`, `.runa/state.toml`,
  `.runa/store/`, and `.runa/workspace/` but writes no `.gitignore`. Teaching
  it to seed this stanza on setup would remove the copy step, but it is a
  change to runa's `init` command in runa's repository — filed forward there,
  outside groundwork's scope.
