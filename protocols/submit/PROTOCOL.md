---
name: submit
description: >-
  Deliver an initial or revised change-proposal for review. Fires when
  completion evidence exists, and re-fires from change-needs-revision;
  preserves immutable proposal version history.
metadata:
  version: "3.0.0"
  updated: "2026-06-11"
---

# Submit

Submit is the gate between verified work and review. It produces the
forge-neutral `change-proposal` artifact that review consumes — whether this
is the first proposal version or a revised version answering review
findings.

The protocol is not a forge operation. It names the methodology obligation:
collect the verified change, deliver it through the configured connector,
and record the proposal in a stable artifact with branch, commit, base,
summary, immutable `version`, and opaque `handle`. Forge-specific delivery
lives entirely behind the forge capability connector seam; the artifact's
`handle` carries only the connector-issued `{id, display}` reference
downstream.

## Steps

1. **Resolve the round.** This delivery is initial when no
   `change-needs-revision` disposition is pending, and a revision when one
   is. A revision answers the prior round's blocking findings; identify the
   prior reviewed proposal version before proceeding — if it cannot be
   identified, stop rather than overwrite history.

2. **Address findings (revision rounds only).** Resolve each blocking
   finding with the same discipline the original work used: behavior-level
   findings get failing tests first (`implement`'s cycle), evidence gaps get
   the gate re-run (`verify`), contract gaps update the contract. Commit the
   revision to the proposal branch.

3. **Prepare the proposal.** Fix the branch, commit, and base that carry the
   change, and write a summary that names the contracted behaviors the
   change ships. The summary is the proposal's public claim; it derives from
   the behavior contract and the completion evidence, not from memory.

4. **Deliver through the forge connector.** Initial delivery invokes the
   invariant `deliver-change-proposal` forge capability operation; revision
   delivery resolves the methodology `revise` step and then delivers the new
   version through the same connector surface. The protocol encodes no
   forge-specific delivery language.

5. **Deliver the `change-proposal`.** Invoke the `change-proposal` MCP tool.
   The object below is MCP tool input, not artifact body. `instance_id` is a
   tool parameter that names the artifact instance; it is extracted before
   validating artifact content, becomes the workspace filename, and must not
   appear in the artifact body. Runa injects `work_unit` from session
   context; the agent does not supply `work_unit`. Do not write the
   workspace JSON file directly:

   ```
   change-proposal({
     instance_id: "<slug>",
     branch: "<proposal branch or carrier branch>",
     commit: "<proposal commit or stable revision>",
     base: "<target base revision>",
     summary: "<human-readable proposal summary>",
     version: <review-round version>,
     handle: {
       id: "<connector-issued id>",
       display: "<human-readable proposal>"
     }
   })
   ```

   Runa validates the remaining artifact body fields against the
   change-proposal schema, persists the artifact, and records it in the
   artifact store.

A revision round never mutates an earlier proposal artifact: it creates a
new valid `change-proposal` whose `version` advances for this work unit.
Review re-runs through its `on_change` trigger on the new version.

## Failure Policy

- If the proposal cannot be delivered, stop without producing a
  `change-proposal` artifact.
- If a revision round cannot identify the prior reviewed proposal version,
  stop rather than overwrite proposal history.
- If delivery exposes forge-specific details, stop and route the defect to the
  connector boundary; proposal artifacts carry only opaque capability handles.

## Corruption Modes

- `revision-loop-bypass`: responding to review without producing a fresh
  proposal version, leaving review no changed input to process.
- `version-overwrite`: replacing an earlier proposal artifact instead of
  preserving review-round history.
- `forge-leakage`: embedding forge-specific delivery procedure in the
  protocol rather than behind the connector seam.
- `summary-drift`: a proposal summary that names work the evidence does not
  support, or omits behaviors the contract requires.

## Cross-References

- `workflow-contracts/submit.toml` defines the C-2 delivery and revision
  flow.
- `schemas/change-proposal.schema.json` defines the proposal artifact.
- `protocols/review/PROTOCOL.md` consumes the proposal and produces exactly
  one typed review disposition.
- `verify` (protocol): supplies the completion evidence this gate requires.
