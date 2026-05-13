---
name: plan
description: >-
  Use when an implementation task needs design convergence before code
  changes — multiple valid approaches exist, scope is unclear, or
  modifications cut across multiple files or subsystems. Use this before
  any implementation that changes interfaces, touches multiple subsystems,
  or where the approach isn't obvious. If you're about to start coding
  without a clear design, plan first.
metadata:
  version: "1.1.0"
  updated: "2026-03-08"
  origin: "Adapted from OpenAI Codex CLI (Apache-2.0). See LICENSE-UPSTREAM."
---

# Plan

Converge from exploration to a decision-complete implementation design before
modifying code. A decision-complete plan leaves no design choices to the
implementer — every approach, interface, data flow, edge case, and test
strategy is resolved.

For first-principles constraint framing, use `reckon`.
For behavior contracts, use `specify`.
For executable work-unit decomposition after design convergence, use
`decompose`.

## Goal

Produce a plan detailed enough that a separate agent could implement it
without making any design decisions.

## Constraints

- `read-only-until-converged`: do not modify repo-tracked files during
  planning. Exploration — reads, searches, static analysis, dry-runs,
  builds, tests that write only to caches or build artifacts — is allowed
  and encouraged. Mutations — edits, codegen, formatters that rewrite
  files, patches — are not. When in doubt: if the action would be described
  as "doing the work" rather than "planning the work," do not do it.

- `decision-complete`: the plan must resolve every design choice — approach,
  interfaces, data flow, edge cases, test strategy. If the implementer
  would need to decide something, the plan is not done.

- `explore-before-assuming`: eliminate unknowns by reading code, not by
  guessing. Search relevant files, inspect entrypoints, confirm current
  implementation shape before forming any opinion.

- `assumptions-are-explicit`: when exploration cannot resolve an unknown,
  decide with rationale and record it as an explicit assumption. Never
  leave a design choice implicit.

## Procedures

### phase-1-ground-in-environment

Explore the codebase to build a concrete understanding of current state.
Without this, plans describe imagined systems that collide with the actual
code.

1. Read the work-unit, task, or request to identify what must change.
2. Search for relevant files: entrypoints, configs, schemas, types,
   manifests, docs, and existing implementations of similar behavior.
3. Trace the code paths that the change will touch or interact with.
4. Identify existing patterns, utilities, and conventions to reuse.
5. Note what you still do not know after exploration.

### phase-2-resolve-intent

Clarify what the change must achieve and what is out of scope. Without
intent boundaries, every approach looks equally valid and trade-offs
cannot be evaluated.

1. State the goal and success criteria derived from the work-unit and
   exploration.
2. Identify in-scope and out-of-scope boundaries.
3. Surface constraints from the codebase: dependencies, API contracts,
   performance budgets, existing tests that must keep passing.
4. For each remaining ambiguity, classify and resolve:
   - **Discoverable fact** (repo/system truth): explore further. Search
     configs, manifests, entrypoints, schemas, types. Never guess what
     you can read.
   - **Preference or tradeoff** (not discoverable): choose the option best
     supported by codebase evidence, record it as an explicit assumption
     with rationale.

### phase-3-converge-implementation

Design the implementation until decision-complete. This is where multiple
valid approaches collapse into a single chosen design — without convergence,
the implementer re-opens every trade-off the planner evaluated.

1. Choose the approach. When multiple valid approaches exist, compare
   trade-offs against the constraints from phase 2 and select one.
2. Specify interfaces: APIs, schemas, function signatures, data flow.
3. Identify edge cases and failure modes. Decide handling for each.
4. Define the test strategy: existing tests to preserve, new tests to
   write, verification commands to run.
5. Note any migration or compatibility concerns.
6. Decision-completeness check: does the plan leave any design choice
   to the implementer? If yes, resolve it or record an explicit
   assumption with rationale.

### write-plan

Record the converged design. Include enough detail to prevent
implementation mistakes, no more — expand only where ambiguity is
dangerous.

1. **Title** — what this plan achieves.
2. **Summary** — 1-3 sentences on the change and its rationale.
3. **Key changes** — grouped by subsystem or behavior. Mention paths
   only when needed to prevent ambiguity. Compress related changes into
   high-signal bullets. Reference existing patterns, utilities, and
   conventions found during exploration.
4. **Test plan** — how to verify correctness end-to-end.
5. **Assumptions** — every unresolvable unknown with rationale for the
   chosen default.

Omit repeated repo facts and edge cases that cannot cause implementation
mistakes.

### deliver-plan

Deliver the `implementation-plan` artifact by invoking the
`implementation-plan` MCP tool. The object below is MCP tool input, not
artifact body. `instance_id` is a tool parameter that names the artifact
instance; it is extracted before validating artifact content, becomes the
workspace filename, and must not appear in the artifact body. Runa injects
`work_unit` from session context; the agent does not supply `work_unit`. Do not
write the workspace JSON file directly:

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

## Corruption Modes

- `imagination-planning`: designing without reading the codebase first.
  The plan describes a system that does not match the actual code.
- `premature-mutation`: editing files before the plan is decision-complete.
  Implementation starts leaking into the planning phase.
- `implicit-assumption`: making a design choice without recording it.
  The implementer will face the same ambiguity the planner avoided.
- `analysis-paralysis`: exploring indefinitely without converging. Three
  rounds of targeted exploration is usually sufficient. Decide and move.
- `file-inventory-plan`: listing every file to touch instead of describing
  behavioral changes. Files are implementation detail; behavior is the
  contract.
- `incomplete-plan`: leaving a design choice unresolved ("TBD", "decide
  later", "depends"). Either resolve it or record an explicit assumption
  with rationale.

## Cross-References

- `reckon`: first-principles constraint framing — runs before plan when
  the problem space itself is unclear.
- `specify`: behavior contract — provides the behavior statements the plan
  must implement.
- `take`: work initiation — selects which work-unit to plan for and prepares the session.
- `decompose`: executable work-unit decomposition and work-unit quality —
  turns a decision-complete design into agent-executable work-units with
  binary acceptance criteria.
