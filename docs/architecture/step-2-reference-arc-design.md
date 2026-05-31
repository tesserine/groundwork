# Step 2 Reference Arc Design

## Audience and Purpose

This note is for agents and contributors authoring Step 2 of ADR-0002's
methodology-sovereignty rollout. It resolves the submit -> review -> land
reference arc decisions that #330-#334 build against.

The decisions here are constraints, not implementation instructions. They name
what the contracts and mechanics must make true, and they also name the places
where the current Step-1 substrate is not enough.

## Grounding

ADR-0002's 2026-05-28 revision fixes the arc vocabulary at six
forge-invariant operations: `deliver-change-proposal`, `review`, `revise`,
`apply-approved-change`, `reflect-disposition`, and `close-out`. It also
replaces `patch` with `change-proposal`, gives each proposal an immutable
`version`, adds a forge-tagged `handle`, and makes `review-findings` carry the
review disposition consumed by the land/revise flow.

The Step-1 substrate on `main` has these relevant facts:

- `workflow-contracts/*.toml` node `mechanics` are bare strings. The conformance
  runner resolves them as names from `manifest.toml` plus any `mechanics/**/*.toml`
  `name` values.
- `schemas/mechanic.schema.json` has `name` and an optional `forge_tag`; it has no
  separate operation field.
- `tooling.mechanics` validates that a mechanic's `forge_tag` is registered, but
  it does not select a mechanic for an active forge.
- `manifest.toml` registers available forge tags (`github`, `sourcehut`), but it
  does not declare an active forge or operation-to-mechanic bindings.
- `review-findings.schema.json` already makes classification structural:
  `approved` findings cannot contain blocking observations, and `needs_revision`
  findings must contain at least one blocking observation.

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

`review` consumes the current proposal version and produces a `review-findings`
artifact whose `against_version` names the reviewed proposal version. Re-review
is expressed by `review` triggering on `on_change("change-proposal")`, not by
inventing a separate cycle vocabulary. When a new proposal version appears,
runa's input freshness model makes the review protocol eligible again for that
work unit.

The `version` field is methodology semantics, not runa semantics. Runa observes
artifact state and freshness; the review contract must select the latest valid
proposal version for the work unit and avoid reviewing an already-covered
version.

### 2. Classification is produced by `review`

Finding classification lives in `review-findings`, and the disposition is
authoritative as produced by the `review` step. There is no separate `triage`
protocol in Step 2 and no unnamed governance step between review and land.

The `review` protocol may involve a human or external review agent, but the
capstone is still the `review-findings` artifact. The producing review step is
responsible for recording `blocking` or `non-blocking` on each finding and the
aggregate `disposition` (`approved` or `needs_revision`). Full automation of the
blocking call is deferred; naming the producing step is not deferred.

### 3. Land gates on approved review disposition

`land` must not activate from a raw `change-proposal` or legacy `patch`. The
release gate is the approved review disposition in `review-findings`.

This is not fully realizable on the current runa trigger substrate as an exact
activation gate, because runa currently has artifact-type triggers but no field
predicate such as `review-findings.disposition == "approved"`. A type-level
trigger on `review-findings` would also fire for `needs_revision`, which would
activate `land` on a non-release state.

Therefore #332 requires a substrate addition before it can honestly satisfy the
gate: runa/manifest trigger conditions need a field predicate over a valid
artifact instance, at minimum enough to express "activate `land` when a scoped
`review-findings` instance has `disposition = approved`." The land C-2 contract
still verifies the disposition before applying the change, but runtime activation
must be predicate-gated so `needs_revision` findings route to revision instead
of a failing land run.

### 4. Forge-operation resolution is a Step-2 substrate gap

C-2 contracts must reference forge-invariant operation names only. They must not
contain `create-pr`, `pr-merge`, or other forge-specific HOW vocabulary.

The current Step-1 substrate does not yet implement the resolution mechanism
needed by that decision. Bare mechanic names plus optional `forge_tag` validation
prove that a mechanic has a registered forge tag; they do not prove that an
operation reference resolves to exactly one mechanic for an active forge.

The Step-2 resolution mechanism is:

- Treat a C-2 node mechanic string as an operation handle when it names one of
  the six invariant operations.
- Treat a C-3 mechanic's `name` as the operation it implements; when `forge_tag`
  is present, the mechanic is a forge-specific implementation of that operation.
- Resolve a forge-specific operation as `(operation name, active forge_tag)`.
- Reject missing matches and ambiguous matches.
- Validate, for the reference arc, that `github` and `sourcehut` each provide
  implementations for every forge-touching operation they need.

This mechanism is not present on `main`. It should be added as a substrate
prerequisite before the downstream contracts and mechanics are treated as
complete. #330 and #332 may author forge-invariant operation references only
after the conformance runner can validate the operation handles; #333 and #334
may author forge-tagged mechanics only after the runner can prove their
operation binding under the selected forge tag.

## Downstream Constraints

- #330: `submit` produces `change-proposal`, not `patch`; its contract uses
  `deliver-change-proposal` and, for revision rounds, `revise` as invariant
  operation handles. It must not embed GitHub or SourceHut vocabulary.
- #331: `review` consumes `change-proposal`, triggers on
  `on_change("change-proposal")`, produces authoritative `review-findings`, and
  names the disposition itself.
- #332: `land` consumes approved `review-findings`, applies the approved change,
  reflects disposition, and closes out. It depends on the approved-disposition
  trigger predicate substrate.
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
- [review-findings schema](../../schemas/review-findings.schema.json)
- [workflow-contract schema](../../schemas/workflow-contract.schema.json)
- [mechanic schema](../../schemas/mechanic.schema.json)
- [runa interface contract](https://github.com/tesserine/runa/blob/main/docs/interface-contract.md)

## Acceptance Check

This note closes #243's open cycle-vocabulary question by choosing
artifact-versioned re-review through `on_change("change-proposal")`, grounded in
runa's trigger model. It closes the triage-home question by making
`review-findings` produced by `review` the classification authority. It closes
the forge-resolution question by naming the exact current substrate gap and the
required operation resolution mechanism. It also names the land-disposition
trigger gap explicitly, so #332 does not assume a runtime feature that does not
exist on `main`.
