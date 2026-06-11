---
name: orient
description: >-
  Use when working in a groundwork-equipped project, at session start, task
  initiation, or any moment requiring methodology orientation or persistent
  documentation-writing guidance. Activates the full skill system as one
  connected methodology and carries the always-on documentation discipline.
metadata:
  version: "4.0.0"
  updated: "2026-06-11"
---

# Orient

Groundwork is one connected methodology, not a skill collection. Every
protocol and skill closes a specific failure mode on the path from problem
framing to shipped change. This skill is the map.

## Operating Stance

Skills are the default operating mode, not optional extras. When a skill's
trigger matches the current work, invoke it — the default is activation,
not restraint. The corruption to watch for is under-use, not over-use; the
triggers themselves provide the scope.

## Entry Point

Read the work-unit graph first. Whether starting a session, picking up
work, or orienting mid-task, the graph tells you where you are: what's in
progress, what's blocked, what's next. Agent sessions are bounded — context
windows end, agents rotate — and the work-unit graph is the persistence
layer that survives those boundaries. Work from the graph, not from memory.
See [work-unit-model.md](https://github.com/tesserine/groundwork/blob/main/docs/architecture/work-unit-model.md).

## The Shape of the Work

Two phases, connected by the work-unit artifact.

**Planning (unscoped).** An external request becomes work-units: `survey`
establishes what actually needs doing; `decompose` breaks it into
work-units with acceptance criteria and dependency edges.

**Entry.** A work-unit reaches the scoped pipeline one of two ways: newly
created by `decompose`, or materialized from an existing forge ticket by the
`acquire` skill (the "start on ticket #N" path). Either way the result is a
work-unit artifact, indistinguishable downstream, that `take` activates on.

**The scoped pipeline (per work-unit).** Seven stations carry one selected
work-unit to a landed change. The behavior contract is the spine: created
at entry, threaded unbroken to the close.

1. **`take`** — contract-first entry: prepare the workspace, frame the
   work, author the behavior contract that defines done.
2. **`plan`** — converge on a decision-complete design that maps scenarios
   to implementation steps.
3. **`implement`** — RED-GREEN-REFACTOR per scenario; no production code
   without a failing test first.
4. **`verify`** — the completion gate: fresh evidence, criterion coverage,
   documentation impact.
5. **`submit`** — deliver the verified change as an immutable, forge-neutral
   change-proposal version.
6. **`review`** — the judgment gate: evaluate against the contract; emit
   exactly one typed disposition. Needs-revision routes back through
   submit.
7. **`land`** — apply the approved version, reflect the disposition, close
   out, record completion.

Under runa, the runtime drives these stations per work-unit; an agent's job
inside any station is that station's discipline, ending at its capstone
artifact. Depth scales with the change at every station — a trivial
work-unit traverses the same path lightly; the disciplines are constant,
the dose is proportional.

Not every piece of work needs every phase: a bug with an existing work-unit
enters at the scoped pipeline; a new capability enters at planning. The
constraint is sequence — you cannot land before verifying — not
completeness.

## Cross-Cutting Disciplines

These are not stations; they engage when their trigger fires, at any stage.

- **`reckon`** — first-principles reasoning, on every generative act. Not
  step-one-once: the trigger is creation, not sequence position.
- **`contract`** — the BDD discipline: authoring the behavior contract at
  `take`, carrying traceability through every station after.
- **`work-unit-craft`** — the discipline for authoring a work-unit's tracker
  record: outcomes over prescription, so the record does not mis-steer the
  agent that reads it. Fires when a work-unit record is written or re-scoped.
- **`debug`** — root cause before fixes, whenever a failure appears. After
  3 failed fix attempts, stop and invoke `reckon` to question the
  architecture.
- **`resolve`** — structural friction resolution. When operational friction
  appears — missing tool, broken config, stale convention — stop and
  resolve it structurally before continuing; friction that exceeds
  side-quest scope becomes a work-unit. Unresolved friction compounds.
- **`research`** — external evidence when decisions depend on facts outside
  the codebase.
- **`code-review`** — the evaluation discipline `review` applies to a
  change proposal.
- **`acquire`** — entry from an existing forge ticket: reads the ticket and
  materializes the work-unit artifact `take` activates on. Fires at the
  cold-start boundary, when work begins from a ticket reference.

## Integration Principles

- **Sovereignty.** Every handoff passes outcomes — WHAT must be true —
  never implementation steps. Work-units define acceptance criteria, not
  procedure; plans define interfaces and decisions, not scripts. Prescribed
  steps that encode wrong assumptions propagate unchallenged; agent
  judgment navigates the map.
- **Records carry the delegation.** A work-unit's tracker record is the spec
  an implementing agent reads — the body is the standalone specification,
  comments are a log. When authoring or re-scoping a record, `work-unit-craft`
  provides the discipline: outcomes over prescription, and the corruption
  modes that make records mis-steer their readers.
- **Behavior traceability.** The contract from `take` is traceable at every
  station: plans link decisions to scenarios, tests prove named scenarios,
  verification reports scenario-level coverage, review judges against the
  contract, landing records what coverage shipped.
- **Documentation obligation.** User-facing changes carry documentation
  obligations; user-visible changes require a CHANGELOG entry. The
  always-on writing discipline:
  [references/documentation.md](references/documentation.md).
- **Fresh contexts for independent work.** When a plan contains independent
  tasks, dispatch fresh subagents for each — stale context from earlier
  tasks pollutes later ones. Match model capability to task complexity.

## Corruption Modes

- **Methodology as gates.** Checking off stations regardless of whether the
  work needs them, or invoking a skill because its name matched a keyword.
  The map has entry points; the constraint is sequence, not completeness.
- **Contract dropoff.** Tests pass but no one can name which scenario each
  proves; completion claims cite command output instead of behavior
  coverage.
- **Work-unit discipline failure.** Deciding what to work on from
  conversation or memory instead of the graph; starting blocked work.
- **Sovereignty violation.** Acceptance criteria that describe steps to
  perform rather than outcomes to verify; plans that read as scripts.
- **Documentation drift.** Claiming completion without checking whether the
  change affects documentation, or deferring known drift untracked.

For the connecting structure — artifacts, manifest edges, schemas, and
protocol topology — see
[connecting-structure.md](https://github.com/tesserine/groundwork/blob/main/docs/architecture/connecting-structure.md).
