---
name: resolve
description: >-
  Friction-resolution through the reconciling force. Use when encountering
  operational friction — a missing tool, broken config, stale convention,
  undocumented requirement, or any obstacle that the agent's default is to route
  around. Assesses the structural cause and resolves it permanently as a side
  quest before resuming the original task. Trigger signals: you are about to
  skip a step because something is not installed; you are writing a workaround
  instead of fixing the source; you used language like "for now" or "we can fix
  this later"; a tool produced an error you are about to ignore; you are doing a
  manual step that a tool should handle; you are making a decision that is not
  documented anywhere.
metadata:
  version: "2.1.0"
  updated: "2026-03-08"
---

# Resolve

*When two forces collide, introduce the third.*

When you hit operational friction — a missing tool, a broken config, a stale convention — you face a collision. Your drive to complete the current task pushes forward. The obstacle pushes back. The default response is to route around: find a workaround, keep moving. Both sides lose. The task proceeds on a degraded path, and the obstacle persists for every future session.

The reconciling move is to stop, step outside the collision, and resolve the obstacle structurally. This is the third force — neither suppressing the task nor accepting the obstacle, but transforming the situation so the task resumes on cleared ground.

This is a cross-cutting discipline, not a phase. It fires at any stage of work — framing, design, implementation, verification, landing — whenever the operational environment impedes progress.

## The Reconciling Move

Five steps. The side quest.

0. **Stop.** You have hit friction. Do not route around it. Do not continue the original task with a workaround. The instinct to keep moving is the failure mode this skill exists to catch. The fix you are about to make is infrastructure — its cost is paid once; its benefit recurs across every future session.

   Task momentum carries agents past friction before it even registers as a distinct event. Stop exists to interrupt this momentum. Without it, agents will assess the friction while simultaneously implementing a workaround, and the workaround — dressed as pragmatism — will win because it is downstream of task momentum.

1. **Step outside.** You are not debugging a bug — you are encountering an obstacle in the operational environment. Step outside both forces to see the collision clearly. Name the friction: what specifically is impeding progress? What category does it fall into? (See Recognition Patterns below.)

2. **Ground.** Apply `reckon`'s Orient: what should the operational environment enable here? What is the simplest structural state that would make this friction not exist — not just for you, but for every future agent? This is the grounded fix target. Do not design a workaround; design the absence of the obstacle. Your workaround instinct is diagnostic data — it shows you exactly what the environment *should* provide but does not. Use that insight to design the structural fix.

   This is a focused application of `reckon`'s Orient. The full six-step reckoning move is rarely needed for friction resolution — most friction has an obvious structural cause. But the orient question is essential: "What should the environment enable?" prevents designing a clever workaround when a simple structural fix is what is needed.

3. **Resolve.** Resolve the friction permanently. This is a bounded interruption to the original task, not a replacement for it. Execute the fix: install the tool, update the config, add the instruction, fix the convention, update the documentation. Verify the fix works before returning — run the tool, test the config, confirm the instruction is loadable. If the fix exceeds side-quest scope (see Scope Guidance below), file an issue and apply the minimum viable workaround — but the issue is mandatory.

4. **Return.** Resume the original task. The path is now clear. Both forces are honored: the task proceeds, and the environment is permanently improved.

---

## Recognition Patterns

These are the categories of friction. When you notice any of these, the instinct will be to route around. Stop. Introduce third force.

### 1. Missing Tool

A tool, binary, or dependency that should be available is not installed.

***Recognition:*** You are about to skip a step because a tool is not available, or you are about to implement a manual workaround for what the tool does. The workaround feels pragmatic — "I can do this without the tool."
***Fix:*** Install the tool. Add install instructions to project docs if the installation is non-obvious.

### 2. Broken Configuration

A configuration file is wrong, stale, or missing.

***Recognition:*** You are about to edit code to work around a configuration problem, or you are ignoring an error/warning because "it still works." Configuration drift is invisible friction — it does not block, but it degrades every operation.
***Fix:*** Fix the configuration at source.

### 3. Stale Convention

A documented convention no longer matches reality, or an undocumented convention is creating confusion.

***Recognition:*** You are following a convention that produces wrong results, or you are unsure which of two contradictory conventions to follow, or you are making a decision that every future agent will also need to make because the convention is not written down.
***Fix:*** Update the documentation. If the convention itself is wrong, fix the convention.

