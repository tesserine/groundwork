---
name: take
description: >-
  Contract-first entry of the scoped pipeline: receive an already-selected
  work-unit, prepare the workspace, establish the behavior contract that
  defines done, and carry that contract through the pipeline to a submitted
  change. The contract produced here is the spine every downstream protocol
  carries to land; until the runtime sequences the stations autonomously,
  take carries it. Trigger on: 'take', 'take work', 'start work-unit'.
metadata:
  version: "3.1.0"
  updated: "2026-06-17"
---

# Take — Contract-First Entry

Take opens work on a single work-unit. Selection happened upstream — the
work-unit artifact exists and runa activates take on it, having arrived
either from `decompose` (a newly created work-unit) or from the `acquire`
skill (materialized from an existing forge ticket). Entry's real job is to
stand on prepared ground and state, precisely and verifiably, what will be
true when this work is done.

That statement is the `behavior-contract`: development here is
behavior-driven, and it begins at the door. The contract authored in this
protocol threads unbroken through `plan`, `implement`, `verify`, `submit`,
`review`, and `land` — every later stage either refines it, executes it,
proves it, or records it.

## Steps

1. **Orient.** Load the methodology if not already loaded this session —
   invoke the `orient` skill. It connects the protocols and skills into one
   system and carries the always-on documentation discipline.

2. **Prepare the workspace.** Establish clean, isolated ground: a workspace
   free of unrelated changes, synced to the current base, on a feature branch
   named for this work-unit, with the tracker reflecting that the work-unit
   is claimed. Outcomes and conventions:
   [references/workspace.md](references/workspace.md).

3. **Frame the work.** Read the injected work-unit. Derive the frame from its
   fields — purpose from `description`, success from `acceptance_criteria`,
   boundaries from `scope` and `out_of_scope` (fall back to
   description-inferred boundaries when the arrays are absent). Do not start
   work whose `dependencies` are still open; a blocked work-unit is a
   substrate signal, not an invitation.

4. **Author the behavior contract.** Refine each acceptance criterion into
   one or more sentence-named Given/When/Then scenarios — the executable
   definition of done. The `contract` skill is the authoring discipline:
   behavior before mechanics, one behavior per scenario, names that read as
   specification. Invoke it. Where a criterion cannot be expressed as an
   observable behavior, that is a defect in the work-unit — resolve it
   against the work-unit's intent, and record the interpretation in the
   scenario's `criterion` reference rather than silently guessing.

5. **Deliver the `behavior-contract`.** Invoke the `behavior-contract` MCP
   tool. The object below is MCP tool input, not artifact body. `instance_id`
   is a tool parameter that names the artifact instance; it is extracted
   before validating artifact content, becomes the workspace filename, and
   must not appear in the artifact body. Runa injects `work_unit` from
   session context; the agent does not supply `work_unit`. Do not write the
   workspace JSON file directly:

   ```
   behavior-contract({
     instance_id: "<slug>",
     title: "<human-readable contract title>",
     scenarios: [{
       name: "<sentence-named scenario>",
       criterion: "<acceptance criterion this refines>",
       given: "<initial context>",
       when: "<action or event>",
       then: "<observable outcome>"
     }]
   })
   ```

   Runa validates the remaining artifact body fields against the
   behavior-contract schema, persists the artifact, and records it in the
   artifact store. Where no runtime is present to accept the MCP tool — a
   checkout that is not an initialized runa project — author the same
   contract as a committed workspace artifact (the behavior-contract JSON,
   or the work-unit issue if there is no workspace store) so the spine
   exists and binds the test-first cycle either way.

6. **Carry the contract through to a submitted change.** Take does not end
   at contract delivery. When the runtime sequences the pipeline
   autonomously, it advances the work station to station; until then, take
   carries it — that bridging is take's job at the door. With the behavior
   contract as the spine, proceed through the stations in order, invoking
   each: `plan` (a decision-complete design against the contract),
   `implement` (build it test-first — every scenario is a failing test
   before its code; `contract-after-code` is forbidden), `verify` (every
   scenario green, the change sound), `submit` (deliver the change for
   review). Advance through the boundaries; do not stop at one waiting to
   be carried. Review and land — the independent-judgment gate and the
   governance close — follow once every scenario is green and verify
   passes.

## Scale

Depth scales with the change. A trivial work-unit gets a one-scenario
contract written in minutes; a substantial one gets the full refinement of
every criterion. The discipline is constant — done is defined before work
begins — the dose is proportional.

## Operating Principles

- **The contract is the spine.** Every downstream artifact traces to the
  scenarios named here. Vague scenarios at entry become unanchored work at
  every later stage.
- **Plan from the work-unit graph, not from memory.** Sessions end and
  context windows close; the work-unit graph and the artifact store are the
  working memory that survives. Read them; do not reconstruct from
  recollection.
- **Dependencies are hard blockers.** Work whose dependencies are open
  produces partial results that complicate the graph.
- **Direction over prediction.** Scenarios state observable outcomes, not
  implementation forecasts. Implementation sharpens inside the contract's
  boundaries, not around them.

## Corruption Modes

- `contract-after-code`: deferring contract authoring to implementation —
  the defining failure this protocol exists to prevent. Done gets defined by
  what was built instead of the work-unit's intent.
- `scope-creep`: scenarios that exceed the work-unit's boundaries. The
  contract covers the acceptance criteria — nearby work belongs in other
  work-units.
- `criteria-parroting`: copying acceptance criteria verbatim as scenarios
  without refinement into observable Given/When/Then behavior.
- `skip-preparation`: authoring the contract on dirty or unbranched ground —
  loses workspace isolation and makes `submit` harder.
- `state-lag`: the tracker not reflecting that this work-unit is in
  progress. Inaccurate state is planning debt for every other session.
- `abandon-at-contract`: delivering the behavior contract and stopping —
  handing the work to a runtime that is not sequencing it. The contract
  becomes a definition of done that nothing executes, and the stations are
  silently skipped. Until the runtime carries the work, take does.

## Cross-References

- `contract` (skill): the BDD discipline — authoring the contract here,
  carrying it through every later stage.
- `reckon` (skill): when framing reveals the work-unit's premise is unclear
  or contested, reckon before contracting.
- `decompose` (protocol): owns work-unit boundaries and acceptance-criteria
  quality. A work-unit that cannot be framed or contracted routes back there.
- `acquire` (skill): the other entry source — materializes the work-unit
  artifact from an existing forge ticket before take activates on it.
- `plan` (protocol): the next station — consumes the contract and converges
  on a decision-complete design.
- `land` (protocol): the closing bookend — take establishes what done means;
  land records that it was done.
