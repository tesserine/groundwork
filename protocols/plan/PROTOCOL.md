---
name: plan
description: >-
  Converge from exploration to a decision-complete implementation design
  before any code changes. Fires after the behavior contract exists and
  before implement. If you are about to start coding with unresolved design
  choices, plan first.
metadata:
  version: "2.2.0"
  updated: "2026-06-17"
  origin: "Adapted from OpenAI Codex CLI (Apache-2.0). See LICENSE-UPSTREAM."
---

# Plan

Converge from exploration to a decision-complete implementation design
before modifying code. Decision-complete means the implementer makes no
design choices: approach, interfaces, data flow, edge cases, and test
strategy are all resolved or recorded as explicit assumptions.

The plan serves the behavior contract: it decides how each scenario will be
made true. A plan that cannot map its steps to named scenarios is designing
something other than the contracted work.

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

1. **Ground in the environment.** Read the contract and work-unit; search
   the entrypoints, configs, schemas, and existing implementations of
   similar behavior; trace the code paths the change will touch; note the
   patterns and utilities to reuse — and what remains unknown.

2. **Resolve intent.** State the goal and success criteria from the contract
   scenarios. Fix in-scope and out-of-scope boundaries. Surface codebase
   constraints: dependencies, API contracts, performance budgets, tests that
   must keep passing. For each remaining ambiguity: a discoverable fact is
   explored further; a genuine preference or tradeoff is decided on codebase
   evidence and recorded as an explicit assumption.

3. **Converge the design.** First reckon the design: converging a
   decision-complete design is a generative act — open the resolved
   principles corpus at `~/.groundwork/principles/`, select the principles
   that govern this design, read them, and reason the approach from them
   rather than the nearest pattern or an adjacent example (the reckon skill
   is the move). Then choose the approach (compare tradeoffs against
   the constraints when several are valid). Specify interfaces, signatures,
   and data flow. Decide handling for each edge case and failure mode.
   Define the test strategy: which scenarios become which tests, what must
   keep passing, what commands verify. Then check: does any design choice
   remain for the implementer? Resolve it or record the assumption.

4. **Record the plan.** Title; a 1–3 sentence summary; key changes grouped
   by behavior or subsystem (paths only where ambiguity is dangerous); the
   scenario-to-steps mapping; the test plan; every assumption with its
   rationale. Compress — expand only where ambiguity would cause
   implementation mistakes.

5. **Deliver the `implementation-plan`.** Invoke the `implementation-plan`
   MCP tool. The object below is MCP tool input, not artifact body.
   `instance_id` is a tool parameter that names the artifact instance; it is
   extracted before validating artifact content, becomes the workspace
   filename, and must not appear in the artifact body. Runa injects
   `work_unit` from session context; the agent does not supply `work_unit`.
   Do not write the workspace JSON file directly:

   ```
   implementation-plan({
     instance_id: "<slug>",
     summary: "<what the plan accomplishes>",
     design_decisions: [{decision: "...", rationale: "..."}, ...],
     affected_files: ["..."],
     behavior_mapping: [{scenario: "...", steps: ["..."]}, ...]
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
- `contract-detachment`: plan steps that map to no scenario — designing
  beside the contract instead of from it.

## Cross-References

- `reckon` (skill): first-principles constraint framing. A decision-complete
  design is a generative act, so reckon fires before the plan converges —
  grounding the design in the navigational principles, not pattern-matching
  the existing system or an adjacent example. Per reckon's own trigger
  (every generative act, not a sequence position); dose proportional to the
  change, the discipline constant.
- `take` (protocol): produced the behavior contract this plan serves.
- `implement` (protocol): executes this plan through RED-GREEN-REFACTOR.
- `research` (skill): external evidence when design decisions depend on
  facts outside the codebase.
