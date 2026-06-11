# Gate Patterns

Reference for verify: what each claim requires, the signals that an
unverified claim is about to be made, and the rationalizations that
precede one.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = the claim has no basis
```

## What Each Claim Requires

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test of original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Verified vs Unverified

**Tests:**
```
Verified:   [Run test command] → [See: 34/34 pass] → "All tests pass"
Unverified: "Should pass now" / "Looks correct"
```

**Regression tests (red-green):**
```
Verified:   Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
Unverified: "I've written a regression test" (without red-green verification)
```

**Build:**
```
Verified:   [Run build] → [See: exit 0] → "Build passes"
Unverified: "Linter passed" (linter does not check compilation)
```

**Requirements:**
```
Verified:   Re-read plan → Create checklist → Verify each item → Report gaps or completion
Unverified: "Tests pass, phase complete"
```

**Agent delegation:**
```
Verified:   Agent reports success → Check VCS diff → Verify changes independently
Unverified: Trust agent report at face value
```

## Red Flags — STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!")
- About to commit or package for review without verification
- Trusting agent success reports without independent verification
- Relying on partial verification to represent full results
- Thinking "just this once" or "this is a small change"
- Any wording implying success without having run verification

The rule applies to exact phrases, paraphrases, implications of success
("Ready for review"), and any communication suggesting completion.

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | Run the verification |
| "I'm confident" | Confidence is not evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter is not compiler |
| "Agent said success" | Verify independently |
| "Partial check is enough" | Partial proves nothing about the whole |
| "Different words so rule doesn't apply" | Spirit over letter — any success claim requires evidence |
