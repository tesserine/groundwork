---
name: implement
description: >-
  Protocol for executing any feature or bugfix against a behavior contract
  and implementation plan. Enforces test-driven development through
  RED-GREEN-REFACTOR with delete-and-start-over discipline. Fires when
  production code is about to be written — implementing
  behavior-contract-defined behaviors, fixing bugs, or refactoring.
metadata:
  version: "1.0.0"
  updated: "2026-03-08"
  origin: "Adapted from obra/superpowers (MIT). See LICENSE-UPSTREAM."
---

# Implement

Write the test first. Watch it fail. Write minimal code to pass.

If you did not watch the test fail, you do not know if it tests the right
thing.

## The Iron Law

```
NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST
```

Wrote code before the test? Delete it. Start over.

- Do not keep it as "reference"
- Do not "adapt" it while writing tests
- Do not look at it
- Delete means delete

Implement fresh from tests. No exceptions.

## Lifecycle Role

This protocol is the execution discipline in groundwork's topology. It sits
between behavior identification and completion verification:

1. `specify` identifies what behaviors the system needs — sentence-named scenarios
   in Given/When/Then form.
2. **`implement` executes** those behaviors through RED-GREEN-REFACTOR. Each RED
   test corresponds to a named behavior scenario from `specify`.
3. `verify` gates the completion claim with
   behavior-level evidence.

This protocol owns per-test cycle evidence: each test was watched failing,
then passing. It does not own aggregate completion evidence — that belongs
to `verify`.

## Discipline

Each discipline exists because the default — what happens without it —
produces code that cannot be trusted.

**One test at a time.** Write one failing test, make it pass, refactor. Then
the next. Multiple failing tests at once diffuse focus and invite shortcuts.

**Verify RED.** Run the test and confirm it fails. Confirm it fails for the
expected reason — missing feature, not a typo or import error. A test that
passes immediately proves nothing: it either tests existing behavior or does
not test what it claims.

**Verify GREEN.** Run the test and confirm it passes. Confirm all other tests
still pass. Pristine output — no errors, no warnings.

**Minimal GREEN.** Write the simplest code that passes the test. Do not add
features, refactor other code, or "improve" beyond what the test requires.
Over-engineering in GREEN is scope creep wearing a productivity mask.

**Refactor only when green.** After GREEN, clean up: remove duplication,
improve names, extract helpers. Keep tests green throughout. Do not add
behavior during refactor.

**Delete-and-start-over.** If you wrote implementation code before the test:
delete the code and start with a failing test. No keeping it as reference. No
adapting it. The sunk cost is already gone. The choice is between code you can
trust (test-driven) and code you cannot (implementation-first).

## Red-Green-Refactor

### RED — Write Failing Test

Write one minimal test showing what should happen. The test name is a behavior
statement — it reads as specification.

```python
# Good: clear name, tests real behavior, one thing
def test_retries_failed_operations_three_times():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("fail")
        return "success"

    result = retry_operation(operation)

    assert result == "success"
    assert attempts == 3
```

```python
# Bad: vague name, tests mock not code
def test_retry_works():
    mock = Mock(side_effect=[RuntimeError(), RuntimeError(), "success"])
    retry_operation(mock)
    assert mock.call_count == 3
```

Requirements:
- One behavior per test
- Clear sentence-style name
- Real code — mocks only when unavoidable (see
  [references/testing-anti-patterns.md](references/testing-anti-patterns.md))

### Verify RED — Watch It Fail

**Mandatory. Never skip.**

Run the test. Confirm:
- The test fails (not errors — a syntax error is not a RED test)
- The failure message matches expectations
- It fails because the feature is missing, not because of typos

Test passes immediately? You are testing existing behavior. Fix the test.

Test errors? Fix the error, re-run until it fails correctly.

### GREEN — Minimal Code

Write the simplest code to pass the test.

```python
# Good: just enough to pass
def retry_operation(fn, max_retries=3):
    for i in range(max_retries):
        try:
            return fn()
        except Exception:
            if i == max_retries - 1:
                raise
```

```python
# Bad: over-engineered
def retry_operation(
    fn,
    max_retries=3,
    backoff="linear",
    backoff_base=1.0,
    on_retry=None,
    retry_filter=None,
):
    # YAGNI — the test asked for none of this
    ...
```

Do not add features, refactor other code, or "improve" beyond the test.

### Verify GREEN — Watch It Pass

**Mandatory.**

Run the test. Confirm:
- The test passes
- All other tests still pass
- Output is pristine (no errors, no warnings)

Test fails? Fix the code, not the test.

Other tests fail? Fix now — do not proceed with a broken suite.

### REFACTOR — Clean Up

After GREEN only:
- Remove duplication
- Improve names
- Extract helpers

Keep tests green. Do not add behavior.

### Repeat

Next failing test for the next behavior.

## Good Tests

| Quality | Good | Bad |
|---------|------|-----|
| **Minimal** | One thing. "and" in name? Split it. | `test_validates_email_and_domain_and_whitespace` |
| **Clear** | Name describes behavior | `test_1`, `test_it_works` |
| **Shows intent** | Demonstrates desired API | Obscures what code should do |

## Procedures

### implement-behavior

Execute the RED-GREEN-REFACTOR cycle for a behavior identified by `specify`.

1. Take the next behavior scenario from `specify`'s priority ranking.
2. Write a failing test whose name is the behavior statement.
3. **Verify RED** — run the test, confirm it fails for the right reason.
4. Write minimal code to pass.
5. **Verify GREEN** — run the test, confirm it passes, confirm suite is green.
6. Refactor while keeping tests green.
7. Repeat for the next behavior.

### fix-bug

