---
name: contract
description: >-
  The behavior-driven development discipline: authoring the behavior contract
  at entry and carrying it unbroken through implementation, verification, and
  closure. Use when refining acceptance criteria into Given/When/Then
  scenarios, when deciding what behavior to implement next, and whenever code
  changes, tests, or completion claims need to stay traceable to specified
  behaviors instead of drifting toward implementation convenience.
metadata:
  version: "2.0.0"
  updated: "2026-06-11"
---

# Contract

The behavior contract is the executable definition of done. This skill is
the BDD home: it authors the contract where work begins (`take`) and carries
it as the source of truth through every later stage. Behavior is specified
once, then everything traces to it — plans link decisions to scenarios,
tests prove named scenarios, verification reports scenario-level coverage,
landing records what coverage shipped.

Reference: [Dan North, Introducing BDD](https://dannorth.net/introducing-bdd/).
Language-specific patterns:
[references/language-patterns.md](references/language-patterns.md).

## Authoring the Contract

1. **Start from the criteria.** Each work-unit acceptance criterion is
   refined into one or more scenarios. Every scenario names the criterion it
   refines — no orphan scenarios, no uncovered criteria.
2. **Ask behavior before mechanics.** "What should this do?" precedes "how
   to test it?" The behavior question surfaces the right scenario; the
   mechanics question optimizes the wrong one.
3. **Name scenarios as sentences.** A scenario name is a behavior statement
   readable as specification: `rejects_expired_tokens_with_401`, not
   `test_auth`. If the names alone don't describe what the system does, the
   specification has disappeared and only code remains.
4. **Structure as Given/When/Then.** Given establishes context (setup only),
   When performs one action (the behavior trigger), Then asserts observable
   outcomes — never internal state.
5. **One behavior per scenario.** A scenario proving three things masks
   which one broke. Split it.
6. **Rank by behavior gap.** Happy path first, core before edge, foundation
   before dependents, user-visible before internal.

### Example

```python
def test_rejects_expired_tokens_with_401():
    """Expired authentication tokens return 401, not a silent fallback."""
    # Given
    token = create_token(expires_at=one_hour_ago)
    client = create_test_client()

    # When
    response = client.get("/api/protected", headers=auth_header(token))

    # Then
    assert response.status_code == 401
    assert "expired" in response.json()["error"].lower()
```

The name is the specification line; the assertions check observable
outcomes. A test asserting `validator._cache` or `result.internal_state`
breaks on refactor and specifies nothing.

## Carrying the Contract

- **Implementation maps to behavior.** Every implementation increment names
  the scenario it advances. Each RED test corresponds to a named scenario.
  Work that cannot be traced to a scenario is unanchored — scope creep or a
  missing specification; resolve which before proceeding.
- **Behavior is the unit of progress.** Execution order follows behavior
  gaps, not code adjacency. Work advances by proving another scenario.
- **Completion is behavior coverage.** "All tests pass" is incomplete unless
  it names which scenarios those tests prove and which criteria those
  scenarios cover. Report coverage, not command output.

### When an existing test fails after a change

Classify before touching it:

- **Bug introduced** — the behavior is still required; fix the
  implementation.
- **Behavior moved** — the behavior lives elsewhere now; redirect the test.
- **Behavior obsolete** — the system no longer needs it; delete the test
  (and its scenario). Never weaken assertions to make a failure go away.

**Delete freely.** Scenarios and tests for behaviors nobody needs are noise,
not safety.

## Corruption Modes

**Contract dropoff.** The contract is treated as a phase that ended when
coding began. *Recognition:* completion claims say "tests pass" without
citing which behaviors have evidence.

**Testing implementation.** Assertions reference private fields, internals,
or intermediate state. *Recognition:* the test would break on a
behavior-preserving refactor.

**Vague names.** Test names are labels, not behavior statements.
*Recognition:* you cannot reconstruct what the module does from names alone.

**Multi-behavior scenarios.** One scenario, several When/Then sequences.
*Recognition:* a failure could mean any of several behaviors broke.

**Test hoarding.** Tests kept for behaviors the system no longer needs.
*Recognition:* fear of deleting because "they might catch something."

**Framework overthinking.** Evaluating test frameworks instead of writing
behaviors. *Recognition:* runners configured, assertion libraries compared,
no behavior specified yet.

## Principles

- **Words shape thinking.** "Given," "when," "then," "should" force thought
  about what the system does rather than how it is built. The language is
  the method.
- **Specification, not verification.** The contract's primary value is
  stating what the system does; catching regressions is the byproduct.

## Cross-References

- `take` (protocol): authors the contract at entry using this discipline.
- `plan` (protocol): maps scenarios to a decision-complete design.
- `implement` (protocol): executes RED-GREEN-REFACTOR per named scenario.
- `verify` (protocol): gates completion on scenario and criterion coverage.
- `land` (protocol): records shipped behavior coverage and explicit gaps.
