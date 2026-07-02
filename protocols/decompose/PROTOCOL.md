---
name: decompose
description: >-
  The work-unit protocol. Produce `work-unit` artifacts: create, refine, and
  triage work-units, decompose epics into them, and deliver each through the
  `work-unit` MCP tool with its connector ticket handle. Close-state review
  happens here; the close itself is performed by `land`. The authoring craft
  lives in the `work-unit-craft` skill; this protocol consults it.
metadata:
  version: "1.1.0"
  updated: "2026-07-02"
---

# Decompose

`decompose` is the pipeline's work-unit surface. It creates, refines, and
triages `work-unit` artifacts, decomposes epics into them, and reviews
close-state before `land` seals the close. The authoring craft those moves
apply — outcomes over prescription, the sovereignty test, contract inputs,
body-vs-comment authority, and the corruption modes that make records
mis-steer implementing agents — lives in the
[`work-unit-craft` skill](../../skills/work-unit-craft/SKILL.md); this
protocol consults that home and owns only its own moves.

`decompose` is also Groundwork's acquisition surface: it is the sole unscoped
producer of the `work-unit` artifact. Ordinary planning reaches this protocol
when a `requirements` artifact satisfies its trigger, so requirements still
precede decomposition in the planning route. Cold-start ticket entry substitutes
that trigger with the entry reference and serves the same work-unit output
surface so the acquire discipline can read the ticket and materialize the
work-unit before any planning-phase requirements artifact exists. The manifest
therefore keeps `requirements` as the trigger, not as a `requires` precondition.

For concrete templates, see [references/templates.md](references/templates.md).
For the work-unit state model and dependency graph format, see
[`work-unit-model.md`](../../docs/architecture/work-unit-model.md).
For first-principles constraint verification before framing work-units, use
`reckon`.

## Guidelines

### Scope and sizing

**One concern per work-unit.** A work-unit that touches unrelated modules forces the
implementer to hold multiple problem contexts simultaneously and makes partial
completion ambiguous. When you notice scope creeping across boundaries, split.

**Session-sized work.** Each task work-unit should be completable in one focused
agent session — from reading context through passing verification. Oversized
work-units cause context loss mid-execution; undersized work-units create coordination
overhead that exceeds the work itself.

### Epics and decomposition

**Vertical slices with dependency graphs.** Decompose epics into independently
shippable slices, not horizontal layers. Each slice delivers observable value.
For epics with 4+ tasks, include a dependency graph showing execution layers
(see [`work-unit-model.md`](../../docs/architecture/work-unit-model.md) § Dependency
Graph Format) so implementers can parallelize independent work.

**Epic completion is recipient-facing.** An epic is complete when its output is
real for its recipient, not merely when its task list is empty. Classify the
epic by the terminal step that makes the output real:

- **capability epics** deliver operator-facing capability. Their decomposition
  includes the required component release work plus a terminal
  ecosystem-release work-unit. That terminal work-unit depends on the component
  release inputs and makes the capability public fact.
- **knowledge/spike epics** terminate in an ADR or recorded decision.
- **decomposition/planning epics** terminate in filed sub-issues.
- **process/ceremony epics** terminate in the adopted process.

Capability-epic release identity belongs to the commons release authority:
ADR-0011, ADR-0012, ADR-0014, and `ECOSYSTEM-RELEASE.md`. Decompose requires
the terminal ecosystem-release step, but does not define the manifest schema,
version choice, verification, or publication procedure.

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
6. Record contract inputs by applying `work-unit-craft`: behavior through
   criteria, documentation through recipient outcomes from `orient`, and code
   quality through the principles corpus plus any stressed universals. Consult
   `contract` for how these inputs are used downstream.
7. Identify dependencies by searching existing work-units in the tracker.
   Record each as a work-unit reference.
8. Assemble using template from `references/templates.md`. Title format:
   `<type>(<scope>): <what>`.

A structural linter is available at `protocols/decompose/scripts/issue_lint.py`
(path from the groundwork methodology root) for validating work-unit bodies
against template schemas. The `work-unit-craft` skill
carries the full authoring discipline — the sovereignty test, body-vs-comment
authority, and the corruption modes that make records mis-steer implementing
agents; consult it when authoring or re-scoping a record.

### decompose-epic

1. Reckon the epic's constraints. Verify what the epic must deliver
   against actual need — not against the requirements document's
   framing or the existing system's structure.
2. Extract deliverables — artifacts that must exist when done.
3. Classify the epic completion boundary: capability, knowledge/spike,
   decomposition/planning, or process/ceremony. If the epic mixes boundaries,
   split it or reckon the primary recipient-facing completion boundary before
   filing tasks.
4. Split into vertical slices that are independently verifiable, including the
   terminal completion work for the selected boundary.
5. Group by module boundary where it clarifies ownership.
6. Build dependency graph (Mermaid `graph TD` + layered text summary —
   see [`work-unit-model.md`](../../docs/architecture/work-unit-model.md) § Dependency Graph Format).
7. For each task, record contract inputs by applying `work-unit-craft`:
   behavior, documentation, and code quality are considered before the task is
   filed.
