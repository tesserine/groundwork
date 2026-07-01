---
name: review
description: >-
  Review a submitted change proposal against the multidimensional contract
  and evidence, and produce exactly one disposition outcome. Routes approval
  through `change-approved` and blocking findings through
  `change-needs-revision`.
metadata:
  version: "2.3.0"
  updated: "2026-07-02"
---

# Review

Review is the judgment gate between a submitted change proposal and
landing. It is where the pipeline's one act of independent judgment about
the change happens: the proposal is examined against the multidimensional
contract, the work-unit, and the evidence — then the decision is recorded as
exactly one typed outcome artifact.

The protocol is not a forge operation. The `code-review` skill supplies the
evaluation discipline; this protocol supplies the routing obligation.
It consults the `contract` skill (`skills/contract/SKILL.md`) for the
lifecycle, and judges every declared dimension through the same join:
`contract.criteria[]` against `completion-evidence.results[]`, one
performed result per criterion.

## Steps

1. **Resolve the reviewed version.** Identify the current `change-proposal`
   version for this work unit. The disposition's `against_version` names it;
   without that binding, later rounds cannot be told from earlier ones.

2. **Inspect against the contract.** Evaluate the proposed change with the
   `code-review` skill's discipline: scope honesty against the work-unit,
   correctness, semantic-shift detection, and evidence quality against the
   multidimensional contract and completion evidence. The contract is the
   measure — a change is judged by whether every declared dimension's
   performed validation is delivered and proven, not by whether commands
   passed. Join `contract.criteria[]` with `completion-evidence.results[]`
   and judge each criterion by the evidence its `check_kind` warrants: run
   or artifact evidence for executable criteria — scenario tests and
   structural, coherence, and conformance gates among them — and reviewer
   attestations with substantive findings for attested criteria, the
   documentation dimension's audience-outcome findings and the code-quality
   dimension's diff loci among them. The same join judges every dimension.
   Consult the `contract` skill for the lifecycle; this protocol judges it,
   it does not restate it.

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

   Judge the close path through the existing proposal, completion evidence,
   and review disposition context: the per-criterion results in
   `completion-evidence.results[]` are the committed, reviewable evidence
   for every declared dimension — behavior, documentation, and code quality
   in the same surface.

## The Independence of the Gate

Review is the scoped pipeline's independent-judgment gate. Transition
authority lives in this typed disposition, not in per-operation approval
elsewhere (per runa's session-surface contract) — so what the gate enforces
is not a human signature but **independence from the author**: the change is
judged by a context that did not produce it. The author's own momentum must
never approve itself.

Independence is satisfied by a context separate from the one that built the
change — a fresh or separate agent context by default, the operator when
chosen. The capstone is the same typed outcome either way, and the
disposition records the reviewer identity. Who reviews is a choice; that the
reviewer is independent of the author is the invariant.

## Corruption Modes

- `disposition-agnostic-routing`: emitting a shared review record and
  asking later steps to infer approval from fields instead of routing by
  outcome type.
- `rubber-stamp-review`: approving because commands passed without checking
  whether the evidence proves every declared dimension. A behavior-only
  approval that ignores documentation or code-quality validation is a rubber
  stamp even when the behavior evidence passes.
- `semantic-shift-dismissal`: treating meaning changes as harmless cleanup
  without reviewing their effect on contracts, schemas, or routing.
- `forge-mechanic-leakage`: embedding forge-specific commands or
  review-tool procedure in the protocol instead of the mechanics layer.

## Cross-References

- `workflow-contracts/review.toml` defines the C-2 review flow and its two
  disposition terminals.
- `skills/code-review/SKILL.md` defines the evaluation discipline.
- `contract` (skill): owns the lifecycle and dimensions this protocol
  consults while judging validation-performed.
- `schemas/change-approved.schema.json` and
  `schemas/change-needs-revision.schema.json` define the typed disposition
  artifacts.
- `docs/architecture/step-2-reference-arc-design.md` explains the
  artifact-versioned review cycle and typed disposition routing.
