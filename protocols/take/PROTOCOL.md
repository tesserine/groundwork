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
  version: "3.3.0"
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

4. **Author the behavior contract.** First reckon it: authoring the
   contract is a generative act — open the resolved principles corpus at
   `~/.groundwork/principles/`, select the principles that govern what
   "done" means here, read them, and reason the contract from them rather
   than the work-unit's surface wording alone (the reckon skill is the
   move). Then refine each acceptance criterion into
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
   carries it — that bridging is take's job at the door.

   The carry begins at `plan`, and the plan is where the work converges.
   The plan that serves this work is the `plan` protocol's contract-centered
   design: the goal stated from the contract's scenarios, each scenario
   mapped to the steps that make it true, the test strategy that turns each
   into a failing test before its code. Where the harness plans before it
   executes, *that design is the plan you surface for approval* — not a
   narration of pipeline mechanics, which station comes next or which
   command advances it. Lead with the contract: its scenario coverage (the
   design), the absence of any gap through which a delivery the contract
   accepts as done could still fail (the robustness), and how each scenario
   is driven red-then-green (the validation). Surface that, and accepting
   the plan is accepting the contracted work — full convergence at the
   planning surface.

   On acceptance, carry it forward yourself. You are already the agent:
   deliver the `implementation-plan` artifact through its output tool to
   advance `plan`, then drive the remaining stations directly — `implement`
   (build it test-first; every scenario a failing test before its code,
   `contract-after-code` forbidden), `verify` (every scenario green, the
   change sound), `submit` (deliver the change for review) — opening
   `runa-mcp` in session mode for the work-unit and, at each station,
   reading its context, doing the work, producing its artifact, advancing.
   Do not hand the carry-through to `runa go --work-unit`: that spawns a
   separate agent that is not yet wired, and the work stalls; until it is
   wired, you drive the session directly. Do not stop at a boundary waiting
   to be carried. Review and land — the independent-judgment gate and the
   governance close — follow once every scenario is green and verify passes.

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
- `mechanics-as-plan`: surfacing a narration of pipeline mechanics — which
  station is next, which command advances it — as the plan, instead of
  running `plan` to produce the contract-centered design. Nothing
  contract-shaped is put up to accept, only a procedure to run; the
  convergence is lost.
- `delegate-to-unwired-runtime`: handing the carry-through to `runa go
  --work-unit` (the autonomous agent-spawn) while it is not yet wired,
  instead of driving the session yourself. The work stalls at a spawned
  agent that never advances — a quieter `abandon-at-contract`. Until that
  path is wired, you are the driver.

## Cross-References

- `contract` (skill): the BDD discipline — authoring the contract here,
  carrying it through every later stage.
- `reckon` (skill): authoring the behavior contract is a generative act, so
  reckon fires before the contract is set — grounding what "done" means in
  the navigational principles, not pattern-matching an adjacent work-unit.
  Per reckon's own trigger (every generative act, not a sequence position);
  dose proportional to the change, the discipline constant.
- `decompose` (protocol): owns work-unit boundaries and acceptance-criteria
  quality. A work-unit that cannot be framed or contracted routes back there.
- `acquire` (skill): the other entry source — materializes the work-unit
  artifact from an existing forge ticket before take activates on it.
- `plan` (protocol): the next station — consumes the contract and converges
  on a decision-complete design.
- `land` (protocol): the closing bookend — take establishes what done means;
  land records that it was done.