### 4. Missing Instruction

An important operational instruction is not in CLAUDE.md or another always-loaded file.

***Recognition:*** You just learned something the hard way that should have been obvious from the project's instructions, or you are about to make a decision that depends on undocumented project-specific knowledge.
***Fix:*** Add the instruction to the appropriate file.

### 5. Degraded Tooling

A tool is present but not working correctly or at reduced capability.

***Recognition:*** You are tolerating errors, warnings, or degraded output because "it mostly works." You have silently adopted a mental model of what the tool "actually" does versus what it claims to do.
***Fix:*** Fix the tool, update its configuration, or remove it if it is not earning its place.

### 6. Process Gap

A workflow step requires knowledge or action that is not part of any documented process.

***Recognition:*** You are about to perform a step that you know from prior context but that a fresh agent would not know, or you are about to skip a step because you do not know whether it applies.
***Fix:*** Document the process step. Update the relevant skill or file an issue.

---

## Scope Guidance

Not all friction resolution fits within a side quest. The distinction matters: an unbounded side quest becomes scope creep; a skipped side quest becomes accumulated friction.

### Inline side quest (resolve now)

- **The fix is under ~15 minutes of work.** Installing a tool, updating a config file, adding a CLAUDE.md instruction, fixing a path.
- **The fix is self-contained.** It does not require design decisions, behavioral changes to the system under development, or cross-cutting modifications.
- **The fix is immediately verifiable.** You can confirm it works before returning to the original task.

### File an issue (resolve later)

- **The fix requires design work.** The friction points to a structural problem that needs grounding, planning, or discussion.
- **The fix is large.** More than ~15 minutes, or touches multiple subsystems.
- **The fix has downstream dependencies.** Other work depends on the resolution, and the resolution needs to be sequenced.
- **The fix requires human judgment.** Policy decisions, tool selection, convention changes that affect the team.

When filing an issue, still apply a **minimum viable workaround** for the current session — but document the workaround in the issue so the permanent fix can remove it.

**The issue is mandatory.** If friction is too large to resolve inline, the issue is the structural fix that prevents it from being forgotten. Skipping the issue is the same failure mode as routing around the friction — it just happens at a different scale.

---

## Corruption Modes

**Routing around.** You encounter friction and continue with a workaround instead of resolving it. Recognition: you used language like "for now," "as a workaround," "we can fix this later," or "this is not blocking." Every "for now" is friction that compounds.

**Half-fix.** You resolved the immediate symptom without addressing the structural cause. Recognition: you fixed the problem for yourself but did not update the documentation, configuration, or instruction that would prevent the next agent from hitting it. The fix is local, not structural.

**Gold-plating.** You used friction as an excuse to redesign adjacent systems. Recognition: your "side quest" has grown to include changes that are not required to resolve the original friction. The fix is unbounded — you are improving, not clearing. Apply scope guidance: if it exceeds side-quest scope, file an issue and return.

**Fix-and-forget.** You resolved the friction but did not record the resolution. Recognition: you installed a tool or changed a config but did not update CLAUDE.md or any documentation. The next agent will encounter the same friction of *not knowing* the fix exists.

**Friction blindness.** You are not recognizing friction as friction. Recognition: you are consistently working around the same obstacle across multiple tasks, and it feels normal. If you find yourself doing the same manual step repeatedly, or if a fresh agent would be surprised by the step, it is friction.

**Premature issue.** You filed an issue for friction that could be resolved inline in under five minutes. Recognition: you are using the issue as a way to defer a trivial fix. The issue takes longer to write than the fix takes to apply. Just fix it.

---

## Cross-References

- `reckon`: Step 2 of the move uses `reckon`'s Orient to assess what the environment should enable. Full reckoning is rarely needed for friction resolution, but the orient question is essential.
- `orient`: carries the always-on documentation discipline that applies when the structural fix involves creating or updating docs.
- `decompose`: When friction exceeds side-quest scope, file an issue using `decompose`. The issue is the structural fix at the meta-level.
- `orient`: `resolve` is an integration principle in `orient`, alongside "Reckon re-fires" and "Research fires at any stage." It fires at any stage.
