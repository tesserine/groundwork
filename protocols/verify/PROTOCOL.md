---
name: verify
description: >-
  Protocol for gating completion claims with fresh verification evidence.
  Fires after execution, before claiming work is complete, fixed, or
  passing. Requires running verification commands and confirming output
  before making any success claims. Evidence before assertions, always.
metadata:
  version: "1.0.0"
  updated: "2026-03-09"
  origin: "Adapted from obra/superpowers (MIT). See LICENSE-UPSTREAM."
---

# Verify

Evidence before claims, always.

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you have not run the verification command in this message, you cannot
claim it passes. There are no exceptions to this rule.

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

## Lifecycle Role

This protocol owns **aggregate completion claims** — the moment before you
say "done." It fires after execution, before packaging work for review.

It does not own per-test cycle evidence (that belongs to the `implement`
protocol — each test watched failing, then passing). It owns the final
gate: all tests pass, all requirements met, the build succeeds, the work is
actually complete.

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Red Flags — STOP

These are signals that you are about to make an unverified claim. If you
notice any of these, stop and run the gate function.

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!")
- About to commit, push, or create a PR without verification
- Trusting agent success reports without independent verification
- Relying on partial verification to represent full results
- Thinking "just this once" or "this is a small change"
- Any wording implying success without having run verification

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

## Key Patterns

**Tests:**
```
Verified:  [Run test command] → [See: 34/34 pass] → "All tests pass"
Unverified: "Should pass now" / "Looks correct"
```

**Regression tests (red-green):**
```
Verified:  Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
Unverified: "I've written a regression test" (without red-green verification)
```

**Build:**
```
Verified:  [Run build] → [See: exit 0] → "Build passes"
Unverified: "Linter passed" (linter does not check compilation)
```

**Requirements:**
```
Verified:  Re-read plan → Create checklist → Verify each item → Report gaps or completion
Unverified: "Tests pass, phase complete"
```

**Agent delegation:**
```
Verified:  Agent reports success → Check VCS diff → Verify changes independently → Report actual state
Unverified: Trust agent report at face value
```

## When to Apply

**Always before:**
- Any variation of success or completion claims
- Any expression of satisfaction about work state
- Any positive statement about whether something works
- Committing, PR creation, task completion
- Moving to the next task
- Accepting delegated agent results

**The rule applies to:**
- Exact phrases ("Tests pass")
- Paraphrases and synonyms ("Everything looks good")
- Implications of success ("Ready for review")
- Any communication suggesting completion or correctness

### deliver-completion-evidence

The capstone is delivery of the `completion-evidence` artifact. Invoke the
`completion-evidence` MCP tool. The object below is MCP tool input, not
artifact body. `instance_id` is a tool parameter that names the artifact
instance; it is extracted before validating artifact content, becomes the
workspace filename, and must not appear in the artifact body. Runa injects
`work_unit` from session context; the agent does not supply `work_unit`. Do not
write the workspace JSON file directly:

```
completion-evidence({
  instance_id: "<slug>",
  criterion_coverage: [{
    criterion: "<acceptance criterion>",
    status: "covered",
    scenarios: ["<covering scenario names>"],
    failures: []
  }]
})
```

Runa validates the remaining artifact body fields against the
completion-evidence schema, persists the artifact, and records it in the
artifact store.

## Corruption Modes

**Performative verification.** Going through the motions without actually
checking. Running the command but not reading the output. Seeing a wall of
text and skipping to the claim. If the output did not change your
understanding, you did not verify.

**Partial verification as sufficient.** Running one test file instead of the
full suite. Checking the linter but not the build. Verifying the happy path
but not the error cases. Partial evidence supports partial claims — nothing
more.

**Stale evidence.** Citing output from a previous run instead of a fresh
execution. Code changed since the last run? The evidence is stale. Only
output from the current message counts.

**Claim-first, evidence-second.** Deciding the work is done, then looking
for evidence to confirm. This inverts the gate function. Evidence determines
the claim — the claim does not select the evidence.

## Cross-References

- `implement` owns per-test cycle evidence (each test watched failing, then
  passing). This protocol owns aggregate completion claims.
- `document` review fires after code changes, before this protocol's gate.
  Documentation accuracy is completion evidence.
- `submit` consumes this protocol's output — work must be verified before
  packaging for review.

## The Bottom Line

Run the command. Read the output. Then claim the result.

No shortcuts. No exceptions.
