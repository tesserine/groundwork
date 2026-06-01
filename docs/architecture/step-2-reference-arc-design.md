# Step 2 Reference Arc Design

## Audience and Purpose

This note is for agents and contributors authoring Step 2 of ADR-0002's
methodology-sovereignty rollout. It resolves the submit -> review -> land
reference arc decisions that #330-#334 build against.

The decisions here are constraints, not implementation instructions. They name
what the contracts and mechanics must make true, and they also name the places
where the current Step-1 substrate is not enough.

## Revision Note

ADR-0003 supersedes the original single-`review-findings` disposition record.
Review now emits exactly one typed outcome artifact, `change-approved` or
`change-needs-revision`, through a required-choice output group. The
review-cycle and classification-home decisions below still hold, but the
cross-protocol routing signal is the produced outcome type rather than a
`disposition` field.

## Grounding

ADR-0002's 2026-05-28 revision fixes the arc vocabulary at six
forge-invariant operations: `deliver-change-proposal`, `review`, `revise`,
`apply-approved-change`, `reflect-disposition`, and `close-out`. It also
replaces `patch` with `change-proposal`, gives each proposal an immutable
`version`, and adds a forge-tagged `handle`. ADR-0003 moves the review
disposition into the produced outcome type consumed by the land/revise flow.

The Step-1 substrate on `main` has these relevant facts:

- `workflow-contracts/*.toml` node `mechanics` are bare strings. The conformance
  runner resolves them as names from `manifest.toml` plus any `mechanics/**/*.toml`
  `name` values.
- `schemas/mechanic.schema.json` has `name` and an optional `forge_tag`; it has no
  separate operation field.
- `tooling.mechanics` validates that a mechanic's `forge_tag` is registered.
- `manifest.toml` registers available forge tags (`github`, `sourcehut`) and
  operation-to-mechanic bindings through `[[mechanics]].forge_tags`.
- `change-approved.schema.json` and `change-needs-revision.schema.json` make
  classification structural: approval cannot contain blocking observations, and
  needs-revision must contain at least one blocking observation.

The runa interface contract grounds the trigger decision: runa exposes artifact
types, protocol declarations, and trigger conditions. `on_change(name)` fires when
the named artifact changes relative to the protocol's current output artifacts
for the same work unit, successful executions record the processed input set, and
cycles emerge from artifact declarations rather than from a separate topology
language. The same contract does not define field-filtered triggers; trigger
conditions operate over artifact types.

## Decisions

### 1. The review cycle is artifact-versioned and re-fired by `on_change`

`submit` produces the first `change-proposal` version and every later revision
version for the same work unit. A revised proposal is a new valid
`change-proposal` instance with `version = previous + 1`; prior versions remain
review-round history.

`review` consumes the current proposal version and produces exactly one typed
outcome artifact whose `against_version` names the reviewed proposal version.
Re-review is expressed by `review` triggering on
`on_change("change-proposal")`, not by inventing a separate cycle vocabulary.
When a new proposal version appears, runa's input freshness model makes the
review protocol eligible again for that work unit.

The `version` field is methodology semantics, not runa semantics. Runa observes
artifact state and freshness; the review contract must select the latest valid
proposal version for the work unit and avoid reviewing an already-covered
version.

### 2. Classification is produced by `review`

Finding classification lives in the typed review outcome artifact, and the
disposition is authoritative as produced by the `review` step. There is no
separate `triage` protocol in Step 2 and no unnamed governance step between
review and land.

The `review` protocol may involve a human or external review agent, but the
capstone is still a typed review outcome artifact. The producing review step is
responsible for recording `blocking` or `non-blocking` on each finding and for
emitting exactly one disposition type. Full automation of the blocking call is
deferred; naming the producing step is not deferred.

### 3. Land gates on approved review disposition

`land` must not activate from a raw `change-proposal` or legacy `patch`. The
release gate is `on_artifact("change-approved")`. `change-needs-revision` routes
to revision instead, and runa's required-choice output group fails a review run
that emits no verdict or more than one verdict.

ADR-0003 supersedes this note's original field-predicate prerequisite. Runa
does not need to read `review-findings.disposition`; it only enforces output
type cardinality and routes on artifact type.

