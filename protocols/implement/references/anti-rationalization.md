# Anti-Rationalization

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
| "Need to explore first" | Fine. Throw away the exploration, start with a test. |
| "Test hard = skip TDD" | Listen to the test. Hard to test means hard to use. |
| "TDD will slow me down" | Test-driven execution is faster than debugging. |
| "Manual test is faster" | Manual testing does not prove edge cases. You will re-test every change. |
| "Existing code has no tests" | You are improving it. Add tests for existing code. |

## Red Flags — Stop and Start Over

Any of these means: delete the code, start over with a failing test.

- Code written before test
- Test written after implementation
- Test passes immediately on first run
- Cannot explain why a test failed
- Tests deferred to "later"
- Rationalizing "just this once"
- "I already manually tested it"
- "Tests after achieve the same purpose"
- "It's about spirit not ritual"
- "Keep as reference" or "adapt existing code"
- "Already spent X hours, deleting is wasteful"
- "TDD is dogmatic, I'm being pragmatic"
- "This is different because..."
