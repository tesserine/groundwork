---
name: take
description: >-
  Session work initiation: select work-unit(s), prepare workspace, declare
  direction. Opening bookend of the session lifecycle — `land` is the closing
  bookend. Trigger on: 'take', 'take work', 'start session', 'start work-unit'.
---

# Take — Work Selection & Initiation

## Overview

Protocol for opening a work session: consume the selected work-unit,
prepare the repository-local workspace, and produce a `claim` that threads
all downstream artifacts.

`take` is the opening bookend of the session lifecycle:
`take` (select + prepare) → implement → `submit` (package for review) →
review → `land` (merge and close).

Plan from the work-unit graph, not from memory. Agent sessions end and context
windows close, but the work-unit graph persists — it is the only working memory
that survives across sessions.

For work-unit decomposition and boundary contracts, use `decompose`.
For first-principles design decisions, use `reckon`.

## Procedures

### session-open

#### Phase 0: Opening

The opening ceremony equips the session with everything subsequent phases
need: the methodology context that connects the protocol-and-skill system
into a coherent whole, awareness of the current workspace state, a
directional frame that guides the session, and a clean starting surface.
Each step builds on the previous — orient loads the methodology, observe
reads the workspace, frame sets direction, banish clears the path.

Follows the LBRP sequence: orient → observe → frame → banish.

##### 0a. Orient

The agent receives its operating methodology — the connected system that
makes later protocols and skills work together rather than in isolation.
`take` opens individual work sessions; `orient` establishes the methodology
those sessions operate within. If `orient` has not been loaded this
session, load it now before proceeding.

```
◈ ORIENT
Methodology: loaded
```

Implementation: invoke the `orient` skill via the Skill tool.

##### 0b. Observe

Compact workspace snapshot. This is the only status check — do not repeat these
commands in later phases.

```
◈ STATUS
Git: [clean/dirty] | Branch: [name] | Last: [commit-oneline]
```

Implementation: `git status --short`, `git log --oneline -1`,
`git branch --show-current`. Report in one block.

##### 0c. Frame

Establish the session's purpose using the Four Touches:

| Touch | Question |
|-------|----------|
| **Purpose** | Why does this session exist? |
| **Success** | What does a completed increment look like? |
| **In scope** | What boundaries contain this work? |
| **Out of scope** | What nearby work is explicitly excluded? |

The work-unit artifact is always present — runa activates the protocol on the
selected work-unit. Derive all four touches from the work-unit body: purpose
from `description`, success from `acceptance_criteria`, scope from the
work-unit's `scope` array, and out-of-scope from the work-unit's
`out_of_scope` array. When either boundary array is absent, fall back to
description-inferred framing.

```
◈ FRAME
Purpose: [one sentence]
Success: [verifiable outcome]
Scope: [in] / [out]
```

##### 0d. Banish

Evaluate workspace state (observed in 0b) against the frame (established in
0c). Clear debris so selection starts clean.

- **Clean workspace** → proceed.
- **Changes relevant to frame** → keep and note.
- **Stale or unrelated changes** → stash or discard (confirm with user before
  destructive action).

```
◈ BANISH
[CLEAN | kept: reason | stashed: reason]
```

#### Phase 1: Consume work-unit

Selection happened upstream — either by operator direction (the operator
names the work-unit and directs runa to activate `take` on it) or by
`decompose` producing the `work-unit` artifact that runa activates `take`
on. Runa is always the activator; the protocol does not select work and is
never invoked CLI-direct.

Read the injected work-unit artifact to load the context that Phase 2
preparation and Phase 3 capstone will build on. When the upstream scope
legitimately spans 2–3 cohesive work-units that share a concern boundary,
runa activates `take` on each in turn; the session may address them as a
batch and package them as one PR at `submit`.

#### Phase 2: Preparation

Set up the repository-local workspace for the selected work.

1. Ensure on `main` and up-to-date: `git checkout main`, `git fetch origin --prune`, `git merge --ff-only origin/main`.
2. Create a feature branch. The work-unit artifact is always present; what
   varies is tracker linkage and, when linked, whether scope is single or
   batched:
   - Linked, single work-unit: `issue-<N>/<slug>`
   - Linked, cohesive batch: `issues-<N>-<M>-.../<slug>` (unbounded)
   - No tracker linkage: `feat/<slug>`, `fix/<slug>`, or `chore/<slug>`

   Slug is the work-unit title — lowercase, hyphenated, truncated to 40
   chars. The `issue-` prefix on linked branch names is a repository-local
   naming convention; `<N>` encodes the work-unit's tracker identifier.
3. Resolve referenced work-units from injected session context. Runa injects
   the active work-unit and any referenced work-units needed as dependencies or
   context. If a referenced work-unit is missing from injected input, halt with
   a substrate-failure signal. Missing injected context is not benign absent
   input: `take` does not attempt retrieval through a tracker surface and does
   not proceed in a degraded state.