### 4. Forge-operation resolution is a Step-2 substrate gap

C-2 contracts must reference forge-invariant operation names only. They must not
contain `create-pr`, `pr-merge`, or other forge-specific HOW vocabulary.

The Step-2 substrate adds the resolution mechanism needed by that decision.
Bare mechanic names plus optional `forge_tag` validation prove that a mechanic
has a registered forge tag; manifest-declared `forge_tags` additionally prove
that an operation reference resolves to exactly one C-3 mechanic for the
declared forge.

The Step-2 resolution mechanism is:

- Treat a C-2 node mechanic string as an operation handle when it names one of
  the six invariant operations.
- Treat a C-3 mechanic's `name` as the operation it implements; when `forge_tag`
  is present, the mechanic is a forge-specific implementation of that operation.
- Resolve a forge-specific operation as `(operation name, active forge_tag)`.
- Reject missing matches and ambiguous matches.
- Validate, for the reference arc, that `github` and `sourcehut` each provide
  implementations for every forge-touching operation they need.

#333 introduced this mechanism for GitHub as the first C-3 mechanic library,
and #334 extends the same invariant operations to SourceHut:
`deliver-change-proposal`, `apply-approved-change`, and
`reflect-disposition` are bound under `forge_tag = "github"` and
`forge_tag = "sourcehut"`. Conformance rejects unknown, missing, or duplicate
operation/tag implementations.

The SourceHut delivery locus is the change-proposal mbox itself. Submit
produces an mbox, stores it at the artifact-store URI recorded in
`change-proposal.handle.mbox`, and does not send it to lists.sr.ht. Land reads
that same mbox handle after resolving the approved proposal by
`work_unit`/`against_version`, applies it with `git am --3way`, verifies the
applied and pushed head match the approved commit, and pushes the target ref
over SSH. Disposition lives in tracker-ticket state; there is no platform merge
or patchset email.

## Downstream Constraints

- #330: `submit` produces `change-proposal`, not `patch`; its contract uses
  `deliver-change-proposal` and, for revision rounds, `revise` as invariant
  operation handles. It must not embed GitHub or SourceHut vocabulary.
- #331: `review` consumes `change-proposal`, triggers on
  `on_change("change-proposal")`, declares a required-choice output group over
  `change-approved` / `change-needs-revision`, and names the disposition by the
  outcome type it produces.
- #332: `land` consumes `change-approved`, applies the approved change, reflects
  disposition, and closes out. It activates on the typed approval outcome, not a
  field predicate.
- #333/#334: GitHub and SourceHut mechanics implement the invariant operation
  handles through `forge_tag`-selected C-3 mechanics. They do not create
  per-(forge x mode) mechanics; the interactive artifact-delivery adapter remains
  the mode layer.

## Deliberate Deferrals

- lists.sr.ht and external-contributor patchset submission remain outside Step 2.
- Native forge review APIs are outside Step 2 except where required by the chosen
  forge-specific mechanics and disposition reflection.
- Full automation of blocking classification is outside Step 2; the review step
  is authoritative for classification.
- General runa trigger predicates beyond the approved-review land gate are not
  designed here.

## Source References

- [ADR-0002](decisions/0002-methodology-sovereignty.md)
- [Step 1 R1 C-2 contract exercise](step-1-r1-c2-contract-exercise.md)
- [change-proposal schema](../../schemas/change-proposal.schema.json)
- [change-approved schema](../../schemas/change-approved.schema.json)
- [change-needs-revision schema](../../schemas/change-needs-revision.schema.json)
- [workflow-contract schema](../../schemas/workflow-contract.schema.json)
- [mechanic schema](../../schemas/mechanic.schema.json)
- [runa interface contract](https://github.com/tesserine/runa/blob/main/docs/interface-contract.md)

## Acceptance Check

This note closes #243's open cycle-vocabulary question by choosing
artifact-versioned re-review through `on_change("change-proposal")`, grounded in
runa's trigger model. It closes the triage-home question by making the typed
review outcome produced by `review` the classification authority. It closes
the forge-resolution question by naming the exact current substrate gap and the
required operation resolution mechanism. ADR-0003 supersedes the original
land-disposition field-predicate gap with typed outcome routing and the
required-choice output edge.
