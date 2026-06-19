---
name: work-unit-craft
description: >-
  Use when authoring or re-scoping a work-unit's tracker record — filing
  new work-units during decompose, rewriting a record's body after a
  pivot, or reviewing a record before delegation. The discipline for
  writing records that transfer problem understanding across a context
  boundary: outcomes over prescription, the body as the standalone spec,
  and the corruption modes that make records mis-steer the agents who
  read them.
metadata:
  version: "1.1.0"
  updated: "2026-06-19"
  origin: >-
    Adapted from pentaxis93/with-claude
    _shared/methodology/issue-craft.md (internal), renamed and
    revoiced forge-agnostically for groundwork.
---

# Work-Unit Craft

A work-unit's tracker record transfers problem understanding across a context
boundary — from the author who sees the problem to the agent who will solve
it. The implementing agent has no access to the author's context, codebase
familiarity, or unstated assumptions. Everything it needs must be in the
record. Forges name the record differently — GitHub says issue, SourceHut
says ticket — the craft is the same on every forge.

## The Central Discipline

**Records describe what must be true, not how to get there.**

A record that says "replace X with Y" has already made the design decision.
If that decision is wrong, the implementing agent will faithfully execute the
wrong solution. The author's job is to describe the problem and the desired
end state. The implementer's job is to find the path.

This is not a stylistic preference. It is the structural defense against the
most common failure mode in work-unit-driven development.

## Ground the Record With Reckon

Before shaping the record, use `reckon` as the cognitive process that
establishes the verified constraints the record will state. `reckon` owns how
those constraints are grounded; this craft owns the record shape that carries
them across the delegation boundary.

## The Sovereignty Test

Before writing any record content, ask:

> **Is this a constraint the implementer must satisfy, or a decision the
> implementer should make?**

- **Constraints** belong in the record: what must be true, what must not
  change, which artifact types to use, what boundary conditions exist.
- **Decisions** belong to the implementer: which files to change, what
  log level each call site should use, how to structure the code, what
  order to work in.

The hardest violations to catch feel like thoroughness. A per-file migration
inventory, a mapping of call sites to log levels, an enumeration of every
function that needs updating — these feel like being helpful. They are
prescription. The implementer will read the codebase and find these things
with full context. The author cannot have that context and will prescribe
from a snapshot.

**The test:** Remove the detail. Do the acceptance criteria still define
what done looks like? If yes, the detail was prescription. If no, it was a
constraint that needs to be expressed differently — as an outcome, not an
inventory.

## Milestone Discipline

Where the forge provides milestones, they are optional release-tracking
tools: when work is aimed at a release and certain work-units must be
guaranteed into it, attach those records to that milestone — release scope
then becomes a query on the milestone field, not a reading exercise through
record bodies.

Much work is not release-shaped. A fix realized and implemented, an
improvement that simply wants to exist — these answer no "which release
needs this?" question. File them with no milestone; they are swept naturally
into whatever release ships next. Do not manufacture a milestone to satisfy
a form.

When a work-unit *is* release-scoped, the milestone field is the answer to
"when." A prose statement in the body — "target for next release," "after
the migration lands" — does not replace it, because prose is invisible to
release-scope queries.

## Label Discipline

Every record needs at least one label that classifies the work. Labels make
the work-unit graph queryable by category — "what bugs are open?" or "what
docs work is pending?" becomes a filter, not a reading exercise.

**Labels must discriminate.** A label applied to every record in the tracker
provides no signal; it is a boilerplate marker, not a classification. If
every open record carries `enhancement`, the label might as well not exist —
the triager learns nothing from seeing it.

**The working test:** if every record in the tracker has the same label, the
label isn't doing its job. Either the taxonomy is too coarse (one bucket for
everything), or records are being default-tagged by habit.

**At creation time, choose a label that distinguishes this work from other
work in the tracker.** The specific taxonomy is project-level — small
projects may need only type categories (feature, bug, chore, docs, refactor,
technical debt), larger projects may want domain or priority dimensions too.
The discipline is that the chosen label carries information, not that it
conforms to a prescribed set.

**The check before closing the authoring pass:**

- Does this record carry at least one label?
- Does the label actually classify the work, or is it the tracker's default
  bucket? If the latter, a more specific label exists or needs to exist.
- If no fitting label exists in the tracker, creating one is a governance
  decision — not an ad-hoc improvisation. Ad-hoc label creation produces
  taxonomy drift (`bug`, `Bug`, `bug-fix` coexisting).

*Recognition:* when you find yourself tagging every record with the same
label because "it fits," the label isn't the problem — the taxonomy is.
Either the project needs more label types, or labels aren't being used as
intended in this tracker.

## The Body Is the Spec; Comments Are a Log

A tracker record has two structurally different surfaces, on every forge,
and using them well is not optional polish — it determines whether a
delegated agent reads the right instruction.

- **The body** is a single, editable field. Editing it *replaces* the
  previous content in place. It is the record's authoritative
  specification — the one statement of what must be true now.
