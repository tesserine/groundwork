---
name: verify
description: >-
  Gate completion claims with fresh verification evidence and a
  documentation-impact review. Fires after implementation, before the work
  is packaged for review. No claim of complete, fixed, or passing without
  running the verification and reading the output — evidence before
  assertions, always.
metadata:
  version: "2.1.0"
  updated: "2026-06-20"
  origin: "Adapted from obra/superpowers (MIT). See LICENSE-UPSTREAM."
---

# Verify

Evidence before claims, always.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If the verification command was not run fresh, in this protocol, the claim
has no basis. Confidence is not evidence; a previous run is not evidence;
a partial check supports only a partial claim. Recognition signals,
claim-by-claim requirements, and the rationalization table:
[references/gate-patterns.md](references/gate-patterns.md).

This protocol owns the aggregate gate — the moment before "done." Per-test
cycle evidence (each test watched failing, then passing) belongs to
`implement`. Completion here means: every contract criterion has one performed
result recording its stated operational check, the work-unit's
criteria are covered, and the documentation still tells the truth.

## Steps

1. **Identify the gate.** Read `contract.criteria[]` and name what proves
   each criterion complete: perform the operational check the criterion
   itself states — its actor, procedure, and observable. The contract is
   the source of coverage; do not derive
   scenario or gate lists outside the criterion records.

2. **Run fresh.** Execute the full command. Read the entire output; check
   the exit code; count the failures. Output from any earlier run is stale
   the moment code changed.

3. **Assess criterion results.** Join contract criteria × performed
   results. Contract criteria and performed results line up when every
   `contract.criteria[].id` has exactly one
   `completion-evidence.results[]` entry with a matching `criterion_id`,
   and each entry records the criterion's stated check performed — the
   run, produced artifact, or recorded finding its procedure yields, with
   its observable read. If verification surfaces a
   failure, stop and invoke `debug` — root cause before fixes. A fix to
   this work-unit's own increment applies `implement`'s cycle discipline
   (failing test first, minimal change), then the gate re-runs fresh from
   step 2. Record honestly whatever the evidence shows — pass or fail per
   criterion, with no invented coverage rows.

4. **Review the declared contracts.** Audit the change against each
   lens the contract declared beyond the behavior coverage assessment.
   For **documentation**:
   confirm each declared pillar's outcome is met, and keep existing docs
   honest against drift — classify each mapped document as accurate,
   drifted, missing, or obsolete; update what the change touched in the same
   branch; file follow-ups for anything deeper. Method:
   [references/documentation-review.md](references/documentation-review.md).
   For **code quality**: audit the diff against each declared universal,
   recording the locus where it holds or the finding where it fails. Method:
   [references/code-quality-review.md](references/code-quality-review.md).

5. **Deliver `completion-evidence`.**
   Invoke the `completion-evidence` MCP tool with one result per contract
   criterion. Executable criteria record run or artifact evidence. Attested
   criteria record reviewer identity and finding; a bare pass is not
   evidence. The object below is MCP tool input, not artifact body.
   `instance_id` is a tool parameter that names the artifact instance; it is
   extracted before validating artifact content, becomes the workspace
   filename, and must not appear in the artifact body.
   Runa injects `work_unit` from session context; the agent does not supply `work_unit`.
   Do not write the workspace JSON file directly.

   ```
   completion-evidence({
     instance_id: "<slug>",
     results: [{
       criterion_id: "<contract criterion id>",
       result: "pass" | "fail",
       binding: "ci" | "harness",
       evidence: {
         summary: "<what the evidence proves>",
         run: {
           command: "<fresh verification command>",
           result: "pass" | "fail",
           output_summary: "<relevant output summary>"
         }
       }
     }, {
       criterion_id: "<attested contract criterion id>",
       result: "pass" | "fail",
       binding: "manual",
       evidence: {
         summary: "<what the reviewer found>",
         attestation: {
           reviewer: "<reviewer identity>",
           finding: "<finding with enough substance to audit>"
         }
       }
     }],
     documentation: {
       updated: ["<docs updated in this change>"],
       verified_accurate: ["<docs reviewed, confirmed accurate>"],
       follow_up_work_units: ["<work-units filed for deeper doc work>"]
     }
   })
   ```

   Runa validates the remaining artifact body fields against the
   completion-evidence schema before persisting the artifact and recording
   it in the artifact store. The schema is the persist seam's whole
   validation reach — it cannot range over another artifact's criterion
   ids — so criterion coverage is this protocol's own gate: every result
   names a declared contract criterion and every contract criterion carries
   a performed result (`invented-coverage` below), and review blocks on any
   uncovered criterion.

The evidence is honest, not aspirational: gaps and failures are recorded as
gaps and failures. Review consumes this evidence and blocks on it — an
uncovered criterion shipped to review is a blocking finding, not a secret.

## Corruption Modes

- `performative-verification`: running the command without reading the
  output. If the output did not change your understanding, you did not
  verify.
- `partial-verification`: one test file standing in for the suite, the
  linter standing in for the build. Partial evidence supports only partial
  claims.
- `stale-evidence`: citing output from before the last code change.
- `claim-first`: deciding the work is done, then selecting evidence to
  confirm it. Evidence determines the claim, never the reverse.
- `drift-tolerance`: documentation known stale but recorded as accurate, or
  deferred without a tracking work-unit.
- `invented-coverage`: deriving scenario or gate coverage beside the
  lens-agnostic contract criteria instead of recording one performed
  result per `contract.criteria[].id`.
- `lifecycle-modeling`: re-encoding the behavior lifecycle in `verify`
  instead of consuming the contract criteria as the single coverage source.

## Cross-References

- `implement` (protocol): owns per-cycle evidence; this protocol owns the
  aggregate gate.
- `contract` (skill): owns the criteria that define done; `verify` reports
  performed results for those criteria, not just command exit codes.
- `debug` (skill): fires on any failure surfaced here, before any fix.
- `submit` (protocol): consumes this evidence — work is packaged for review
  only after the gate has run.
- `orient` (skill): carries the always-on documentation-writing discipline
  that this protocol's review step audits.
