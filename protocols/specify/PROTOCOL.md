---
name: specify
description: Protocol for writing and maintaining executable behavior specifications. Use when defining what a system should do, deciding what behavior to implement next, or expressing behavior as sentence-named Given/When/Then scenarios that produce the behavior-contract artifact.
metadata:
  version: "2.1.0"
  updated: "2026-03-17"
---

# Specify

Specify reframes testing as behavior specification: what the system should do,
under what context, with observable outcomes.

References:
- [Dan North: Introducing BDD](https://dannorth.net/introducing-bdd/)
- For concrete language-specific patterns, see [references/language-patterns.md](references/language-patterns.md)

## Goal

Drive development through sentence-named behaviors and Given/When/Then
structured scenarios.

This protocol produces the `behavior-contract` artifact: the executable
specification that downstream protocols and skills use as the source of truth.

## Discipline

These shape how behaviors are written. Each exists because the default produces
tests that do not serve as specification.

**Behavior before mechanics.** Ask "what should this do?" before "how to test
it?" The behavior question surfaces the right test; the mechanics question
optimizes the wrong one.

**Sentence-named tests.** Test names read as behavior statements. They form a
readable specification of the module. When test names are labels (`testAuth`,
`handleError`), the specification disappears and only the code remains.

> *Bad:* `test_parse_config`, `testUserAuth`, `it('handles errors')`
> *Good:* `rejects_expired_tokens_with_401`, `falls_back_to_default_when_config_missing`, `it('preserves line numbers in error messages')`

**Given/When/Then.** Every test has three phases: setup, action, assertion.
Given establishes context (only setup, no behavior). When performs one action
(the behavior trigger). Then verifies observable outcomes (not internals).
Mixing phases makes tests brittle and hard to read.

**One behavior per test.** Tests containing multiple behaviors mask which
behavior broke. Split them. Three small tests that each prove one thing are
better than one test that proves three.

**Behavior drives priority.** The next test is chosen by behavior gap
importance, not by what is convenient to test. This keeps the specification
growing toward complete coverage of what matters.

### Example: Complete Scenario

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

The test name is the specification line. The Given/When/Then structure makes
the behavior contract visible. The assertion checks observable outcome
(status code, error message), not internal state.

### Example: Bad to Good

```python
# Before - testing implementation
def test_token_validation():
    validator = TokenValidator()
    validator._cache = {}
    result = validator._parse_jwt(expired_token)
    assert result.internal_state == "expired"

# After - testing behavior
def test_rejects_expired_tokens_with_401():
    token = create_token(expires_at=one_hour_ago)
    response = client.get("/api/protected", headers=auth_header(token))
    assert response.status_code == 401
```

The before test breaks if internals change. The after test survives any
refactor that preserves the behavior.

## Procedures

### identify-next-behaviour

1. List existing behaviors from test names; these are the current
   specification.
2. Extract needed behaviors from acceptance criteria, work-unit description, or
   module purpose.
3. Compute missing behaviors (needed minus existing).
4. Rank by importance:
   - **Happy path first** - establishes the primary contract; error paths
     refine it.
   - **Core before edge** - the common case matters more than the rare case.
   - **Foundation before dependents** - behaviors that others build on come
     first.
   - **User-visible impact first** - behaviors users encounter directly before
     internal mechanics.
5. Pick the highest-priority missing behavior that can be expressed as one
   sentence.

### write-behaviour

1. Name the behavior as a sentence-style test name.
2. Write Given/When/Then structure.
3. **Red:** run and confirm failure. A test that passes immediately proves
   nothing; it means either the behavior already exists or the test does not
   check what it claims.
4. **Green:** implement minimal code to pass. Resist the urge to generalize.
5. **Refactor** while keeping the full suite green.

### deliver-behavior-contract

The capstone is delivery of the `behavior-contract` artifact. Invoke the
`behavior-contract` MCP tool. The object below is MCP tool input, not artifact
body. `instance_id` is a tool parameter that names the artifact instance; it is
extracted before validating artifact content, becomes the workspace filename,
and must not appear in the artifact body. Runa injects `work_unit` from session
context; the agent does not supply `work_unit`. Do not write the workspace JSON
file directly:

```
behavior-contract({
  instance_id: "<slug>",
  title: "<human-readable contract title>",
  scenarios: [{
    name: "<scenario name>",
    criterion: "<acceptance criterion this refines>",
    given: "<initial context>",
    when: "<action or event>",
    then: "<expected outcome>"
  }]
})
```

Runa validates the remaining artifact body fields against the
behavior-contract schema, persists the artifact, and records it in the artifact
store.

## Corruption Modes

**Vague names.** Test names that do not describe the behavior.
*Recognition:* You cannot reconstruct what the module does by reading test
names alone. Names are labels (`test_1`, `test_auth`) rather than behavior
statements.

**Missing Given.** Tests with unclear setup context; you cannot tell what
conditions the behavior requires.
*Recognition:* Reading the test, you cannot answer "under what circumstances
does this behavior apply?" Setup is implicit or buried in distant fixtures.

**Multi-behavior tests.** Tests that verify multiple behaviors in one case.
*Recognition:* A test failure could mean any of several behaviors broke. The
test has multiple When/Then sequences or assertions testing different things.

**Framework overthinking.** Choosing or debating test frameworks instead of
writing behaviors.
*Recognition:* You have spent time evaluating frameworks, configuring runners,
or comparing assertion libraries, but no behavior has been specified yet.

## Principles

**Words shape thinking.** Behavior vocabulary - "should," "when," "given" -
improves test design by forcing you to think about what the system does rather
than how it is built. The language is the method.

**Specification, not verification.** Tests are living executable
specifications. Their primary value is documenting what the system does, not
just catching regressions. A test suite you can read as a specification is
worth more than one you can only run.

**Delete freely.** Obsolete behavior tests should be removed. Tests that
describe behaviors nobody needs are noise, not safety.

## Cross-References

- `take`: session-level prioritization and execution sequencing.
- `decompose`: acceptance-criteria rigor, work-unit decomposition, and behavior traceability.
- `implement`: executes RED-GREEN-REFACTOR for specified behaviors.
- `verify`: requires fresh evidence for behavior-level completion claims.
