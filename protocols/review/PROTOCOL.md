---
name: review
description: >-
  Review a submitted change proposal against the behavior contract and
  evidence, and produce exactly one disposition outcome. Routes approval
  through `change-approved` and blocking findings through
  `change-needs-revision`.
metadata:
  version: "2.0.0"
  updated: "2026-06-11"
---

# Review

Review is the judgment gate between a submitted change proposal and
landing. It is where the pipeline's one act of independent judgment about
the change happens: the proposal is examined against the behavior contract,
the work-unit, and the evidence — then the decision is recorded as exactly
one typed outcome artifact.

The protocol is not a forge operation. The `code-review` skill supplies the
evaluation discipline; this protocol supplies the routing obligation.

## Steps

1. **Resolve the reviewed version.** Identify the current `change-proposal`
   version for this work unit. The disposition's `against_version` names it;
   without that binding, later rounds cannot be told from earlier ones.

2. **Inspect against the contract.** Evaluate the proposed change with the
   `code-review` skill's discipline: scope honesty against the work-unit,
   correctness, semantic-shift detection, evidence quality against the
   behavior contract and completion evidence, documentation impact. The
   contract is the measure — a change is judged by whether the contracted
   behaviors are delivered and proven, not by whether commands passed.

3. **Classify findings.** Each observation is `blocking` or `non-blocking`
   at the point of review. Blocking findings prevent approval. Non-blocking
   findings are recorded only when they do not affect correctness,
   traceability, documentation accuracy, or the ability to continue.

4. **Emit exactly one disposition.** The manifest-declared
   `review-disposition` required-choice group:
   - `change-approved` when no blocking findings remain.
   - `change-needs-revision` when at least one blocking finding remains.

   The outcome artifact *is* the disposition. There is no
   disposition-agnostic review record for later steps to reinterpret, and no
   triage step between review and land. Downstream protocols route on the
   produced artifact type; a review run that emits zero or two dispositions
   is invalid.

## The Gate's Authority

Review is the human gate of the scoped pipeline, by design: transition
authority lives in this typed disposition, not in per-operation approval
elsewhere (per runa's session-surface contract). The reviewer may be a
fresh agent context, an external review agent, or the operator — the
capstone is the same typed outcome either way, and the disposition records
the reviewer identity. What the gate may never become is the author's own
momentum approving itself without examination.

## Corruption Modes

- `disposition-agnostic-routing`: emitting a shared review record and
  asking later steps to infer approval from fields instead of routing by
  outcome type.
- `rubber-stamp-review`: approving because commands passed without checking
  whether the evidence proves the contracted behavior.
- `semantic-shift-dismissal`: treating meaning changes as harmless cleanup
  without reviewing their effect on contracts, schemas, or routing.
- `forge-mechanic-leakage`: embedding forge-specific commands or
  review-tool procedure in the protocol instead of the mechanics layer.

## Cross-References

- `workflow-contracts/review.toml` defines the C-2 review flow and its two
  disposition terminals.
- `skills/code-review/SKILL.md` defines the evaluation discipline.
- `schemas/change-approved.schema.json` and
  `schemas/change-needs-revision.schema.json` define the typed disposition
  artifacts.
- `docs/architecture/step-2-reference-arc-design.md` explains the
  artifact-versioned review cycle and typed disposition routing.