#### Phase 3: Claim — produce the session capstone

The capstone is delivery of the `claim` artifact. `claim` threads every
downstream artifact (behavior-contract, implementation-plan, test-evidence,
completion-evidence, documentation-record, patch, completion-record) to
the active work-unit.

Invoke the `claim` MCP tool. The object below is MCP tool input, not artifact
body. `instance_id` is a tool parameter that names the artifact instance; it is
extracted before validating artifact content, becomes the workspace filename,
and must not appear in the artifact body. Runa injects `work_unit` from session
context; the agent does not supply `work_unit`. Do not write the workspace JSON
file directly. The agent supplies `instance_id` and `scope`:

```
claim({
  instance_id: "<slug-naming-this-claim>",
  scope: "<what is being claimed from the work-unit in this session>"
})
```

The `scope` field captures the session's starting direction — what the
agent intends to accomplish from this work-unit. It is a direction, not a
rigid prediction; implementation will sharpen it. Name nearby work
intentionally excluded inline in the scope statement.

Runa validates the remaining artifact body fields against the `claim` schema,
persists the artifact, and records it in the artifact store. The agent does not
write files, construct filenames, or supply `work_unit`.

### session-close

1. Reach a stable checkpoint (done increment or explicit WIP note).
2. Update work-unit state and leave a concise progress comment on the GitHub issue.
3. Record decisions, blockers, and the exact next step.
4. Ensure any follow-up work is represented as GitHub issue(s).
5. Sync workspace and close.

## Key Terms

Brief definitions for self-contained use. See
[`work-unit-model.md`](../../docs/architecture/work-unit-model.md) for the full treatment.

- **Work-unit graph**: the set of open work-units and their dependency edges — the live
  map of what remains and what blocks what.
- **Unblocked**: a work-unit whose hard dependencies are all closed.
- **Execution layer**: a set of work-units that share no mutual dependencies and can
  be worked in parallel once their shared ancestors are closed. Layer 0 has no
  dependencies; layer 1 depends only on layer 0; and so on.
- **Session-sized**: a work-unit that one agent can complete — from reading context
  through passing verification — in a single focused session.
- **Work-unit batch**: 2-3 cohesive work-units addressed together when they share a
  concern boundary and their combined scope is still session-sized.

## Operating Principles

- **Forge tracker is the source of truth.** Planning state lives in work-unit
  records in the active forge, not local task trackers or agent memory.
  Sessions end; the graph doesn't. Forge tracker state and comments reflect
  actual implementation state — inaccurate state is planning debt.
- **Direction over prediction.** Capture starting direction at session open.
  Goals sharpen through implementation — rigid upfront done conditions are
  premature precision. The closing handoff matters more than the opening
  prediction.
- **One session, one increment.** Commit to one independently verifiable
  increment. Fewer, sharper goals beat broad, vague activity — this keeps
  work finishable and reviewable.
- **Dependencies are hard blockers.** Do not start work whose dependencies are
  still open — blocked work produces partial results that complicate the graph.
- **Every session closes with a handoff.** Either finish the increment or
  clearly frame unfinished state. End with an honest state update and a
  concrete, actionable next step. The next session (same or different agent)
  should be able to pick up without guessing.
- **Next actions are executable.** Each next action names an artifact, a command,
  and a done condition — not a vague intention.
- **Prioritize by impact.** Rank by value delivered, time criticality, and
  unblock leverage (how much downstream work this frees), weighed against
  expected effort.

## Corruption Modes

- `recency-drift`: picking last-touched work instead of highest leverage.
- `scope-creep`: crossing concern boundaries mid-session.
- `blocker-bypass`: beginning blocked work anyway.
- `state-lag`: forge tracker state not reflecting real implementation state.
- `open-loop-close`: ending session without a concrete next step.
- `skip-preparation`: jumping from selection to implementation without setting
  up a feature branch — loses workspace isolation and makes `submit` harder.

## Cross-References

- `submit`: the next lifecycle phase — commit, push, and PR creation after
  implementation.
- `land`: the closing bookend — closing ceremony and mechanical merge after
  review. `take`'s opening ceremony (orient, observe, frame, banish) prepares
  the agent for work; `land`'s closing ceremony (gather, verify, review, seal)
  prepares the work for delivery. Parallel structure, inverse direction.
- `decompose`: decomposition, work-unit boundaries, acceptance criteria contracts.
- `reckon`: validate assumptions before committing to an approach.
- `specify`: behavior-first contract definition for implementation increments.
- `orient`: the methodology map — activates the connected system of
  protocols and skills that `take` operates within. Loaded during
  orient (Phase 0a).
- Opening ceremony pattern adapted from LBRP (`aiandi-dev-environment`) —
  internalized, no runtime dependency.