Enter the RED-GREEN-REFACTOR cycle from a bug report.

1. If the root cause is unclear, invoke `debug` first — it owns
   root-cause analysis methodology.
2. Write a failing test that reproduces the bug. The test name describes the
   corrected behavior, not the bug.
3. **Verify RED** — confirm the test fails, demonstrating the bug.
4. Fix the code with the minimum change to pass the test.
5. **Verify GREEN** — confirm the test passes and the suite is green.
6. The test now serves as a regression guard.

### recover-from-violation

When you realize you wrote implementation code before a test:

1. **Stop.** Do not write a test for existing code — that is testing-after.
2. **Delete** the implementation code. No keeping it as reference.
3. **Start fresh** with a failing test.
4. Implement from the test.

This feels wasteful. It is not. The time spent writing code-first is already
gone. The choice now is between trusted code (test-driven) and untrusted code
(implementation-first with tests bolted on). Trusted code is faster in the
long run.

### deliver-test-evidence

The capstone is delivery of the `test-evidence` artifact. Invoke the
`test-evidence` MCP tool. The object below is MCP tool input, not artifact
body. `instance_id` is a tool parameter that names the artifact instance; it is
extracted before validating artifact content, becomes the workspace filename,
and must not appear in the artifact body. Runa injects `work_unit` from session
context; the agent does not supply `work_unit`. Do not write the workspace JSON
file directly:

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

## Anti-Rationalization

Every excuse in this table has been offered sincerely. Every one leads to
untrusted code.

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. The test takes 30 seconds. |
| "I'll test after" | Tests passing immediately prove nothing. |
| "Tests after achieve same goals" | Tests-after ask "what does this do?" Tests-first ask "what should this do?" |
| "Already manually tested" | Ad-hoc is not systematic. No record, cannot re-run. |
| "Deleting X hours is wasteful" | Sunk cost fallacy. Keeping unverified code is technical debt. |
| "Keep as reference, write tests first" | You will adapt it. That is testing-after. Delete means delete. |
| "Need to explore first" | Fine. Throw away exploration, start with a test. |
| "Test hard = skip TDD" | Listen to the test. Hard to test means hard to use. |
| "TDD will slow me down" | Test-driven execution is faster than debugging. |
| "Manual test is faster" | Manual testing does not prove edge cases. You will re-test every change. |
| "Existing code has no tests" | You are improving it. Add tests for existing code. |

## Red Flags — Stop and Start Over

Any of these means: delete code, start over with the `implement` discipline.

- Code written before test
- Test written after implementation
- Test passes immediately on first run
- Cannot explain why test failed
- Tests deferred to "later"
- Rationalizing "just this once"
- "I already manually tested it"
- "Tests after achieve the same purpose"
- "It's about spirit not ritual"
- "Keep as reference" or "adapt existing code"
- "Already spent X hours, deleting is wasteful"
- "TDD is dogmatic, I'm being pragmatic"
- "This is different because..."

## When Stuck

| Problem | Solution |
|---------|----------|
| Do not know how to test | Write the wished-for API first. Write the assertion first. Ask the user. |
| Test too complicated | Design too complicated. Simplify the interface. |
| Must mock everything | Code too coupled. Use dependency injection. |
| Test setup is huge | Extract helpers. Still complex? Simplify the design. |

## Corruption Modes

**Testing-after.** Writing implementation first, then adding tests to confirm
it works.
*Recognition:* Tests pass immediately on first run. You never saw them fail.
You are verifying what you built, not specifying what should be built.

**Rationalization.** Accepting any excuse from the anti-rationalization table
as valid for this particular case.
*Recognition:* You are using words like "pragmatic," "just this once," "spirit
not ritual," or "this is different because."

**Cycle violation.** Skipping verify-RED or verify-GREEN.
*Recognition:* You wrote the test and implementation without running the test
between them. You do not know if the test actually catches the bug it claims
to test.

**Scope creep in GREEN.** Adding features, refactoring, or "improving" beyond
what the failing test requires.
*Recognition:* Your GREEN implementation does more than the test asks for. You
added parameters, configuration, or error handling that no test requires.

**Behavior-contract bypass.** Starting RED tests without identified behavior
scenarios.
*Recognition:* You are writing tests from implementation convenience —
"test this function" — rather than from behavior contract — "this behavior
should exist." The handoff from `specify` was skipped.

## Principles

**Order matters.** Tests written after code pass immediately. Passing
immediately proves nothing — you might test the wrong thing, test
implementation instead of behavior, or miss edge cases. Testing from the first
cycle forces you
to see the test fail, proving it actually tests something.

**Delete is faster than debug.** Sunk cost fallacy says keep the code you
wrote. Reality says rewriting from tests is faster than debugging
untested code later.

**Hard to test means hard to use.** When testing is difficult, the test is
telling you the design needs work. Listen to the test.

**Test-driven execution is pragmatic.** It finds bugs before commit, prevents
regressions, documents behavior, and enables safe refactoring. Shortcuts that
skip the `implement` discipline are slower, not faster.

## Cross-References

- `specify` (protocol): identifies behaviors before this protocol executes
  the cycle. Each RED test corresponds to a named behavior scenario from
  `specify`.
- `verify` (protocol): owns behavior-level completion evidence. This
  protocol owns per-test cycle evidence (watched it fail, watched it pass).
- `debug` (skill): owns root-cause analysis. This protocol provides the
  entry point ("write a failing test reproducing the bug") but defers
  methodology to the `debug` skill when root cause is unclear.
- `document` (protocol): doc comments and type annotations are written
  alongside code during GREEN and REFACTOR phases — they are implementation
  work, not afterthought.
