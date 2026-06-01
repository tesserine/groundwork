---
name: submit
description: >-
  Package verified, documented work as a forge-neutral change-proposal
  artifact. The C-2 contract names invariant delivery operations while C-3
  mechanics own forge-specific execution.
metadata:
  version: "2.0.0"
  updated: "2026-05-31"
---

# Submit

Submit is the gate between verified implementation work and review. It records
the current deliverable as a `change-proposal` so reviewers can inspect a
specific proposal version through a forge-tagged handle.

The protocol is not a forge operation. It names the methodology obligation:
confirm the work has completion evidence and documentation review, choose
whether the proposal is an initial submission or a revision, invoke the
forge-invariant delivery operation, and emit the artifact that review consumes.

## Purpose

Submit preserves the boundary between WHAT and HOW. The workflow contract says a
change proposal must exist for review; it does not prescribe transport,
review-surface creation, carrier generation, or any other forge-specific
mechanism. Those details belong to C-3 mechanics selected by forge
configuration.

The produced proposal carries the common review envelope: work unit, branch,
commit, base, summary, immutable version, and a forge-tagged handle. Version 1
represents the initial proposal. Later versions represent revision rounds for
the same work unit after review asks for changes.

## Proposal Paths

Submit has two delivery paths:

- `deliver-change-proposal` creates the first proposal version for a verified,
  documented change.
- `revise` creates the next proposal version after a needs-revision outcome.

Both paths terminate in the same `change-proposal` artifact type. Proposals are
not disposition outcomes; review decides disposition later by producing either
`change-approved` or `change-needs-revision`.

## Artifact Delivery

The capstone is delivery of the `change-proposal` artifact via the
`change-proposal` MCP tool. The object below is MCP tool input, not artifact
body. `instance_id` is a tool parameter that names the artifact instance; it is
extracted before validating artifact content, becomes the workspace filename,
and must not appear in the artifact body. Runa injects `work_unit` from session
context; the agent does not supply `work_unit`. Do not write the workspace JSON
file directly:

```
change-proposal({
  instance_id: "<slug>",
  branch: "<feature branch name>",
  commit: "<head commit or stable revision identifier>",
  base: "<target base branch or revision>",
  summary: "<human-readable proposal summary>",
  version: <review-round version>,
  handle: { ... forge-tagged handle ... }
})
```

Runa validates the remaining artifact body fields against the change-proposal
schema, persists the artifact, and records it in the artifact store.

## Corruption Modes

- `forge-mechanic-leakage`: embedding forge-specific commands or review-surface
  vocabulary in the protocol instead of leaving mechanics to the C-3 layer.
- `unversioned-revision`: replacing the current proposal without advancing the
  immutable review-round version.
- `premature-submit`: emitting a proposal without completion evidence and
  documentation review.
- `submit-as-review`: treating proposal delivery as approval. Submit only makes
  the proposal available for review.

## Cross-References

- `workflow-contracts/submit.toml` defines the C-2 submit flow and its
  change-proposal terminal.
- `schemas/change-proposal.schema.json` defines the forge-neutral proposal
  envelope and forge-tagged handle variants.
- `docs/architecture/step-2-reference-arc-design.md` explains the
  artifact-versioned review cycle and the invariant operations used by submit.
