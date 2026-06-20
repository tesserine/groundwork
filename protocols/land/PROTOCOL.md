---
name: land
description: >-
  Apply the approved change-proposal version, reflect the disposition, close
  out the work unit, and deliver the completion-record. The closing bookend
  of the scoped pipeline.
metadata:
  version: "3.1.0"
  updated: "2026-06-20"
---

# Land

Land is the approved-disposition gate and the pipeline's closing bookend:
take established what done means; land records that it was done. It
activates only from `change-approved`, applies exactly the proposal version
that approval names, reflects the disposition, and records completion.

Land closes the multidimensional contract. It consults the `contract` skill
(`skills/contract/SKILL.md`) for the lifecycle and records validation
performed for the behavior dimension in the deliverable's behavior form, the
documentation dimension's audience-outcome review, and the code-quality
dimension's projected-universal findings.

The protocol is not a forge operation. It must not activate from a raw
`change-proposal` — an unreviewed proposal is not a release gate — and
`change-needs-revision` routes back to submit, never here.

## Steps

1. **Resolve the approved proposal.** Select the `change-proposal` whose
   `work_unit` matches `change-approved.work_unit` and whose `version`
   equals `change-approved.against_version`. The pair is the binding —
   `against_version` alone is not globally unique across work units. If
   zero or more than one proposal matches, stop before applying. The
   resolved proposal supplies the apply detail: `branch`, `commit`, `base`,
   and `handle`.

2. **Apply.** Resolve the invariant `apply-approved-change` operation
   through `groundwork-mechanic` and run the active-forge mechanic it
   returns, with the resolved proposal detail. Never the latest proposal —
   the approved one.

3. **Reflect the disposition.** Resolve and run `reflect-disposition`: the
   collaboration surface records that the approval was acted on.

4. **Close out.** Resolve and run `close-out`: the work unit's tracker
   record carries its completion context — behavior coverage in scenario or
   gate form, documentation outcomes, code-quality findings, gaps named,
   and the merge reference.

5. **Deliver the `completion-record`.**
   For a runtime-behavior work-unit, follow the scenario-keyed runtime close
   path and invoke the `completion-record` MCP tool. The behavior dimension
   is recorded in `criterion_summary`; the documentation dimension is
   recorded in `documentation_status`; the code-quality dimension is
   recorded as committed evidence in the close-out context, using the diff
   loci and findings from the projected-universals audit. A typed
   code-quality `completion-record` field is the schema expansion deferred
   to #454; do not assert a field the completion-record schema does not
   define.

   The object below is MCP tool input, not artifact body.
   `instance_id` is a tool parameter that names the artifact instance; it is
   extracted before validating artifact content, becomes the workspace
   filename, and must not appear in the artifact body. Runa injects
   `work_unit` from session context; the agent does not supply `work_unit`.
   Do not write the workspace JSON file directly:

   ```
   completion-record({
     instance_id: "<slug>",
     criterion_summary: "<how acceptance criteria were met>",
     gaps: ["<known gaps or deferred work - empty array if none>"],
     merge_reference: "<applied proposal reference>",
     documentation_status: "<documentation coverage summary>"
   })
   ```

   Runa validates the remaining artifact body fields against the
   completion-record schema, persists the artifact, and records it in the
   artifact store. The record distills the contract's closure: the
   criterion summary and documentation status derive from the performed
   validation in context, while code-quality validation remains committed
   close-out evidence until the typed field exists.

   For a documentation-deliverable work-unit, record the gate-form behavior
   coverage as committed evidence. Structural, coherence, and conformance
   gate coverage satisfies the behavior dimension in the deliverable's
   behavior form, and the record still carries documentation and
   code-quality validation-performed. Runa-backed runtime sequencing of
   gate-form close artifacts — and any `completion-record` schema change it
   would require — is deferred to #454; name that boundary honestly rather
   than implying the gate-form runtime path closes end to end today.

## Failure Policy

- If approval does not resolve to exactly one proposal by
  `work_unit`/`against_version`, stop before applying.
- If applying the approved proposal fails, stop before reflecting
  disposition or closing out.
- If disposition reflection or close-out fails after apply, record the gap
  in the completion record rather than claiming complete closure.

## Corruption Modes

- `raw-proposal-landing`: applying a proposal without typed approval.
- `version-only-binding`: selecting by `against_version` alone and risking
  a cross-work-unit collision.
- `latest-proposal-drift`: applying the latest proposal instead of the
  version review approved.
- `forge-leakage`: embedding forge-specific apply or close-out procedure in
  the protocol rather than in mechanics.
- `dimension-drop`: recording behavior-only completion while omitting a
  declared dimension. Dropping documentation or code-quality evidence from
  close-out breaks the contract even when `criterion_summary` is complete.

## Cross-References

- `workflow-contracts/land.toml` defines the C-2 approved-disposition flow.
- `schemas/change-approved.schema.json` defines the approval disposition.
- `schemas/change-proposal.schema.json` defines the proposal detail land
  resolves and applies.
- `schemas/completion-record.schema.json` defines the existing record fields:
  behavior closes through `criterion_summary`, documentation through
  `documentation_status`, and typed code-quality record expansion is
  deferred to #454.
- `contract` (skill): owns the lifecycle and behavior forms this protocol
  consults while recording validation-performed.
- `take` (protocol): the opening bookend — the contract established there
  is what this record closes.
