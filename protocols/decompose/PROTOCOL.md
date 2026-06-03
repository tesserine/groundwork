---
name: decompose
description: >-
  Transfer problem understanding across context boundaries through well-formed
  work-units. Produce `work-unit` artifacts: creating, decomposing, refining,
  and triaging. Close-state review happens here; the close itself is performed
  by `land`.
---

# Work-Unit Craft

A work-unit transfers problem understanding across a context boundary — from the
person who sees the problem to the agent who will solve it. The agent has no
access to your context, your codebase familiarity, or your unstated assumptions.
Everything it needs must be in the work-unit.

For concrete templates, see [references/templates.md](references/templates.md).
For the work-unit state model and dependency graph format, see
[`work-unit-model.md`](../../docs/architecture/work-unit-model.md).
For first-principles constraint verification before framing work-units, use
`reckon`.

## The Central Discipline

**Work-units describe what must be true, not how to get there.**

A work-unit that says "Replace X with Y" has already made the design decision. If
that decision is wrong, the implementing agent will faithfully execute the wrong
solution — and the further the prescription travels through decomposition,
planning, and implementation, the harder it is to catch. The work-unit author's job
is to describe the problem and the desired end state. The implementer's job is
to find the path.

This is not a stylistic preference. It is the structural defense against the
most common failure mode in work-unit-driven development.

## Guidelines

### Scope and sizing

**One concern per work-unit.** A work-unit that touches unrelated modules forces the
implementer to hold multiple problem contexts simultaneously and makes partial
completion ambiguous. When you notice scope creeping across boundaries, split.

**Session-sized work.** Each task work-unit should be completable in one focused
agent session — from reading context through passing verification. Oversized
work-units cause context loss mid-execution; undersized work-units create coordination
overhead that exceeds the work itself.

### Acceptance criteria

**Criteria describe outcomes, not activities.** "Refactor the parser" is an
activity — it passes when someone did something, not when something is true.
"Parser returns typed errors for malformed input" is an outcome — it passes when
a specific observable behavior exists. Every criterion should be verifiable by
running a command or inspecting an artifact.

**Include testing and documentation expectations.** If the change needs tests,
say what kind (unit, integration, behavior). If it affects user-facing behavior,
include documentation updates as criteria. Making these explicit prevents the
implementer from treating them as optional.

### Dependencies

**Explicit and hard only.** Dependencies name other work-units that represent
true blockers — work that literally cannot proceed without the dependency being
complete. Preferred ordering is not a dependency. Soft dependencies create
false bottlenecks that serialize work unnecessarily.

### Epics and decomposition

**Vertical slices with dependency graphs.** Decompose epics into independently
shippable slices, not horizontal layers. Each slice delivers observable value.
For epics with 4+ tasks, include a dependency graph showing execution layers
(see [`work-unit-model.md`](../../docs/architecture/work-unit-model.md) § Dependency
Graph Format) so implementers can parallelize independent work.

### The work-unit as contract

**Must stand alone without external context.** A work-unit is a contract, not a
conversation. The implementer may be a different agent, in a different session,
with no access to the discussion that produced the work-unit. Summary states what
and why. Scope names concrete files or modules. Criteria are binary pass/fail.
Task work-units reference their parent epic or milestone so the work has context
in the work-unit graph. If the work-unit requires reading a Slack thread or "seeing
the earlier discussion" to understand, it is incomplete.

## Procedures

### create-work-unit

1. Reckon constraints. Before framing the work-unit, establish what is
   actually needed — verified constraints, not inherited assumptions.
   If the work-unit originated from an existing solution or implementation
   detail, separate the need from the approach.
2. Classify work-unit type (`task`, `epic`, `bug`, `spike`).
3. Write summary: what needs to exist and why. Not how.
4. Define scope with concrete files or modules.
5. Write acceptance criteria as observable outcomes — functional behavior,
   testing expectations, documentation updates where applicable.
6. Identify dependencies by searching existing work-units in the tracker.
   Record each as a work-unit reference.
7. Assemble using template from `references/templates.md`. Title format:
   `<type>(<scope>): <what>`.

A structural linter is available at `scripts/issue_lint.py` for validating
work-unit bodies against template schemas.

### decompose-epic

1. Reckon the epic's constraints. Verify what the epic must deliver
   against actual need — not against the requirements document's
   framing or the existing system's structure.
