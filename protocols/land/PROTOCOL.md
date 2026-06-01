---
name: land
description: >-
  Apply an approved change after review disposition and produce the
  completion-record that closes the work-unit lifecycle.
metadata:
  version: "2.0.0"
  updated: "2026-06-01"
---

# Land

Land is the gate after review approval. It activates from the typed
`change-approved` outcome, applies the approved change through invariant
operations, reflects the disposition, and emits the `completion-record` that
archives completion for the work unit.

The protocol does not decide whether a proposal is acceptable. Review already
made that decision by producing `change-approved`. A `change-needs-revision`
outcome routes back to submit for a new proposal version and must not activate
land.

## Purpose

Land preserves the boundary between methodology outcome and execution
mechanics. The workflow contract says an approved change must be applied,
approval must be reflected, and close-out must produce a completion record. It
does not prescribe the configured transport or status surface used to perform
those operations.

## Workflow

Land has three invariant operations:

- `apply-approved-change` applies the reviewed change authorized by the
  approval outcome.
- `reflect-disposition` records that the approval disposition has been
  reflected in the configured work surface.
- `close-out` closes the work-unit lifecycle and prepares archival completion
  content.

All paths terminate in the same `completion-record` artifact type.

## Artifact Delivery

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
  merge_reference: "<applied change reference>",
  documentation_status: "<documentation coverage summary>"
})
```

Runa validates the remaining artifact body fields against the
completion-record schema, persists the artifact, and records it in the artifact
store.

## Corruption Modes

- `unapproved-release`: activating land from a raw proposal instead of the
  typed approval outcome.
- `revision-bypass`: treating `change-needs-revision` as releasable instead of
  routing back to submit.
- `mechanic-leakage`: embedding surface-specific commands or release-surface
  vocabulary in the protocol instead of leaving mechanics to the C-3 layer.
- `unrecorded-close-out`: applying the change without producing the archival
  `completion-record`.

## Cross-References

- `workflow-contracts/land.toml` defines the C-2 land flow and its
  completion-record terminal.
- `schemas/change-approved.schema.json` defines the approval outcome that gates
  land.
- `schemas/completion-record.schema.json` defines the archival completion
  record.
- `docs/architecture/step-2-reference-arc-design.md` explains why land routes
  on typed approval disposition.
