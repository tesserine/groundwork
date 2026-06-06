---
name: review
description: >-
  Review a submitted change proposal and produce exactly one disposition
  outcome. Routes approval through `change-approved` and blocking findings
  through `change-needs-revision`.
metadata:
  version: "1.0.0"
  updated: "2026-05-31"
---

# Review

Review is the gate between a submitted change proposal and landing. It decides
whether the current proposal version is safe to advance, then records that
decision as exactly one typed outcome artifact.

The protocol is not a forge operation. It names the methodology obligation:
inspect the proposed change, evaluate it against the work unit and evidence,
classify findings, and emit the disposition that downstream routing can trust.

## Purpose

Review protects the methodology from approving unexamined or ambiguous change.
It asks whether the proposal stays inside scope, preserves intended behavior,
has adequate verification evidence, and carries the documentation required by
the change.

The `code-review` skill supplies the cognitive discipline for this evaluation:
scope honesty, correctness, semantic-shift detection, evidence quality,
documentation impact, and fix-or-file judgment. Review uses that discipline to
produce a routing decision, not to encode a specific review tool.

## Disposition Routing

Review must produce exactly one member of the manifest-declared
`review-disposition` required-choice group:

- `change-approved` when the proposal has no blocking findings.
- `change-needs-revision` when at least one blocking finding remains.

The outcome artifact is the disposition. There is no disposition-agnostic review
record that later steps reinterpret, and there is no separate triage step
between review and land. Downstream protocols route on the produced artifact
type.

## Review Obligation

The reviewed proposal version must be known before the judgment is recorded.
The outcome's `against_version` names that proposal version so later review
rounds cannot be confused with earlier ones.

Findings must be classified at the point of review. Blocking findings prevent
approval and require the `change-needs-revision` outcome. Non-blocking findings
may be recorded only when they do not affect correctness, traceability,
documentation accuracy, or the ability to continue the workflow.

## Required-Choice Gate

The protocol's C-2 workflow contract terminates in two disposition terminals:
`approved` and `needs-revision`. The manifest registers those terminals as a
required output choice so a review run is invalid if it emits no disposition or
more than one disposition.

This gate preserves handle-only forge sovereignty: review consumes the
forge-neutral `change-proposal` artifact and produces methodology-owned outcome
artifacts. It does not prescribe how a reviewer inspects the
change.

## Corruption Modes

- `disposition-agnostic-routing`: emitting a shared review record and asking
  later steps to infer approval from fields instead of routing by outcome type.
- `rubber-stamp-review`: approving because commands passed without checking
  whether the evidence proves the changed behavior.
- `semantic-shift-dismissal`: treating meaning changes as harmless cleanup
  without reviewing their effect on contracts, schemas, or routing.
- `forge-mechanic-leakage`: embedding forge-specific commands or review-tool
  procedures in the protocol instead of leaving mechanics to the C-3 layer.

## Cross-References

- `workflow-contracts/review.toml` defines the C-2 review flow and its two
  disposition terminals.
- `skills/code-review/SKILL.md` defines the review discipline used to evaluate a
  proposal and classify findings.
- `schemas/change-approved.schema.json` and
  `schemas/change-needs-revision.schema.json` define the typed disposition
  artifacts produced by review.
- `docs/architecture/step-2-reference-arc-design.md` explains the
  artifact-versioned review cycle and typed disposition routing.
