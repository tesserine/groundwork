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
  version: "1.1.0"
  updated: "2026-07-02"
---

# Survey

Survey is the entry point to the groundwork pipeline. Runa activates the
protocol when an `intent` artifact enters the system — an external change
request, question, bug report, or feature idea. Intent intake is external;
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

The `requirements` artifact is defined by its schema:
`schemas/requirements.schema.json` is the single home of its fields, and this
section derives from it — a reader of the section and the schema sees one
artifact. Each field must make the cognitive work legible: it carries a
specific judgment out of the inquiry, and it blocks a specific failure mode.

### `scope`

Purpose and boundaries of the work: the territory examined and the bounded
exigence chosen within it, with what falls outside stated as a boundary.

This forces the survey to name the actual territory and commit to one body of
work inside it. It resists scope sprawl, scope timidity, false authority over
areas never examined, and the "fix everything" survey that never chooses.

### `functional_requirements`

What the system should do — discrete items, each a normative need derived from
the territory's purpose rather than from its current implementation.

This forces translation from assessment into decomposable behaviors. It
resists purely descriptive reporting that never crosses into an actionable
body of work.

### `non_functional_requirements`

The qualities the work must hold — performance, security, reliability, and
their kin — stated as needs, not as descriptions of current behavior.

This forces qualities to be derived from purpose and audience. It resists
treating whatever the system currently exhibits as the definition of adequate.

### `constraints`

Technical and business boundaries the work must respect: the real ones —
physics, contract, mandate, platform.

This forces the split between genuine boundaries and inherited convention. It
resists precedent-as-constraint and the architecture legitimism that smuggles
the current structure in as a requirement.

### `assumptions`

What is taken as given: the load-bearing beliefs the survey did not verify,
stated where `decompose` can see them.

This forces epistemic honesty about the unverified. It resists bluffing past
missing evidence and building silently on unknowns — a material uncertainty
either becomes an explicit assumption here or sends the survey back to
`research`.

### `dependencies`

External dependencies affecting decomposition: what outside the territory the
work waits on or touches.

This forces the outward edges to be named before units are cut. It resists
work-unit graphs that discover their blockers at execution time.

The inquiry that fills these fields — orienting to the territory, separating
descriptive state from normative need, surfacing and rejecting distorting
frames, choosing a bounded exigence — is owned by the Procedures below. The
fields carry that inquiry's judgment; they do not replace it, and a
schema-valid artifact produced without the inquiry is artifact theater (see
Corruption Modes).

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
the object below is MCP tool input, not artifact body.
`instance_id` is a tool parameter.
It names the artifact instance and becomes the workspace filename.
It must not appear in the artifact body.
This planning-phase artifact is unscoped; runa does not inject `work_unit`.
Do not write the workspace JSON file directly.

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

Survey triggers on an `intent` artifact — an external input that enters the
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
