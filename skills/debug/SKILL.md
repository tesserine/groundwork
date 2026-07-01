---
name: debug
description: >-
  Root-cause investigation discipline. Use when a test fails, behavior is
  unexpected, or any failure occurs — before proposing fixes. Enforces
  structured investigation before fix attempts. Fires at any stage
  when failures appear. If you are about to fix something without understanding
  why it broke, this skill applies.
metadata:
  version: "1.1.0"
  updated: "2026-06-11"
  origin: "Adapted from obra/superpowers (MIT). See LICENSE-UPSTREAM."
---

# Debug

*Find root cause before fixing. Symptom fixes are failure.*

## The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

Proposed a fix before understanding the cause? Retract it — not kept as a
"working theory," not tested "just to see," not proposed alongside
investigation. Investigate from evidence. No exceptions.

The failure is not a phase: it surfaces during framing, planning,
execution, verification, and landing alike. The trigger is the failure,
not the stage. "Unexpected" is only meaningful relative to a defined
expectation — check the contract first.

## The Investigation Move

Five steps. Always the same.

0. **Stop.** Do not guess, fix, or propose. Fix momentum carries agents
   past failures before investigation registers as a distinct activity;
   every guess that happens to work teaches nothing and leaves the actual
   cause in place.

1. **Read.** The actual error output, all of it: full stack trace, error
   messages, exit codes, the warnings that preceded the failure, the exact
   assertion that failed. Most root causes are stated plainly in output
   that was skimmed. Read before interpreting.

2. **Reproduce.** Confirm you can trigger the failure reliably: exact
   steps, consistent or intermittent, what changed recently (diff, recent
   commits, dependencies, config, environment). If you cannot reproduce,
   gather more data — you cannot verify a fix for a failure you cannot
   trigger.

3. **Trace.** Backward from symptom to source. The error manifests at one
   point; the bug rarely lives there. Find where the bad value appears,
   find its producer, ask what called it with bad input, and keep tracing
   up until valid data becomes invalid — that transition is the root
   cause. Fix there, not at the symptom. When manual tracing is blocked,
   instrument: log value and call stack per level, run once, analyze the
   evidence — do not interleave gathering and fixing. After fixing at
   source, consider validation at each layer the data crosses:
   [references/defense-in-depth.md](references/defense-in-depth.md).

4. **Hypothesize and test.** One specific hypothesis: "the root cause is X
   because evidence Y shows Z." Smallest possible change, one variable at a
   time. Confirmed → hand off to `implement` fix-bug. Wrong → form a new
   hypothesis from the evidence; never stack fixes on a failed one.

## The 3-Fix Escalation Rule

Count your fix attempts. Three fixes and the failure persists? **Stop
fixing. Question the architecture.** The pattern: each fix reveals a new
issue elsewhere, fixes demand massive refactoring, the root cause keeps
shifting. When it fires:

1. Do not attempt fix #4.
2. Invoke `reckon` — is the pattern fundamentally sound, or is the design
   carrying inherited complexity?
3. Architecture sound → the investigation was incomplete; return to Step 0
   with the evidence from the three attempts.
4. Architecture unsound → the fix is architectural; file it through
   `decompose` — that exceeds debugging scope.

## Pattern Analysis

When tracing does not expose the root cause, compare against known-good:
find a working example of the same pattern, read it completely (partial
understanding of a pattern guarantees bugs), list every difference however
small, and check what dependencies, config, or environment the working
version assumes.

## Recognition Index

When any of these fires, stop and return to Step 0. Full expositions and
the anti-rationalization table:
[references/recognition.md](references/recognition.md).

| Signal | One-line trigger |
|---|---|
| Premature fix | A fix in mind before the data flow is traced. |
| Fix stacking | A new change on top of an unremoved failed fix. |
| Symptom treatment | A guard, catch, or default at the error site. |
| Evidence-free hypothesis | "It is probably X" with no evidence cited. |
| Investigation fatigue | "Just try something" because investigation feels slow. |

## Corruption Modes

**Guess-and-check** — a series of edits followed by test runs, fixes
before root causes. **Symptom-fixing** — absorbing invalid data downstream
instead of at its origin. **Fix-stacking** — uncommitted changes from
failed hypotheses leaving the codebase in an unknown state.
**Investigation-without-action** — extensive notes, no converging
hypothesis; investigation serves hypothesis formation. **Process as
theater** — investigation that confirms the initial intuition at every
step is rationalizing, not investigating.

## Cross-References

- `implement` (protocol): owns the fix execution cycle. Root cause
  established here hands off to its fix-bug entry; this skill writes no
  tests and implements no fixes.
- `verify` (protocol): owns fix verification — this skill investigates.
- `reckon` (skill): the 3-fix rule escalates there; the move shares its
  discipline of establishing truth before acting.
- `resolve` (skill): when investigation reveals the failure is operational
  friction (missing tool, broken config, stale convention), the root cause
  is environmental — hand off.
- `contract` (skill): the contract defines what "expected" means.
