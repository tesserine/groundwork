---
name: land
description: >-
  Apply the approved change-proposal version, reflect the disposition, close
  out the work unit, and deliver completion-record.
metadata:
  version: "2.0.0"
  updated: "2026-06-01"
---

# Land

Land is the approved-disposition gate. It activates only from
`change-approved`, resolves the exact proposal version that was approved,
applies that proposal through the configured mechanics, reflects the
disposition, and records completion.

The protocol is not a forge operation. It names the methodology obligation:
use review's typed approval as the release gate and apply only the proposal
detail that approval names.

## Activation

Land activates on `on_artifact("change-approved")`. It must not activate from
a raw `change-proposal`; an unreviewed proposal is not a release gate.
`change-needs-revision` routes back to submit and cannot activate land.

## Approved Proposal Resolution

`change-approved` carries disposition metadata: `work_unit`,
`against_version`, reviewer, timestamp, and findings. The proposal detail used
to apply the change comes from `change-proposal`.

Land must select the `change-proposal` whose `work_unit` matches
`change-approved.work_unit` and whose `version` equals
`change-approved.against_version`. The pair is the binding. `against_version`
alone is not globally unique because multiple work units can have the same
review-round number.

The resolved proposal supplies the apply detail: `branch`, `commit`, `base`,
and `handle`. If no proposal or more than one proposal matches the
`work_unit`/`against_version` pair, land stops without applying a change.

## Apply, Reflect, Close Out

After resolving the approved proposal, land invokes the invariant operations in
order:

1. `apply-approved-change` applies the resolved proposal detail.
2. `reflect-disposition` records that the approved disposition was acted on.
3. `close-out` records work-unit completion context.

These operation names remain forge-invariant. Forge-specific mechanics may
implement them, but the protocol does not prescribe those mechanics. Resolve
each operation through the `forge-operation` skill, which reads
`GROUNDWORK_FORGE`, defaults to `github` when absent, and selects exactly one
mechanic from the manifest matrix.

## Deliver `completion-record`

The capstone is delivery of the `completion-record` artifact via the
`completion-record` MCP tool. The object below is MCP tool input, not artifact
body. `instance_id` is a tool parameter that names the artifact instance; it is
extracted before validating artifact content, becomes the workspace filename,
and must not appear in the artifact body. Runa injects `work_unit` from session
context; the agent does not supply `work_unit`. Do not write the workspace JSON
file directly:

```
completion-record({
  instance_id: "<slug>",
  criterion_summary: "<how acceptance criteria were met>",
  gaps: ["<known gaps or deferred work - empty array if none>"],
  merge_reference: "<applied proposal reference>",
  documentation_status: "<documentation coverage summary>"
})
```

Runa validates the remaining artifact body fields against the completion-record
schema, persists the artifact, and records it in the artifact store.

## Failure Policy

- If approval does not resolve to exactly one proposal by
  `work_unit`/`against_version`, stop before applying.
- If applying the approved proposal fails, stop before reflecting disposition
  or closing out.
- If disposition reflection or close-out fails after apply, record the gap in
  the eventual completion context rather than claiming complete closure.

## Corruption Modes

- `raw-proposal-landing`: applying a proposal without typed approval.
- `version-only-binding`: selecting by `against_version` alone and risking a
  cross-work-unit collision.
- `latest-proposal-drift`: applying the latest proposal instead of the proposal
  version review approved.
- `forge-leakage`: embedding forge-specific apply or close-out procedure in the
  protocol rather than in mechanics.

## Cross-References

- `workflow-contracts/land.toml` defines the C-2 approved-disposition flow.
- `schemas/change-approved.schema.json` defines the approval disposition.
- `schemas/change-proposal.schema.json` defines the proposal detail land
  resolves and applies.
