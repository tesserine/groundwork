---
name: submit
description: >-
  Deliver an initial or revised change-proposal artifact for review.
  Re-fires from change-needs-revision and preserves immutable proposal
  version history.
metadata:
  version: "2.0.0"
  updated: "2026-06-01"
---

# Submit

Submit is the gate between verified work and review. It produces the
forge-neutral `change-proposal` artifact that review consumes, whether the
delivery is the first proposal version or a revised version after review asks
for changes.

The protocol is not a forge operation. It names the methodology obligation:
collect the verified change, deliver a proposal through the configured
mechanics, and record the proposal detail in a stable artifact with branch,
commit, base, summary, immutable `version`, and forge-tagged `handle`.

## Activation

Submit activates in two cases:

- `documentation-record` exists after completion evidence and documentation
  review, producing the initial `change-proposal`.
- `change-needs-revision` exists after review, producing a later
  `change-proposal` version for the same work unit.

The revision round does not mutate the earlier proposal artifact. It creates a
new valid `change-proposal` whose `version` advances for that work unit. Review
then re-runs through its existing `on_change("change-proposal")` trigger.

## Proposal Delivery

Initial delivery uses the invariant `deliver-change-proposal` operation.
Revision delivery uses the invariant `revise` operation and then delivers the
new proposal version. Both paths end in the same capstone: a
`change-proposal` artifact.

When invoking `deliver-change-proposal`, resolve the operation through the
`forge-operation` skill. It reads the active forge from `GROUNDWORK_FORGE`,
defaults to `github` when absent, and selects the forge-specific mechanic from
the manifest matrix.

The protocol must not encode forge-specific delivery language. The artifact's
`handle` carries the forge-tagged reference needed by downstream review and
apply mechanics while the protocol remains at the WHAT layer.

## Deliver `change-proposal`

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
  branch: "<proposal branch or carrier branch>",
  commit: "<proposal commit or stable revision>",
  base: "<target base revision>",
  summary: "<human-readable proposal summary>",
  version: <review-round version>,
  handle: {
    forge_tag: "<registered forge tag>",
    "...": "<forge-specific handle fields>"
  }
})
```

Runa validates the remaining artifact body fields against the change-proposal
schema, persists the artifact, and records it in the artifact store.

## Failure Policy

- If the proposal cannot be delivered, stop without producing a
  `change-proposal` artifact.
- If a revision round cannot identify the prior reviewed proposal version, stop
  rather than overwrite proposal history.
- If delivery mechanics expose forge-specific details, keep them inside the
  forge-tagged `handle` and the configured mechanics layer.

## Corruption Modes

- `revision-loop-bypass`: responding to review without producing a fresh
  proposal version, leaving review with no changed input to process.
- `version-overwrite`: replacing an earlier proposal artifact instead of
  preserving review-round history.
- `forge-leakage`: embedding forge-specific delivery procedure in the protocol
  rather than in mechanics and handles.

## Cross-References

- `workflow-contracts/submit.toml` defines the C-2 delivery and revision flow.
- `schemas/change-proposal.schema.json` defines the proposal artifact.
- `protocols/review/PROTOCOL.md` consumes the proposal and produces exactly one
  typed review disposition.
