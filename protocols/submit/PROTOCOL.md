---
name: submit
description: >-
  Deliver an initial or revised change-proposal for review. Fires when
  completion evidence exists, and re-fires from change-needs-revision;
  preserves immutable proposal version history.
metadata:
  version: "3.1.0"
  updated: "2026-06-20"
---

# Submit

Submit is the gate between verified work and review. It produces the
forge-neutral `change-proposal` artifact that review consumes — whether this
is the first proposal version or a revised version answering review
findings.

Submit packages the multidimensional contract for review. It consults the
`contract` skill (`skills/contract/SKILL.md`) for the lifecycle and carries
the performed validation from `verify`: the behavior dimension in the
deliverable's behavior form, the documentation dimension's audience-outcome
review, and the code-quality dimension's projected-universal findings.

The protocol is not a forge operation. It names the methodology obligation:
collect the verified change, deliver it through the configured mechanics,
and record the proposal in a stable artifact with branch, commit, base,
summary, immutable `version`, and forge-tagged `handle`. Forge-specific
delivery lives entirely in the mechanic layer; the artifact's `handle`
carries the forge-tagged reference downstream.

## Steps

1. **Resolve the round.** This delivery is initial when no
   `change-needs-revision` disposition is pending, and a revision when one
   is. A revision answers the prior round's blocking findings; identify the
   prior reviewed proposal version before proceeding — if it cannot be
   identified, stop rather than overwrite history.

2. **Address findings (revision rounds only).** Resolve each blocking
   finding with the same discipline the original work used: behavior-level
   findings get failing tests first (`implement`'s cycle), documentation or
   code-quality findings update the affected dimension and evidence gaps get
   the gate re-run (`verify`), contract gaps update the contract. Commit the
   revision to the proposal branch.

3. **Prepare the proposal.** Fix the branch, commit, and base that carry the
   change, and write a summary that names the declared dimensions the change
   ships. The summary is the proposal's public claim; it derives from the
   completion evidence, not from memory: behavior coverage in scenario or
   gate form, documentation outcomes from the audience-outcome review, and
   code-quality findings from the projected-universals audit. The
   `contract` skill supplies the lifecycle and the behavior form; this
   protocol packages the validation-performed, it does not restate the
   lifecycle.

4. **Deliver through the forge mechanic.** Initial delivery resolves the
   invariant `deliver-change-proposal` operation; revision delivery resolves
   the invariant `revise` operation and then delivers the new version. An
   executing agent resolves each operation through `groundwork-mechanic` and
   runs the active-forge mechanic it returns. The protocol encodes no
   forge-specific delivery language.

5. **Deliver the `change-proposal`.**
   For a runtime-behavior work-unit, follow the scenario-keyed runtime close
   path and invoke the `change-proposal` MCP tool. The proposal summary
   carries the multidimensional claim: executable scenarios or scenario
   coverage for behavior, documentation outcomes, and code-quality findings.
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
       forge_tag: "<registered forge tag>",
       "...": "<forge-specific handle fields>"
     }
   })
   ```

   Runa validates the remaining artifact body fields against the
   change-proposal schema, persists the artifact, and records it in the
   artifact store.

   For a documentation-deliverable work-unit, report the gate-form
   packaging as committed evidence. The structural, coherence, and
   conformance coverage is the behavior dimension in the deliverable's
   behavior form, and the proposal still carries documentation and
   code-quality validation-performed for review. Runa-backed runtime
   sequencing of gate-form close artifacts — and any `change-proposal`
   schema change it would require — is deferred to #454; name that boundary
   honestly rather than routing this path through a runtime shape it cannot
   satisfy today.

A revision round never mutates an earlier proposal artifact: it creates a
new valid `change-proposal` whose `version` advances for this work unit.
Review re-runs through its `on_change` trigger on the new version.

## Failure Policy

- If the proposal cannot be delivered, stop without producing a
  `change-proposal` artifact.
- If a revision round cannot identify the prior reviewed proposal version,
  stop rather than overwrite proposal history.
- If delivery mechanics expose forge-specific details, keep them inside the
  forge-tagged `handle` and the configured mechanics layer.

## Corruption Modes

- `revision-loop-bypass`: responding to review without producing a fresh
  proposal version, leaving review no changed input to process.
- `version-overwrite`: replacing an earlier proposal artifact instead of
  preserving review-round history.
- `forge-leakage`: embedding forge-specific delivery procedure in the
  protocol rather than in mechanics and handles.
- `summary-drift`: a proposal summary that names work the evidence does not
  support, or omits a declared dimension the contract requires. A
  behavior-only summary that drops documentation or code-quality validation
  is drift even when behavior coverage is green.

## Cross-References

- `workflow-contracts/submit.toml` defines the C-2 delivery and revision
  flow.
- `schemas/change-proposal.schema.json` defines the proposal artifact.
- `protocols/review/PROTOCOL.md` consumes the proposal and produces exactly
  one typed review disposition.
- `contract` (skill): owns the lifecycle and behavior forms this protocol
  consults while packaging validation-performed.
- `verify` (protocol): supplies the completion evidence this gate requires
  across behavior, documentation, and code quality.
