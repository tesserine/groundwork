# ADR-0007: Dimension-Agnostic Contract Machine

**Status:** Proposed — delivered for operator review with groundwork#492 \
**Date:** 2026-07-01 \
**Supersedes:** [ADR-0004](0004-contract-first-scoped-pipeline.md)'s behavior-contract-as-spine framing

## Context

ADR-0004 made the scoped pipeline contract-first, but the runtime surface
made behavior structurally privileged. The `behavior-contract` artifact
encoded scenario/gate forms, while documentation and code quality were
carried by prose conventions and late evidence sections. That shape made
new dimensions require new fields, bespoke lifecycle rules, or both.

Completion evidence had the same asymmetry: it recorded criterion coverage
through behavior-specific scenario/gate joins plus a documentation impact
section. Code quality had no equal evidence lane, and attested checks could
collapse into bare pass claims.

## Decision

The live contract artifact type is `contract`, not `behavior-contract`.
`take` produces one dimension-agnostic contract surface whose `criteria`
array can declare any dimension. Each criterion owns its `dimension`,
`acceptance_criterion`, `statement`, `hollow_delivery`, criterion-level
`check_kind`, and check descriptor. `check_kind` is never a dimension-level
property.

The live performed-evidence surface remains `completion-evidence`, but it
records `results[]` in one shape keyed by contract criterion id. Executable
criteria record run or artifact evidence. Attested criteria record reviewer
identity and finding. A bare pass is not evidence.

Detectability is generic. The same mechanism flags absent warranted
dimensions, hollow criteria, under-declared warranted criteria, unknown
evidence criteria, and declared contract criteria that have no completion
evidence. It does not special-case behavior.

## Consequences

- Adding a new dimension requires declaring criteria; it does not require a
  new artifact type, privileged field, or lifecycle branch.
- The contract remains the scoped pipeline spine, but behavior is no longer
  the schema spine.
- `implementation-plan` and `test-evidence` keep their existing
  scenario/gate internals until their separate leveling work. This ADR
  changes the contract and completion-evidence surfaces only.
- Runtime and documentation references to the live contract artifact use
  `contract`. Historical records may still name `behavior-contract` when
  describing the superseded design.