2. Extract deliverables — artifacts that must exist when done.
3. Split into vertical slices that are independently verifiable.
4. Group by module boundary where it clarifies ownership.
5. Build dependency graph (Mermaid `graph TD` + layered text summary —
   see [`work-unit-model.md`](../../docs/architecture/work-unit-model.md) § Dependency Graph Format).
6. Size-check each candidate: split if oversized, merge if trivial.
7. Create task work-units in topological order (lowest execution layer first).
8. Create or update parent epic with task checklist and dependency graph.

### define-task-boundary

A well-bounded task has:

- **Title**: verb + object + short outcome
- **Scope**: concrete files or modules touched
- **Goal**: one sentence describing the observable outcome
- **Acceptance criteria**: binary pass/fail checks describing end state
- **Test plan**: exact verification command or scenario
- **Effort**: `small`, `medium`, or `large`

### refine-work-unit

1. Reckon the work-unit's framing. Before editing, verify that the problem
   statement reflects actual need — not an inherited solution dressed as
   a requirement.
2. Diagnose: vague summary, missing scope, untestable criteria, implicit
   dependencies, oversized scope, or prescription leaking into criteria.
3. Apply targeted fixes only where weak. Keep already-strong sections unchanged.
4. Re-verify the central discipline — does any criterion or scope statement
   prescribe an implementation approach?

### triage-work-units

1. Refine non-ready work-units first.
2. Build dependency graph for the backlog.
3. Create topological execution layers.
4. Apply labels (`size:*`, module/area).
5. Flag stale work-units (no progress for 14+ days) for review. Resolution:
   resume, split, or close as wont-fix with rationale.

### review-work-unit-closure

1. Verify all acceptance criteria against implementation.
2. Check scope deviations — split unintended extra work into new work-units.
3. Update parent epic checklist.

The close event itself — marking the work-unit closed in the forge tracker —
is performed by `land` when it produces the `completion-record`. `decompose`
owns the pre-close review; `land` owns the seal.

### deliver-work-unit

Tracker operations in the procedures above — searching existing work-units,
labels, stale-age review, and parent-epic checklist updates — remain required
for `decompose`'s current forge-tracker-coupled workflow. Delivering the
`work-unit` artifact through runa's MCP tool does not replace those tracker
surfaces. Full runa-native `decompose` — where work-units live as runa
artifacts with tracker as an optional sync target — is separate future work.

Deliver each `work-unit` artifact by invoking the `work-unit` MCP tool once
per delivered artifact. For tracker-backed work-units that decompose is newly
creating, create the tracker ticket before invoking the `work-unit` MCP tool so
the artifact can use the forge-assigned ticket identity. `create-ticket` is a
first-delivery-only step: refinement never calls it, and decompose does not
adopt a pre-existing tracker ticket into a new artifact. If a tracker ticket
already exists, this delivery path must not create a second ticket for it. The
object below is MCP tool input, not artifact body. `instance_id` is a tool
parameter that names the artifact instance; it is extracted before validating
artifact content, becomes the workspace filename, and must not appear in the
artifact body. `work-unit` is a planning-phase artifact: the agent supplies the
schema fields shown below, and runa does not inject `work_unit`. Work-unit
artifact bodies have no top-level `work_unit` field and no forge-specific
identity outside `handle`. Do not write the workspace JSON file directly.

Use a fresh `instance_id` when creating a new work-unit. Reuse the existing
`instance_id` when refining an already-delivered work-unit artifact so artifact
identity and inbound dependency references remain stable. A new tracker-backed
work-unit first calls the active forge's `create-ticket` mechanic. First MCP
delivery then uses `work-unit-<N>-<short-slug>`, where `<N>` is the
forge-assigned ticket number, and must populate `handle` exactly once from the
identity returned by `create-ticket`. Non-tracker work-units omit `handle` and
first delivery uses `<short-slug>` directly. Subsequent updates reuse the
`instance_id` established at first delivery. If the artifact is tracker-backed,
subsequent updates also carry the existing `handle` through unchanged from the
previously delivered artifact body. Do not call `create-ticket`, re-derive
`handle`, or omit `handle` during refinement; MCP delivery persists the
submitted body. In this section, "refining an existing work-unit" means
refining an existing artifact, not merely refining a tracker item.

