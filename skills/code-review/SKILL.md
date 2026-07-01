---
name: code-review
description: >-
  Use when reviewing a change proposal for scope honesty, correctness,
  semantic-shift detection, evidence quality, documentation impact, and
  fix-or-file discipline. Produces review judgment as cognitive content,
  not forge tooling.
metadata:
  version: "1.0.0"
  updated: "2026-05-31"
---

# Code Review

Review establishes whether a proposed change is safe to advance. It is not a
style pass and not a forge operation. The reviewer evaluates the change against
the work unit, contract, implementation plan, and verification
evidence, then classifies findings as blocking or non-blocking.

## Review Focus

**Scope honesty.** Confirm the change stays inside the claimed work. A change
outside the work unit is either removed or filed as follow-up work before
approval.

**Correctness.** Look for behavior regressions, broken interfaces, invalid
schemas, unreachable graph paths, stale fixtures, and tests that no longer prove
the behavior they name.

**Semantic-shift detection.** Treat "cleanup" skeptically when it changes
meaning. Renames, schema vocabulary changes, and routing changes are semantic
unless proven otherwise.

**Evidence quality.** Verification must be fresh and relevant to the claimed
behavior. Passing commands are not enough when the tests do not cover the
changed behavior.

**Documentation impact.** User-visible or authoring-surface changes require
documentation that explains the current behavior. Historical decision records may
name superseded designs, but current guides must not teach obsolete interfaces.

**Fix-or-file discipline.** Blocking findings must be fixed in the change before
approval. Non-blocking findings may be filed as follow-up only when the current
change remains correct without them.

## Finding Classification

- `blocking`: approval would ship incorrect behavior, misleading current docs,
  missing required evidence, scope creep, or a broken contract/interface.
- `non-blocking`: useful improvement that does not affect correctness,
  traceability, or the ability to continue the workflow.

## Corruption Modes

- `rubber-stamp-review`: approving because tests pass without checking whether
  the tests prove the claimed behavior.
- `style-substitution`: spending review attention on formatting preferences
  while missing behavior or contract drift.
- `scope-amnesia`: accepting unrelated changes because they are small.
- `historical-doc-rewrite`: editing decision records to hide superseded states
  instead of marking current guidance accurately.
