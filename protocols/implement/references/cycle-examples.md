# Cycle Examples

Worked examples for each phase of RED-GREEN-REFACTOR.

## RED — a good failing test

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
# Bad: vague name, tests the mock not the code
def test_retry_works():
    mock = Mock(side_effect=[RuntimeError(), RuntimeError(), "success"])
    retry_operation(mock)
    assert mock.call_count == 3
```

## Verify RED — what counts as failing correctly

- The test fails — a syntax error or import error is not a RED test.
- The failure message matches expectations.
- It fails because the feature is missing, not because of a typo.

Test passes immediately? You are testing existing behavior — fix the test.
Test errors? Fix the error and re-run until it fails correctly.

## GREEN — minimal means minimal

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
# Bad: over-engineered — the test asked for none of this
def retry_operation(
    fn,
    max_retries=3,
    backoff="linear",
    backoff_base=1.0,
    on_retry=None,
    retry_filter=None,
):
    ...
```

## Test quality

| Quality | Good | Bad |
|---------|------|-----|
| **Minimal** | One thing. "and" in the name? Split it. | `test_validates_email_and_domain_and_whitespace` |
| **Clear** | Name describes behavior | `test_1`, `test_it_works` |
| **Shows intent** | Demonstrates the desired API | Obscures what the code should do |
