---
name: survey
description: >-
  Protocol for surveying a repo, project, codebase, or responsibility area to
  determine what actually needs doing before decomposition. Use when an
  autonomous agent must decide whether work is needed, what the real exigence
  is, or how to turn an unfamiliar territory into an honest assessment instead
  of inheriting the backlog, the current architecture, or a familiar project
  pattern.
metadata:
  version: "1.0.0"
  updated: "2026-03-17"
---

# Survey

Survey is the entry point to the groundwork pipeline. Runa activates the
protocol when a `request` artifact enters the system — an external change
request, question, bug report, or feature idea. Request intake is external;
once survey produces `requirements`, runa manages the downstream cascade
through decompose and the execution-phase protocols.

Survey exists because "what needs doing here?" is the most dangerous judgment
an unsupervised agent makes. This is where anchoring, pattern-matching, and
descriptive-normative confusion do the most damage. The protocol's job is not
to produce a neat report. Its job is to force the inquiry that separates honest
situation assessment from inherited momentum.

## Goal

Produce a `requirements` artifact that gives `decompose` a grounded body of
work: the territory examined, the actual exigence within it, the reasoning for
its priority, and the alternatives that were considered and rejected.

## Central Discipline

**Survey is disciplined inquiry, not a checklist.** The steps have an order
because later judgments depend on earlier distinctions. You cannot choose an
exigence before separating descriptive truth from normative need. You cannot
recommend work before rejecting the frames that would distort it.

The depth of each step scales with the territory. A tiny repo with three open
work-units and a clear README may need only a light survey. An unfamiliar codebase
with no documentation, contested boundaries, or weak evidence needs a deeper
one. The requirement is honest coverage of the territory at hand, not ritual
completion of every step at maximum depth.

## Companion Skills

- `reckon` identifies what the territory must enable, separates that from
  what currently exists, and governs reasoning from verified constraints.
- `research` gathers evidence when the repo, system, or local docs cannot
  resolve a material unknown.

## Requirements Structure

The `requirements` artifact must make the cognitive work legible. Each field
exists for two reasons: it forces specific thinking, and it blocks a specific
failure mode.

### `surveyed-territory`

What area was examined, what boundaries define it, and what was intentionally
left outside this survey.

This forces the agent to name the actual territory instead of speaking about
"the project" in the abstract. It resists scope sprawl, scope timidity, and
the false authority that comes from making claims about areas that were never
actually examined.

### `descriptive-state`

Observed facts about what exists now: code, docs, work-units, workflows,
architecture, operator signals, and evidence gathered from the territory.

This forces observation before prescription. It resists fantasy, premature
design, and project-type pattern matching by making the agent state what is
actually present before deciding what is needed.

### `normative-needs`

What must be true that is not yet true, derived from the territory's purpose,
audience, or constraints rather than from its current implementation.

This forces the descriptive-normative split. It resists treating the current
architecture, backlog, or coding style as the definition of correctness.

### `chosen-exigence`

The one body of work that should move forward now.

This forces commitment. It resists both "fix everything" sprawl and timid
surface work by requiring a single real need, not a bag of observations.

### `priority-reasoning`

Why the chosen exigence outranks other plausible directions right now.

This forces comparative judgment rather than instinct. It resists anchoring on
the existing backlog, first-seen problem, or most familiar solution shape.

### `rejected-alternatives`

Plausible frames, fixes, or work bodies that were considered and rejected, with
reasons for rejection.

This forces dissent against the most tempting wrong answers. It resists
backlog anchoring, familiar-template projection, and the silent assumption that
the first plausible frame must be the right one.

### `recommended-work`

The bounded work package that `decompose` should turn into executable work-units.

This forces translation from assessment into action. It resists purely
descriptive reporting that never crosses into an actionable body of work.

### `out-of-scope-or-deferred`

Work noticed during survey that should not be taken forward in this assessment,
with reasons for exclusion or deferral.

This forces boundary discipline. It resists "while we're here" expansion and
keeps the assessment honest about what it is not trying to solve.

### `unknowns-or-research-needs`

Material uncertainties that still affect confidence, plus any evidence that
must still be gathered.

This forces epistemic honesty. It resists bluffing past missing evidence and
tells `decompose` where additional grounding or research may still be needed.

## Procedures

### orient-to-territory

Name the territory before judging it. Define what part of the repo, system, or
responsibility area is under examination and what signals caused the survey to
start.

