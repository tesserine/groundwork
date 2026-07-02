# Step 1 R1 C-2 Contract Exercise

> **Historical note.** This is a session record from the ADR-0002
> methodology-sovereignty rollout, retained as history. It does not
> describe the present system; for that, read
> [`connecting-structure.md`](connecting-structure.md) and the substrate
> homes it links.

## Audience and Purpose

This note is for agents and contributors preparing Step 2 of ADR-0002's
methodology-sovereignty rollout. It records what the first source C-2 workflow
contract exercise proved, and what it did not prove.

## Result

Issue #317 exercised the C-2 workflow-contract format on the forge-neutral
`verify` protocol. The authored `workflow-contracts/verify.toml` contract held
as-authored against the current C-2 schema, parser graph checks, and manifest
registry resolution. No schema or parser revision was needed for this shape.

The exercise covered a three-node workflow with `always` edges, one
single-field `case` plus `default` branch, and two reachable terminals that
produce the same `completion-evidence` artifact.

## Remaining R1 Limits

This is narrow evidence, not broad validation of every C-2 capability. The
forge-touching arc still needs to exercise larger case sets, multi-field
decision pressure, loops with exits, and registry failures in production
authoring conditions.

Step 2 can proceed against the current C-2 format with that limitation named:
the format held for `verify`'s shape, while the arc remains the broader
format-fidelity test.
