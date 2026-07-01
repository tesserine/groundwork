---
name: implement
description: >-
  Execute the multidimensional contract through test-driven development:
  RED-GREEN-REFACTOR with delete-and-start-over discipline. Fires when
  production code is about to be written — implementing contracted
  behaviors, fixing bugs, or refactoring.
metadata:
  version: "2.3.0"
  updated: "2026-06-20"
  origin: "Adapted from obra/superpowers (MIT). See LICENSE-UPSTREAM."
---

# Implement

Write the test first. Watch it fail. Write minimal code to pass.

If you did not watch the test fail, you do not know whether it tests the
right thing.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Wrote code before the test? Delete it and start over. Not as reference, not
adapted while writing tests — deleted. The sunk cost is already spent; the
choice now is between code you can trust and code you cannot.

Every excuse for skipping this has been offered sincerely and every one
leads to untrusted code:
[references/anti-rationalization.md](references/anti-rationalization.md).

## Steps

Take the next behavior item from the contract in the deliverable's behavior
form (the plan orders them). Consult the `contract` skill
(`skills/contract/SKILL.md`) for the behavior lifecycle: a
runtime-behavior work-unit is driven by a scenario test for each executable
scenario, and a documentation-deliverable work-unit is driven by a
structural, coherence, and conformance gate for each gate-form behavior
item. Build toward all three declared dimensions — behavior,
documentation, and code quality — not behavior alone.

1. **RED — write one failing check.** The check name is the behavior
   statement. One behavior, real code over mocks
   ([references/testing-anti-patterns.md](references/testing-anti-patterns.md)),
   intent visible in the assertion or gate. For a runtime-behavior work-unit
   this is a scenario test; for a documentation-deliverable work-unit this
   is the structural, coherence, or conformance gate the contract names.

2. **Verify RED — watch the check fail.** Run the check. It must *fail*,
   not error, and fail because the behavior is missing — not a typo or
   import problem. A check that passes immediately proves nothing: fix the
   check.

3. **GREEN — write minimal code or documentation to pass.** The simplest
   change that satisfies the check and the relevant documentation or
   code-quality dimension. No extra parameters, no configuration, no error
   handling that no check requires. Over-engineering in GREEN is scope creep
   wearing a productivity mask. Where the minimal change involves a real
   design choice — a structure, an abstraction, a boundary — reckon it: open
   the resolved principles corpus at `~/.groundwork/principles/`, select the
   principles that govern the choice, and reason it from them rather than the
   nearest pattern (the reckon skill is the move). Dose-proportional — a
   trivial pass needs no reckon; a real structural choice does.

4. **Verify GREEN — watch it pass.** Run the check: it passes. Run the
   suite: everything else still passes, output pristine. A failing check
   means fix the change, not the check.

5. **REFACTOR — clean up on green.** Remove duplication, improve names,
   extract helpers. Tests stay green throughout; no behavior is added.
   Documentation outcomes and code-quality projections stay true while the
   internal form improves.

6. **Repeat** for the next behavior item. When every behavior item in scope
   has cycle evidence, and the documentation and code-quality dimensions have
   been advanced where declared, deliver (below).

Worked good/bad examples for each phase:
[references/cycle-examples.md](references/cycle-examples.md).

## Entering from a bug

1. Root cause unclear? Invoke `debug` first — investigation precedes fixes.
2. Write the failing test that reproduces the bug, named for the corrected
   behavior. If the bug reveals a behavior the contract missed, add the
   missing behavior item in the deliverable's behavior form — the contract
   stays the source of truth.
3. Run the cycle from step 2 above. The test remains as the regression
   guard.

## Recovering from a violation

Realized you wrote implementation before its test? Stop. Delete the
implementation. Start fresh from a failing test. Writing a test for
existing code is testing-after — it verifies what you built, not what
should be built.

## Deliver `test-evidence`

The capstone is delivery of the `test-evidence` artifact through the
`test-evidence` MCP tool in the deliverable's behavior form. For a
runtime-behavior work-unit, deliver scenario-keyed evidence. For a
documentation-deliverable work-unit, deliver gate-form evidence for
structural, coherence, and conformance gates. The object below is MCP tool
input, not artifact body. `instance_id` is a tool parameter that names the
artifact instance; it is extracted before validating artifact content,
becomes the workspace filename, and must not appear in the artifact body.
Runa injects `work_unit` from session context; the agent does not supply
`work_unit`. Do not write the workspace JSON file directly.

Scenario form:

```
test-evidence({
  instance_id: "<slug>",
  behavior_form: "scenario",
  evidence: [{
    scenario: "<scenario name from contract>",
    result: "pass",
    command: "<verification command>",
    output_summary: "<proof the test ran>"
  }]
})
```

Gate form:

```
test-evidence({
  instance_id: "<slug>",
  behavior_form: "gate",
  evidence: [{
    name: "<gate name from contract>",
    criterion: "<acceptance criterion this gate covers>",
    category: "structural" | "coherence" | "conformance",
    result: "pass",
    command: "<verification command>",
    output_summary: "<proof the check ran>"
  }]
})
```

Runa validates the remaining artifact body fields against the test-evidence
schema, persists the artifact, and records it in the artifact store.

This protocol owns per-cycle evidence — each behavior item watched failing,
then passing. The aggregate completion gate belongs to `verify`.

## When Stuck

| Problem | Solution |
|---------|----------|
| Do not know how to test | Write the wished-for API first; write the assertion first. |
| Test too complicated | The design is too complicated. Simplify the interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup is huge | Extract helpers. Still huge? Simplify the design. |

Hard to test means hard to use. Listen to the test.

## Corruption Modes

- `testing-after`: tests pass immediately on first run; you never saw them
  fail. You are verifying what you built, not specifying what to build.
- `cycle-violation`: skipping verify-RED or verify-GREEN; you do not know
  whether the test catches what it claims.
- `scope-creep-in-green`: the GREEN implementation does more than the test
  asks.
- `contract-bypass`: writing checks from implementation convenience ("test
  this function") instead of from the deliverable's behavior form.
- `rationalization`: any entry from the
  [anti-rationalization table](references/anti-rationalization.md) accepted
  as valid "just this once."

## Cross-References

- `contract` (skill): owns the behavior lifecycle, including executable
  scenarios for runtime behavior and structural, coherence, and conformance
  gate validation for documentation-deliverable behavior, plus the
  documentation and code-quality dimensions this protocol carries through the
  build.
- `plan` (protocol): supplies the decision-complete design and behavior-item
  ordering this protocol executes.
- `debug` (skill): owns root-cause investigation; hand off when a failure's
  cause is unclear, receive back a established root cause.
- `verify` (protocol): owns the aggregate completion gate after this
  protocol's per-cycle evidence.
- Documentation is written alongside code — doc comments and type
  annotations are GREEN/REFACTOR work, not an afterthought; `verify` checks
  the result.
