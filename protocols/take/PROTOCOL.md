---
name: take
description: >-
  Contract-first entry of the scoped pipeline: receive an already-selected
  work-unit, prepare the workspace, and establish the contract that
  defines done. The contract produced here is the spine every downstream
  protocol carries to land; the session surface advances the pipeline from
  it. Trigger on: 'take', 'take work', 'start work-unit'.
metadata:
  version: "3.9.0"
  updated: "2026-07-02"
---

# Take — Contract-First Entry

Take opens work on a single work-unit. Selection happened upstream — the
work-unit artifact exists and runa activates take on it, having arrived
either from `decompose` (a newly created work-unit) or from the `acquire`
skill (materialized from an existing forge ticket). Entry's real job is to
stand on prepared ground and state, precisely and verifiably, what will be
true when this work is done.

That statement is the `contract`: development here is
contract-driven, and it begins at the door. The contract authored in this
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

   Ground the frame in the whole ticket.
   The ticket body is the work-unit's spec.
   The comment log is the running record: review state, dispositions, and directives live there.
   `acquire` surfaces it from the `read-ticket` snapshot per forge-capability `1.2.0`.
   The newest review directives at the submitted head govern the work.
   The body remains the spec, and directives refine delivery against it.
   Weigh each log entry by recency and standing: a directive superseded by a newer round, or by a body amendment, is record, not direction.

4. **Author validation defined across the contract.** First reckon it:
   authoring the contract is a generative act — open the resolved principles
   corpus at `~/.groundwork/principles/`, select the principles that govern
   what "done" means here, read them, and reason the contract from them
   rather than the work-unit's surface wording alone (the reckon skill is
   the move).

   The `contract` skill is the single home of what validation defined means,
   per dimension: consult `skills/contract/SKILL.md` for the dimension
   table, the teeth principle, and the density rule that bind every
   dimension alike; `skills/contract/references/documentation-contract.md`
   for the documentation dimension's authoring form; and
   `skills/contract/references/code-quality-contract.md` for the
   code-quality dimension's authoring form. Use `orient` for the
   documentation audience taxonomy, and `~/.groundwork/principles/` for the
   universals themselves.

   Take's own role here is narrow and does not re-derive any of that: from
   this work-unit's own already-framed inputs (step 3), author this
   work-unit's validation defined — one instance of criteria per dimension
   the work-unit has, in the form and to the teeth and density the
   `contract` skill defines, sized to what this work-unit actually
   stresses. A validation-defined output that cannot be checked against the
   `contract` skill's own dimension table and teeth principle has
   re-encoded the lifecycle instead of consulting it — the
   `lifecycle-modeling` corruption mode below names exactly this failure.

5. **Deliver the contract spine.** Invoke the `contract` MCP tool with
   dimension-agnostic criteria. Each criterion declares the dimension it
   serves, the work-unit acceptance criterion it refines, the statement that
   defines done, the hollow delivery that would fail it, the `check_kind`
   (`executable` or `attested`), and the check descriptor. The object below
   is MCP tool input, not artifact body. `instance_id` is a tool parameter
   that names the artifact instance; it is extracted before validating
   artifact content, becomes the workspace filename, and must not appear in
   the artifact body. Runa injects `work_unit` from session context; the
   agent does not supply `work_unit`. Do not write the workspace JSON file
   directly.

   ```
   contract({
     instance_id: "<slug>",
     title: "<human-readable contract title>",
     criteria: [{
       id: "<stable criterion id>",
       dimension: "behavior" | "documentation" | "code-quality" | "<other>",
       acceptance_criterion: "<acceptance criterion this refines>",
       statement: "<dimension-specific definition of done>",
       hollow_delivery: "<plausible delivery that would fail this criterion>",
       check_kind: "executable" | "attested",
       check: "<check descriptor>"
     }]
   })
   ```

   Runa validates the remaining artifact body fields against the contract
   schema, persists the artifact, and records it in the artifact store.

   Delivering the contract is take completing: the session surface computes
   the next ready station from artifact state and advances the work to it —
   the seam runa's session-surface contract
   (`docs/session-surface-contract.md` in the runa repository) and the
   manifest's trigger declarations own. Where no runtime is present
   to accept the MCP tool — a checkout that is not an initialized runa
   project — author the same contract as a committed workspace artifact (the
   contract JSON, or the work-unit issue if there is no workspace store) so
   the spine exists and binds the test-first cycle either way.

## Scale

Depth scales with the change. A trivial work-unit gets a one-scenario
contract written in minutes; a substantial one gets the full refinement of
every criterion. The discipline is constant — done is defined before work
begins — the dose is proportional.

## Operating Principles

- **The contract is the spine.** Every downstream artifact traces to the
  criteria declared here by `criterion_id`. Vague criteria at entry become
  unanchored work at every later stage.
- **Plan from the work-unit graph, not from memory.** Sessions end and
  context windows close; the work-unit graph and the artifact store are the
  working memory that survives. Read them; do not reconstruct from
  recollection.
- **Dependencies are hard blockers.** Work whose dependencies are open
  produces partial results that complicate the graph.
- **Direction over prediction.** Behavior items state observable outcomes or
  reviewer-checkable gates, not implementation forecasts. Implementation
  sharpens inside the contract's boundaries, not around them.

## Corruption Modes

- `contract-after-code`: deferring contract authoring to implementation —
  the defining failure this protocol exists to prevent. Done gets defined by
  what was built instead of the work-unit's intent.
- `scope-creep`: criteria that exceed the work-unit's boundaries. The
  contract covers the acceptance criteria — nearby work belongs in other
  work-units.
- `criteria-parroting`: copying acceptance criteria verbatim as scenarios
  without refinement into observable Given/When/Then behavior.
- `stale-directive-followership`: framing a resume from older comment-trail
  direction. The newest review directives at the submitted head govern;
  the body is the spec — a superseded directive is record, not direction.
- `skip-preparation`: authoring the contract on dirty or unbranched ground —
  loses workspace isolation and makes `submit` harder.
- `state-lag`: the tracker not reflecting that this work-unit is in
  progress. Inaccurate state is planning debt for every other session.
- `dimension-declaration-only`: naming documentation or code-quality
  dimensions without defining the validation each must satisfy. The
  contract has labels but no teeth.
- `gate-as-scenario`: fabricating Given/When/Then scenarios for a
  documentation-deliverable unit whose behavior is actually proved by
  structural, coherence, and conformance gates.
- `lifecycle-modeling`: re-encoding the contract lifecycle or dimension
  authority in `take` instead of consulting the `contract` skill, `orient`,
  and the principles corpus as their single homes.

## Cross-References

- `contract` (skill): the multidimensional contract discipline — validation
  defined here, carrying it through every later stage. Its documentation and
  code-quality references own the audience-outcome checklist and projected
  universals forms.
- `reckon` (skill): authoring the contract is a generative act, so
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