For new tracker-backed work-units produced by `create-work-unit` or
`decompose-epic`:

```
work-unit({
  instance_id: "work-unit-123-pipeline-refactor",
  title: "<type(scope): what>",
  description: "<what needs doing and why>",
  acceptance_criteria: ["..."],
  scope: ["decompose delivery", "take framing"],
  out_of_scope: ["submit protocol", "land protocol"],
  dependencies: ["work-unit-122-artifact-store-cleanup"],
  handle: {
    forge_tag: "github",
    url: "<issue URL returned by create-ticket>",
    number: 123
  }
})
```

For new non-tracker work-units produced by `create-work-unit` or
`decompose-epic`:

```
work-unit({
  instance_id: "pipeline-refactor",
  title: "<type(scope): what>",
  description: "<what needs doing and why>",
  acceptance_criteria: ["..."],
  scope: ["decompose delivery", "take framing"],
  out_of_scope: ["submit protocol", "land protocol"],
  dependencies: ["artifact-store-cleanup"]
})
```

For refinements produced by `refine-work-unit`:

```
work-unit({
  instance_id: "<existing-instance-id>",
  title: "<type(scope): what>",
  description: "<what needs doing and why>",
  acceptance_criteria: ["..."],
  scope: ["decompose delivery", "take framing"],
  out_of_scope: ["submit protocol", "land protocol"],
  dependencies: ["work-unit-122-artifact-store-cleanup"],
  handle: {
    forge_tag: "github",
    url: "<existing issue URL from the delivered artifact handle>",
    number: 123
  }
})
```

Choosing a new slug during refinement creates a duplicate artifact and leaves
inbound `dependencies` pointing at the stale work-unit instead of the refined
one.

Runa validates the remaining artifact body fields against the `work-unit`
schema, persists the artifact under the given `instance_id`, and records it in
the artifact store.
Dependency references must use canonical delivered work-unit `instance_id`
values, not tracker shorthand such as `#123`, `123`, `work-unit-123`, or
`issue-123`. For tracker-backed dependencies, first delivery uses the same
`work-unit-<N>-<short-slug>` convention. For non-tracker-backed dependencies,
use the dependency's bare `<short-slug>` `instance_id`.

## Triggers

- creating or refining work-units
- decomposing large goals into executable work
- triaging or prioritizing a backlog
- reviewing work-units before closure
- planning milestones or releases

## Corruption Modes

- `implicit-how`: implementation prescription leaks into scope or criteria.
  The work-unit says "use library X" or "replace A with B" instead of describing
  the required end state.
  *Recognition: read scope and criteria aloud — if they name tools, patterns,
  or implementation steps rather than observable outcomes, prescription has
  leaked in.*

- `activity-criteria`: criteria describe activities ("refactor", "clean up",
  "investigate") rather than outcomes. They pass when someone did something,
  not when something is true.
  *Recognition: ask "can I verify this by running a command or inspecting an
  artifact?" If no, it is an activity.*

- `dependency-blindness`: blockers exist but are not surfaced. The implementer
  discovers mid-session that prerequisite work is incomplete.
  *Recognition: before filing, ask "what must already be true for this work
  to start?" If the answer references unfinished work, that is a dependency.*

- `kitchen-sink-epic`: an epic that accumulates loosely related work until it
  is too large to reason about or track. No clear deliverable boundary.
  *Recognition: if you cannot state the epic's done condition in one sentence,
  it is too broad.*

- `premature-work-units`: filing detailed task work-units for work that depends on
  unresolved design decisions. The work-units will need rewriting when the
  decisions land.
  *Recognition: if the work-unit's scope would change based on an open question,
  the question must be answered first (spike work-unit).*

- `graph-omission`: an epic with 4+ tasks has no dependency graph or layered
  execution order, forcing implementers to discover sequencing by reading
  every task.
  *Recognition: if someone asked "what can I work on right now?" and you
  cannot answer without reading all task bodies, the graph is missing.*

## Cross-References

- `reckon`: first-principles constraint verification before work-unit framing,
  refinement, and epic decomposition.
- `take`: session-level prioritization and execution discipline.
- `specify`: behavior framing and test naming discipline.
- `plan`: design convergence before implementation.
- `land`: merge-and-close completion events.
- `document`: documentation updates as acceptance criteria for user-facing
  changes.