8. Size-check each candidate: split if oversized, merge if trivial.
9. Create task work-units in topological order (lowest execution layer first).
10. Create or update parent epic with task checklist and dependency graph.

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
4. Re-apply the contract input pass from `work-unit-craft`, preserving any
   behavior, documentation, and code quality inputs that remain true and adding
   any missing special inputs.
5. Re-verify `work-unit-craft`'s central discipline — does any criterion or
   scope statement prescribe an implementation approach?

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

Delivery is two coupled surfaces. The tracker operations the procedures above
perform — searching existing work-units, labels, stale-age review, and
parent-epic checklist updates — act on the planning home; the `work-unit` MCP
tool call below persists the execution-scoped artifact that carries the
connector handle back to it.

Deliver each `work-unit` artifact by invoking the `work-unit` MCP tool once
per delivered artifact. Every work-unit is tracker-backed. For a newly created
work-unit, first invoke the connector capability `create-ticket` operation and
carry the returned `{ id, display }` handle into the artifact body. `create-ticket`
is a first-delivery-only step: refinement never calls it, and decompose does not
adopt a pre-existing tracker ticket into a new artifact. If a tracker ticket
already exists, this delivery path must not create a second ticket for it. The
object below is MCP tool input, not artifact body. `instance_id` is a tool
parameter that names the artifact instance; it is extracted before validating
artifact content, becomes the workspace filename, and must not appear in the
artifact body. `work-unit` is a planning-phase artifact: the agent supplies the
schema fields shown below, and runa does not inject `work_unit`. Work-unit
artifact bodies have no top-level `work_unit` field and no forge identity
outside the connector handle. Do not write the workspace JSON file directly.

Use a fresh `instance_id` when creating a new work-unit. Reuse the existing
`instance_id` when refining an already-delivered work-unit artifact so artifact
identity and inbound dependency references remain stable. First MCP delivery
uses a stable id derived from the connector handle's `id`, and must populate
`handle` exactly once from the identity returned by `create-ticket`.
Subsequent updates reuse the `instance_id` established at first delivery and
carry the existing `handle` through unchanged from the previously delivered
artifact body. Do not call `create-ticket`, re-derive `handle`, or omit
`handle` during refinement; MCP delivery persists the submitted body. In this
section, "refining an existing work-unit" means refining an existing artifact,
not merely refining a tracker item.

For new tracker-backed work-units produced by `create-work-unit` or
`decompose-epic`:

```
work-unit({
  instance_id: "work-unit-<sha256-handle-id>",
  title: "<type(scope): what>",
  description: "<what needs doing and why>",
  acceptance_criteria: ["..."],
  scope: ["decompose delivery", "take framing"],
  out_of_scope: ["submit protocol", "land protocol"],
  dependencies: ["work-unit-122-artifact-store-cleanup"],
  handle: {
    id: "<connector-issued ticket identity>",
    display: "<human-readable ticket identity>"
  }
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
    id: "<existing connector handle id>",
    display: "<existing connector handle display>"
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
`issue-123`.

## Triggers

- creating or refining work-units
- decomposing large goals into executable work
- triaging or prioritizing a backlog
- reviewing work-units before closure
- planning milestones or releases

## Corruption Modes

The authoring corruption modes live in `work-unit-craft`; the modes below are
decompose's own — epic, graph, and delivery misuse.

- `kitchen-sink-epic`: an epic that accumulates loosely related work until it
  is too large to reason about or track. No clear deliverable boundary.
  *Recognition: if you cannot state the epic's done condition in one sentence,
  it is too broad.*

- `graph-omission`: an epic with 4+ tasks has no dependency graph or layered
  execution order, forcing implementers to discover sequencing by reading
  every task.
  *Recognition: if someone asked "what can I work on right now?" and you
  cannot answer without reading all task bodies, the graph is missing.*

- `refinement-as-first-delivery`: a refinement is delivered as if it were a
  first delivery — `create-ticket` invoked, a fresh `instance_id` minted, or
  `handle` re-derived for an already-delivered work-unit. The tracker gains a
  second ticket for the same work, or the artifact store gains a duplicate
  whose inbound `dependencies` still point at the stale instance.
  *Recognition: before delivering, ask "does a delivered artifact for this
  work-unit already exist?" If yes, the delivery is a refinement — reuse its
  `instance_id` and carry its `handle` through unchanged.*

## Cross-References

- `work-unit-craft` (skill): the authoring craft every procedure applies —
  the single home of record discipline and its corruption modes.
- `reckon`: first-principles constraint verification before work-unit framing,
  refinement, and epic decomposition.
- `acquire` (skill): the mirror of this protocol's create path — decompose
  creates the ticket it delivers; acquire adopts the ticket it is given and
  creates none. A ticket-quality gap acquire surfaces routes to
  `refine-work-unit` here.
- `take`: session-level prioritization and execution discipline.
- `contract` (skill): behavior framing and scenario naming discipline.
- `plan`: design convergence before implementation.
- `land`: merge-and-close completion events.
- `verify`: documentation updates as acceptance criteria for user-facing
  changes.
