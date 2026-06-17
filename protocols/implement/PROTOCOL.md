---
name: implement
description: >-
  Execute the behavior contract through test-driven development:
  RED-GREEN-REFACTOR with delete-and-start-over discipline. Fires when
  production code is about to be written — implementing contracted
  behaviors, fixing bugs, or refactoring.
metadata:
  version: "2.1.0"
  updated: "2026-06-17"
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

## Steps — the cycle, per scenario

Take the next behavior scenario from the contract (the plan's
`behavior_mapping` orders them), then:

1. **RED — write one failing test.** The test name is the scenario's
   behavior statement. One behavior, real code over mocks
   ([references/testing-anti-patterns.md](references/testing-anti-patterns.md)),
   intent visible in the assertion.

2. **Verify RED — watch it fail.** Run the test. It must *fail*, not error,
   and fail because the behavior is missing — not a typo or import problem.
   A test that passes immediately proves nothing: fix the test.

3. **GREEN — write minimal code to pass.** The simplest code that satisfies
   the test. No extra parameters, no configuration, no error handling that
   no test requires. Over-engineering in GREEN is scope creep wearing a
   productivity mask. Where the minimal code involves a real design choice
   — a structure, an abstraction, a boundary — reckon it: open the resolved
   principles corpus at `~/.groundwork/principles/`, select the principles
   that govern the choice, and reason it from them rather than the nearest
   pattern (the reckon skill is the move). Dose-proportional — a trivial
   pass needs no reckon; a real structural choice does.

4. **Verify GREEN — watch it pass.** Run the test: it passes. Run the
   suite: everything else still passes, output pristine. A failing test
   means fix the code, not the test.

5. **REFACTOR — clean up on green.** Remove duplication, improve names,
   extract helpers. Tests stay green throughout; no behavior is added.

6. **Repeat** for the next scenario. When every scenario in scope has its
   cycle evidence, deliver (below).

Worked good/bad examples for each phase:
[references/cycle-examples.md](references/cycle-examples.md).

## Entering from a bug

1. Root cause unclear? Invoke `debug` first — investigation precedes fixes.
2. Write the failing test that reproduces the bug, named for the corrected
   behavior. If the bug reveals a behavior the contract missed, add the
   scenario — the contract stays the source of truth.
3. Run the cycle from step 2 above. The test remains as the regression
   guard.

## Recovering from a violation

Realized you wrote implementation before its test? Stop. Delete the
implementation. Start fresh from a failing test. Writing a test for
existing code is testing-after — it verifies what you built, not what
should be built.

## Deliver `test-evidence`

The capstone is delivery of the `test-evidence` artifact. Invoke the
`test-evidence` MCP tool. The object below is MCP tool input, not artifact
body. `instance_id` is a tool parameter that names the artifact instance; it
is extracted before validating artifact content, becomes the workspace
filename, and must not appear in the artifact body. Runa injects `work_unit`
from session context; the agent does not supply `work_unit`. Do not write
the workspace JSON file directly:

```
test-evidence({
  instance_id: "<slug>",
  evidence: [{
    scenario: "<scenario name from behavior-contract>",
    result: "pass",
    command: "<verification command>",
    output_summary: "<proof the test ran>"
  }]
})
```

Runa validates the remaining artifact body fields against the test-evidence
schema, persists the artifact, and records it in the artifact store.

This protocol owns per-cycle evidence — each test watched failing, then
passing. The aggregate completion gate belongs to `verify`.

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
- `contract-bypass`: writing tests from implementation convenience ("test
  this function") instead of from named scenarios.
- `rationalization`: any entry from the
  [anti-rationalization table](references/anti-rationalization.md) accepted
  as valid "just this once."

## Cross-References

- `contract` (skill): each RED test corresponds to a named scenario; the
  carrying discipline lives there.
- `plan` (protocol): supplies the decision-complete design and scenario
  ordering this protocol executes.
- `debug` (skill): owns root-cause investigation; hand off when a failure's
  cause is unclear, receive back a established root cause.
- `verify` (protocol): owns the aggregate completion gate after this
  protocol's per-cycle evidence.
- Documentation is written alongside code — doc comments and type
  annotations are GREEN/REFACTOR work, not an afterthought; `verify` checks
  the result.