- **Comments** are an append-only, chronological log. They accumulate;
  they cannot replace each other or the body; they are read in sequence
  after the body.

An implementing agent consumes the record as **body plus all comments
together** — forge clients return both. It has no way to know which comment
is still live and which was superseded three pivots ago. So:

> **The body must be a complete, standalone specification that is correct
> on its own. Comments must never carry live direction that contradicts
> the body.**

When a work-unit is re-scoped — and multi-turn reckoning routinely re-scopes
work-units — **the correction goes into the body by editing it to a coherent
standalone statement.** It does *not* go in as a new comment layered on top
of a now-stale body. A record's authoritative state must be readable from
the body alone, because a fresh reader (or a delegated agent) reconstructs
intent from the body first and is actively mis-steered by a comment trail
that records every superseded direction as if it were current.

Comments are legitimately for: progress reports, grounding findings,
verification results, dependency signals, and a record that a decision was
*made* — never for the decision's current content, which belongs in the
body. If a comment's direction is later superseded, either it is harmless
history (a finding that still holds) or it must be explicitly marked
superseded so it cannot be read as live.

## Corruption Modes

### stale-comment-direction

The record's body has been re-scoped, but earlier comments carrying the old
direction remain unmarked. A delegated agent reads body + comments, sees the
superseded direction in the comment trail, and reconstructs it as live —
proposing or choosing the very shapes the body discarded.

This is the multi-turn analogue of `governance-narrative`: that mode is
about not narrating the reasoning journey *in the body*; this mode is about
not leaving the reasoning journey's *discarded conclusions* alive *in the
comments*, where they outrank, in an agent's reading, the body that
superseded them.

*Recognition:* After re-scoping a work-unit, read it the way the agent
will — body, then every comment in order. Does any comment state a direction
the body no longer holds? If so, the agent will see a contradiction and may
follow the comment.

*The test:* Could a fresh agent, reading body + all comments, come away
believing the work-unit wants something the current body rejects? If yes,
the body is not standalone, or a comment needs a superseded marker.

*The fix:* (1) Edit the body to a coherent standalone spec that states its
own authority and what the single next action is. (2) Mark every comment
carrying superseded direction with an explicit banner (`SUPERSEDED — the
record body is the single source of truth`), keeping genuinely-still-valid
findings flagged as such. Do not let a record's truth be a diff the reader
must compute across body and comment history.

*Learned in the field: a record was re-scoped to grounding-first in the
body, but three earlier comments carried discarded design directions. The
delegated agent read the comment trail and came back asking the operator to
choose between two of the discarded shapes — having never seen the body's
"ground first, choose nothing" as the live instruction, because the comments
contradicted it.*

### implicit-how

Implementation prescription leaks into scope or criteria. The record says
"use library X" or "replace A with B" instead of describing the required end
state.

*Recognition:* Read scope and criteria aloud — if they name tools, patterns,
or implementation steps rather than observable outcomes, prescription has
leaked in.

*Exception:* A governance decision that constrains the solution space is not
prescription — it is a constraint. "Use tracing, not log" is a governance
decision about which dependency to adopt. "Add tracing to
runa-cli/src/main.rs line 75" is prescription about where to put it.

### what-invention

The record invents constraints that don't exist in the problem. Unlike
implicit-how (which prescribes implementation), this mode creates
requirements — it passes the sovereignty test because constraints belong in
records, but the constraints are fabricated rather than grounded.

Records are seeds for agent execution. The agent faithfully builds from what
the record says. An invented constraint propagates through the plan into the
implementation with perfect fidelity, and looks locally correct at every
layer because each layer reproduces what it was given.

*Recognition:* For each constraint and acceptance criterion, ask "does this
exist in the problem, or did I create it?" If the problem statement is "runa
targets Linux" and the criterion says "distinguishes between cross-platform
compilation and Linux-targeted live execution," the distinction was
invented — the problem has no tiers to distinguish.

*Learned in the field: a record said "runa targets Linux" but the acceptance
criteria invented a multi-tier platform support contract. The implementing
agent built its entire plan around that distinction. Three iterations to
trace the contamination back to the record.*

### negative-criteria

Acceptance criteria state what must *not* exist or what must *not* happen,
rather than what must be true. The author has established positive criteria
that already imply the absence, then adds a negative criterion that feels
like closing the loophole.

The implementing agent treats every criterion as a first-class requirement
and designs tests around it. A negative criterion — "no code path does X" —
produces tests for the absence of behavior: assertions that no function is
called, that no iteration occurs, that no pattern exists in the source.
These tests are brittle, test implementation rather than behavior, and break
on any refactor. Worse, the agent may restructure working code to make the
negative criterion more provable, introducing complexity that serves the
test rather than the system.

*Recognition:* For each criterion, ask: "Is this stating what must be true,
or what must not be true?" If negative, check whether the positive criteria
already imply the absence. If they do, the negative criterion is redundant
and harmful. If they don't, the positive criteria are incomplete — fix them
rather than adding a negative.

