---
name: plan
description: >-
  Converge from exploration to a decision-complete implementation design
  before any code changes. Fires after the contract exists and
  before implement. If you are about to start coding with unresolved design
  choices, plan first.
metadata:
  version: "2.5.0"
  updated: "2026-07-02"
  origin: "Adapted from OpenAI Codex CLI (Apache-2.0). See LICENSE-UPSTREAM."
---

# Plan

Converge from exploration to a decision-complete implementation design
before modifying code. Decision-complete means the implementer makes no
design choices: approach, interfaces, data flow, edge cases, and test
strategy are all resolved or recorded as explicit assumptions.

The plan serves the multidimensional contract. It consults the `contract`
skill (`skills/contract/SKILL.md`) for the contract lifecycle and the
dimensions the build must serve: the behavior dimension, the documentation
dimension, and the code-quality dimension are declared as uniform typed
criteria in `contract.criteria[]`.

The plan maps every contract criterion to implementation steps, keyed by
`criterion_id`. Each criterion carries its own dimension, statement, and
check on the contract artifact; the plan consults them there rather than
restating them. A behavior criterion's check is commonly an executable
scenario or a structural, coherence, or conformance gate; a documentation
criterion's steps say how the declared documentation outcome will be met;
a code-quality criterion's steps say how the reviewer-checkable projection
will hold of the change. One mapping shape serves every dimension.

## Constraints

- `read-only-until-converged`: no mutations to repo-tracked files during
  planning. Reads, searches, builds, and tests that write only caches are
  exploration and encouraged. If the action would be described as "doing the
  work" rather than "planning the work," do not do it.
- `decision-complete`: every design choice resolved or recorded as an
  explicit assumption with rationale. Never left implicit.
- `explore-before-assuming`: eliminate unknowns by reading code, not by
  guessing. Never guess what you can read.

## Steps

1. **Ground in the environment.** Read the contract and work-unit; read
   every declared criterion — its dimension, statement, hollow delivery,
   `check_kind`, and check — from `contract.criteria[]`; search the entrypoints, configs, schemas, and existing
   implementations of similar behavior; trace the code paths the change
   will touch; note the patterns and utilities to reuse — and what remains
   unknown.

2. **Resolve intent.** State the goal and success criteria from the
   contract's declared criteria across every dimension. Name each criterion
   by its `criterion_id` and take its check as the contract states it —
   an executable scenario stays a scenario, a structural, coherence, or
   conformance gate stays a gate; never convert one check into another.
   Fix in-scope and out-of-scope boundaries. Surface codebase constraints:
   dependencies, API contracts, performance budgets, tests that must keep
   passing, documentation outcomes, and code-quality projections. For each
   remaining ambiguity: a discoverable fact is explored further; a genuine
   preference or tradeoff is decided on codebase evidence and recorded as an
   explicit assumption.

3. **Converge the design.** First reckon the design: converging a
   decision-complete design is a generative act — open the resolved
   principles corpus at `~/.groundwork/principles/`, select the principles
   that govern this design, read them, and reason the approach from them
   rather than the nearest pattern or adjacent example. This is the point
   where the reckon skill is the move. Then choose the approach (compare
   tradeoffs against the constraints when several are valid). Specify
   interfaces, signatures, and data flow. Decide handling for each edge case
   and failure mode.
   Define the test strategy: which criteria become which checks, what
   must keep passing, what commands verify, and how documentation and
   code-quality criteria are carried. Then check: does any design choice
   remain for the implementer? Resolve it or record the assumption.

4. **Record the plan.** Title; a 1–3 sentence summary; key changes grouped
   by behavior or subsystem (paths only where ambiguity is dangerous); the
   criterion-to-steps mapping covering every contract criterion; the
   test plan; every assumption with its rationale. Compress — expand only where ambiguity
   would cause implementation mistakes.

5. **Deliver the `implementation-plan`.**
   Invoke the `implementation-plan` MCP tool with one uniform
   `criterion_mapping` keyed by `criterion_id` — one mapping per contract
   criterion, the same shape for every dimension. The object below is MCP
   tool input, not artifact body.
   `instance_id` is a tool parameter that names the artifact instance; it is
   extracted before validating artifact content, becomes the workspace
   filename, and must not appear in the artifact body.
   Runa injects `work_unit` from session context; the agent does not supply `work_unit`.
   Do not write the workspace JSON file directly.

   ```
   implementation-plan({
     instance_id: "<slug>",
     summary: "<what the plan accomplishes>",
     design_decisions: [{decision: "...", rationale: "..."}, ...],
     affected_files: ["..."],
     criterion_mapping: [{
       criterion_id: "<contract criterion id>",
       steps: ["..."]
     }, ...]
   })
   ```

   Runa validates the remaining artifact body fields against the
   implementation-plan schema, persists the artifact, and records it in the
   artifact store.

## Scale

Depth scales with the change. When the approach is obvious and the change is
contained, ground quickly, record the single real decision, and deliver —
the discipline is that the decision is *recorded*, not that the document is
long. Multi-subsystem or interface-changing work earns the full convergence.

## Corruption Modes

- `imagination-planning`: designing without reading the codebase; the plan
  describes a system that does not exist.
- `premature-mutation`: editing files before the plan is decision-complete.
- `implicit-assumption`: a design choice made but not recorded — the
  implementer re-faces the same ambiguity.
- `analysis-paralysis`: exploring without converging. Three rounds of
  targeted exploration is usually sufficient; decide and move.
- `file-inventory-plan`: listing files to touch instead of behavioral
  changes. Files are detail; behavior is the contract.
- `contract-detachment`: plan steps that map to no contract criterion, or
  a declared criterion left with no mapping — designing beside the contract
  instead of from it.

## Cross-References

- `contract` (skill): owns the contract lifecycle — every dimension
  declared as uniform typed criteria, with executable scenarios and
  structural, coherence, and conformance gates as the behavior dimension's
  usual checking apparatus.
- `reckon` (skill): first-principles constraint framing. A decision-complete
  design is a generative act, so reckon fires before the plan converges —
  grounding the design in the navigational principles, not pattern-matching
  the existing system or an adjacent example. Per reckon's own trigger
  (every generative act, not a sequence position); dose proportional to the
  change, the discipline constant.
- `take` (protocol): produced validation defined in the contract dimensions
  this plan serves.
- `implement` (protocol): executes this plan through RED-GREEN-REFACTOR over
  each contract criterion the plan orders.
- `research` (skill): external evidence when design decisions depend on
  facts outside the codebase.
