# Recognition Patterns and Anti-Rationalization

The signals that you are about to violate debug's Iron Law, and the
excuses that precede a violation. When any of these fires, stop and
return to Step 0 of the investigation move.

## Recognition Patterns

### 1. Premature Fix

You are proposing a solution before completing investigation.

***Recognition:*** You have not traced the data flow, but you have a fix in mind. The fix "seems obvious." You are about to say "I think the issue is X, let me fix it."
***Corrective:*** "Have I traced to root cause, or am I guessing from symptoms?" Return to Trace.

### 2. Fix Stacking

You are adding fixes on top of previous failed fixes.

***Recognition:*** Your previous fix did not work, and you are about to make another change without removing the first fix or re-analyzing. The codebase now has two changes, neither of which you understand fully.
***Corrective:*** Revert the failed fix. Return to Step 0 with new evidence.

### 3. Symptom Treatment

You are fixing where the error appears rather than where it originates.

***Recognition:*** Your fix adds a null check, a try/catch, a default value, or a conditional at the error site. The bad data still flows through the system — you are just catching it later.
***Corrective:*** "Am I fixing the source or the symptom?" Return to Trace.

### 4. Evidence-Free Hypothesis

You are guessing without evidence.

***Recognition:*** Your hypothesis does not reference specific evidence from Read/Reproduce/Trace. You are reasoning from how the code "should" work rather than from what it actually does. You are about to say "it is probably X."
***Corrective:*** "What specific evidence supports this hypothesis?" If none, return to Read.

### 5. Investigation Fatigue

You are tempted to skip investigation because prior attempts failed.

***Recognition:*** You have been investigating for a while without progress. The instinct is to "just try something and see." This is the most dangerous moment — fatigue makes guess-and-check feel like progress.
***Corrective:*** Take a different angle. Add more instrumentation. Narrow the reproduction. Do not abandon methodology when it feels slow — abandoning it is slower.

## Anti-Rationalization

Every excuse in this table has been offered sincerely. Every one leads to
thrashing.

| Excuse | Reality |
|--------|---------|
| "The issue is simple, I do not need the process" | Simple issues have root causes too. Investigation is fast for simple bugs. |
| "Emergency, no time for process" | Systematic investigation is faster than guess-and-check thrashing. |
| "Just try this first, then investigate" | The first guess sets the pattern. Do it right from the start. |
| "I see the problem, let me fix it" | Seeing the symptom is not understanding the root cause. |
| "Multiple fixes at once saves time" | Cannot isolate what worked. Creates new bugs. |
| "The reference is too long, I will adapt the pattern" | Partial understanding guarantees bugs. Read it completely. |
| "One more fix attempt" (after 2+ failures) | 3+ failures = architectural problem. Question the pattern. |
| "I do not fully understand, but this might work" | "Might work" is guessing. Investigate until you understand. |