*The test:* Remove the negative criterion. Can the positive criteria still
be satisfied by an implementation that has the unwanted behavior? If no, the
negative was redundant. If yes, strengthen the positive criteria.

### activity-criteria

Criteria describe activities ("refactor", "clean up", "investigate") rather
than outcomes. They pass when someone did something, not when something is
true.

*Recognition:* Ask "can I verify this by running a command or inspecting an
artifact?" If no, it is an activity.

### execution-inventory

The record includes an inventory of things the implementer will discover
through normal execution — file lists, function enumerations, call counts,
per-item classifications. This is the failure mode that feels most like
helping.

*Recognition:* Ask "did I produce this by reading the codebase?" If yes, the
implementer will do the same reading with better context. The inventory
belongs in their session, not in the record.

### governance-narrative

The record includes a "Context" or "Background" section that narrates the
authoring session's reasoning journey — the analogy that sparked the
insight, the audit that surfaced the problem, the sequence of realizations
that led to the architectural decision. The decision itself is already
stated elsewhere in the record. The narrative served the authoring session;
the implementer needs the decision, not its derivation.

This corruption mode is driven by the same urge as execution-inventory — the
author just did hard thinking and wants to preserve it. But a record is a
delegation, not a transcript. The implementer orients from the problem
statement and the governance decisions, not from the story of how those
decisions were reached.

*Recognition:* For each section, ask: "Does the implementer need this to
understand what must be true, or does it explain how the author arrived at
what must be true?" If the latter, it belongs in session notes, not the
record.

*The test:* Remove the section. Can the implementer still orient, understand
the problem, and verify acceptance criteria? If yes, the section was
governance narrative.

*Exception:* A brief predecessor reference is not governance narrative — it
is a dependency signal. "Predecessor: #118" orients the implementer to
related work. A paragraph explaining how the #118 review cycle led to the
current insight is narrative.

### premature-record

Filing a *detailed* record — one that presents itself as a complete spec —
for work whose scope still depends on unresolved design decisions. The
record *looks* plannable but will need rewriting when the decisions land,
and an agent may plan against the stale shape before the rewrite.

*Recognition:* A record carries full acceptance criteria and a worked body,
but its scope would change based on an open question. The body claims a
resolution the work has not reached.

*The honest form:* capturing unresolved-scope work is legitimate and
necessary — the honest form *declares* its unreadiness instead of hiding it.
In groundwork, that is a `spike` work-unit: the open question becomes the
work, and the detailed record is filed only after the spike resolves it. The
defect is masquerading as specced while unresolved, not the mere fact of
unresolved scope.

### dependency-blindness

Blockers exist but are not surfaced. The implementer discovers mid-session
that prerequisite work is incomplete.

*Recognition:* Before filing, ask "what must already be true for this work
to start?" If the answer references unfinished work, that is a dependency.

## What Belongs in a Record

- **Summary:** What needs to exist and why. Not how.
- **Governance decisions:** Technical choices made at the governance level
  that constrain the solution space (e.g., which dependency, which
  architectural pattern, which boundary).
- **Constraints:** What must remain true, what must not change, what
  boundary conditions exist.
- **Acceptance criteria:** Observable outcomes — functional behavior,
  testing expectations, documentation updates. Binary pass/fail.
- **Dependencies:** Work-unit references that represent true blockers.

## What Does Not Belong in a Record

- Per-file change inventories
- Implementation step sequences
- Log level or error classification mappings
- Code structure recommendations
- Negative criteria whose absence is already implied by positive criteria
- Governance reasoning narrative (how the decision was reached)
- Anything the implementer will determine by reading the codebase
- Live direction in comments that contradicts the body — when re-scoping,
  edit the body to a coherent standalone spec and mark superseded comments,
  rather than layering a new direction comment on a stale body

## Metadata at File Time

- **Label (required):** at least one label that discriminates this
  work-unit's category from other work in the tracker. A default bucket
  applied to everything carries no signal.
- **Milestone (optional, where the forge provides them):** attach the target
  release when the work-unit is release-scoped; otherwise leave it off. See
  Milestone Discipline.

## Cross-References

- `decompose`: the protocol where work-unit records are authored —
  `create-work-unit` and `decompose-epic` apply this craft; the structural
  linter at `protocols/decompose/scripts/issue_lint.py` (path from the
  groundwork methodology root) validates record bodies against template
  schemas.
- `reckon`: establishes the verified constraints a record states; fire it
  before framing the work-unit.
- [`docs/architecture/work-unit-model.md`](../../docs/architecture/work-unit-model.md):
  the work-unit state model and dependency graph format the record
  participates in.

---

*The most dangerous record is structurally correct — scope, criteria,
checkboxes — but prescribes the wrong solution. An implementing agent will
faithfully execute the prescription. The discipline is not in the structure.
It is in what the structure contains.*