Depth scales with ambiguity. In a legible small repo, this may be one paragraph
and a short exploration pass. In a large or unfamiliar system, this may require
tracing boundaries, owners, interfaces, and documentation gaps before anything
else is safe to claim.

### observe-descriptive-state

Gather evidence about what exists. Read the relevant code, docs, work-units,
artifacts, and system signals. Use `research` when local evidence is
insufficient.

Do not interpret yet. The task here is to state what is present and what is
missing, not what should happen next.

### separate-normative-needs

Use `reckon` to derive what the territory must enable, for whom, and under what
constraints. Compare that against the descriptive state.

This is the hinge of the protocol. Survey fails if descriptive truth ("this is
how the repo currently works") is allowed to masquerade as normative truth
("this is what the repo should continue doing").

### surface-candidate-exigencies

Generate the plausible bodies of work implied by the gap between descriptive
state and normative need. Include more than one candidate when the territory
permits it.

This keeps the inquiry open long enough to avoid the first plausible frame
solidifying into dogma.

### reject-distorting-frames

Interrogate each candidate for anchoring and distortion.

Ask:
- Is this just the existing backlog speaking?
- Am I accepting the current architecture as legitimate because it already
  exists?
- Am I projecting a familiar repo pattern onto this one?
- Am I trying to fix everything?
- Am I retreating to the safest visible surface work-unit?

Record the alternatives that fail this scrutiny and why they were rejected.

### choose-bounded-exigence

Select one exigence that best fits the territory's real need and current
priority. State why it wins now and what remains outside the boundary.

The output here is not "a list of interesting problems." It is a bounded
judgment about what should move forward first.

### deliver-requirements

Deliver the `requirements` artifact by invoking the `requirements` MCP tool:
the object below is MCP tool input, not artifact body. `instance_id` is a
tool parameter that names the artifact instance; it is extracted before
validating artifact content, becomes the workspace filename, and must not
appear in the artifact body. This planning-phase artifact is unscoped; runa
does not inject `work_unit`. Do not write the workspace JSON file directly.

```
requirements({
  instance_id: "<slug>",
  scope: "<purpose and boundaries — from § Requirements Structure>",
  functional_requirements: ["..."],
  non_functional_requirements: ["..."],
  constraints: ["..."],
  assumptions: ["..."],
  dependencies: ["..."]
})
```

Runa validates the remaining artifact body fields against the requirements
schema, persists the artifact under the given `instance_id`, and records it in
the artifact store.

Delivery is successful when the tool returns without error; the survey is
transmitted when the payload preserves the inquiry that produced it. Schema
validity is not substance validity — if the content hides the reasoning
behind the choices, the survey has not been transmitted even when the call
succeeds.

## Invocation Pattern

Survey triggers on a `request` artifact — an external input that enters the
system as a change request, question, bug report, or feature idea. This is the
entry point to the managed pipeline. Once `requirements` is produced, runa
manages the downstream cascade through decompose and the execution-phase
protocols.

## Corruption Modes

**Backlog anchoring.** The assessment merely restates the open work-units as "what
needs doing."
*Recognition:* Remove the work-unit list and the survey says nothing different.

**Architecture legitimism.** The assessment treats the current structure as
evidence that the structure is correct.
*Recognition:* Existing modules, boundaries, or workflows are described as
requirements without any grounding step.

**Project-type projection.** The assessment imports a familiar template for
this kind of repo instead of reading this repo.
*Recognition:* Replace the repo name with another similar project and the
assessment would still read the same.

**Scope collapse.** The survey either tries to fix everything or picks only the
nearest surface work-unit.
*Recognition:* The chosen exigence is either unbounded or trivially local.

**Descriptive-normative confusion.** What exists is reported as if it were what
must exist.
*Recognition:* The assessment cannot answer "needed for whom, and why now?"

**Artifact theater.** The artifact is structurally complete but cognitively
empty.
*Recognition:* The fields are filled, but there is no evidence of comparison,
rejection, or judgment.

## Cross-References

- `reckon`: first-principles constraint verification and principled reasoning
  for deriving normative need.
- `research`: evidence gathering when local inspection is insufficient.
- `decompose`: consumes `requirements` and turns the selected work into executable
  work-units.
- `take`: starts a session once the work-unit graph reflects the work chosen
  through survey.
