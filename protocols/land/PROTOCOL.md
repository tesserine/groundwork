---
name: land
description: >-
  Apply the approved change-proposal version, reflect the disposition, close
  out the work unit, and deliver the completion-record. The closing bookend
  of the scoped pipeline.
metadata:
  version: "3.3.0"
  updated: "2026-07-02"
---

# Land

Land is the approved-disposition gate and the pipeline's closing bookend:
define established what done means; land records that it was done. It
activates only from `change-approved`, applies exactly the proposal version
that approval names, reflects the disposition, and records completion.

Land closes the multi-lens contract. It consults the `contract` skill
(`skills/contract/SKILL.md`) for the lifecycle and records validation
performed for every declared lens from the same uniform evidence
surface: the per-criterion results in `completion-evidence.results[]`.

The protocol is not a forge operation. It must not activate from a raw
`change-proposal` — an unreviewed proposal is not a release gate — and
`change-needs-revision` routes back to submit, never here.

## Steps

1. **Resolve the approved proposal.** Select the `change-proposal` whose
   `work_unit` matches `change-approved.work_unit` and whose `version`
   equals `change-approved.against_version`. The pair is the binding —
   `against_version` alone is not globally unique across work units. If
   zero or more than one proposal matches, stop before applying. Also read
   the matching `work-unit` artifact so the connector input can use the
   connector-issued work-unit handle.

2. **Apply.** Invoke the connector capability `apply-approved-change`
   operation with the input shape required by the vendored
   `apply-approved-change-input` schema:

   - `work_unit`: the matching `work-unit.handle`
   - `change`: the resolved `change-proposal.handle`
   - `approved_version`: `change-approved.against_version`, equal to the
     resolved `change-proposal.version`
   - `approved_commit`: the resolved `change-proposal.commit`
   - `base`: the resolved `change-proposal.base`

   `branch` is not passed to `apply-approved-change`; the connector schema
   rejects extra fields. Never apply the latest proposal — apply the approved
   one.

3. **Reflect the disposition.** Invoke `reflect-disposition`: the
   collaboration surface records that the approval was acted on.

4. **Close out.** Invoke `close-out`: the work unit's tracker record carries
   its completion context — per-criterion coverage across every declared
   lens, gaps named, and the merge reference — derived from
   `completion-evidence.results[]`.

5. **Deliver the `completion-record`.**
   Invoke the `completion-record` MCP tool. Every field derives from the
   uniform evidence surface: `criterion_summary` summarizes the
   per-criterion results in `completion-evidence.results[]` across every
   declared lens — behavior, documentation, and code quality alike;
   `documentation_status` derives from the documentation lens's
   recorded results; the code-quality lens's recorded findings and
   diff loci enter the close-out context as committed evidence. Do not
   assert a field the completion-record schema does not define.

   The object below is MCP tool input, not artifact body.
   `instance_id` is a tool parameter that names the artifact instance; it is
   extracted before validating artifact content, becomes the workspace
   filename, and must not appear in the artifact body.
   Runa injects `work_unit` from session context; the agent does not supply `work_unit`.
   Do not write the workspace JSON file directly:

   ```
   completion-record({
     instance_id: "<slug>",
     criterion_summary: "<how acceptance criteria were met>",
     gaps: ["<known gaps or follow-up work - empty array if none>"],
     merge_reference: "<applied proposal reference>",
     documentation_status: "<documentation coverage summary>"
   })
   ```

   Runa validates the remaining artifact body fields against the
   completion-record schema, persists the artifact, and records it in the
   artifact store. The record distills the contract's closure: every
   recorded lens derives from the performed per-criterion results, by
   the same derivation, with `completion-evidence.results[]` as the single
   evidence surface.

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
- `lens-drop`: recording behavior-only completion while omitting a
  declared lens. Dropping documentation or code-quality evidence from
  close-out breaks the contract even when `criterion_summary` is complete.

## Cross-References

- `workflow-contracts/land.toml` defines the C-2 approved-disposition flow.
- `schemas/change-approved.schema.json` defines the approval disposition.
- `schemas/change-proposal.schema.json` defines the proposal detail land
  resolves before mapping it to the connector apply input.
- `schemas/forge-capability/v2/forge-capability.schema.json` defines the
  `apply-approved-change-input` connector payload land must satisfy.
- `schemas/completion-record.schema.json` defines the record fields land
  fills from the uniform evidence surface: `criterion_summary` carries
  per-criterion coverage for every lens, `documentation_status`
  carries the documentation lens's derived summary, and the
  code-quality results enter close-out context as committed evidence.
- `contract` (skill): owns the lifecycle this protocol consults while
  recording validation-performed.
- `define` (protocol): the opening bookend — the contract established there
  is what this record closes.
