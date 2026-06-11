# Assumed-Constraint Patterns

These fire on all first-principles work — design, analysis, strategy,
decomposition. When you notice any of these, stop and reckon.

## 1. Problem-as-Given

Accepting the problem statement without questioning scope, framing, or premises.

***Recognition:*** You are optimizing within the frame you were handed. You have not asked whether the frame is correct.
***Corrective:*** "What problem are we actually solving? Is this the right question, or the question we were given?"

## 2. Description as Design

Treating what the current system does as the definition of what it should do — documenting what is instead of designing what's needed.

***Recognition:*** Your "requirements" are descriptions of existing behavior. Every claim traces to existing code or configuration; none trace to user needs. You read the implementation and organized your findings instead of asking what it must enable.
***Corrective:*** "If this implementation did not exist, what would users need?" Start from the need. Use the existing implementation for gap analysis only after the design exists.

## 3. Borrowed Structure

Importing categories, patterns, or architecture from adjacent systems without verifying fit.

***Recognition:*** Your design's structure mirrors an adjacent system, a familiar pattern, or the categories in the request. You did not derive them from requirements — you inherited them. The analogy feels natural, perhaps too natural.
***Corrective:*** "What structure would emerge from the requirements alone?" Design fresh. Compare with the inherited structure afterward. Identify where the analogy breaks.

## 4. Precedent as Constraint

Treating past decisions, existing implementations, or prior investment as requirements.

***Recognition:*** "We did it this way before," "the existing system does X," or "we already invested in Y" appears in your reasoning as constraint rather than data point. The existing solution is your design starting point rather than a comparison target.
***Corrective:*** Precedent is evidence, not constraint. Past investment is irrelevant to future value. "If this precedent did not exist, what would we build?"

## 5. Complexity Preservation

Maintaining complexity because removing it seems risky.

***Recognition:*** You are preserving structure not because it serves current requirements, but because removing it might break something you do not understand — or adding structure for requirements that do not yet exist.
***Corrective:*** "What is the simplest design that meets requirements?" If simpler than what exists, the complexity needs justification or removal.

## 6. Audience Assumption

Designing for the requester, yourself, or an imagined user rather than verified actual users.

***Recognition:*** You have not identified who this serves. You are designing for the voice in the prompt.
***Corrective:*** "Who actually uses this? What do they actually need?" Ground the audience before grounding the design.

## 7. Abstraction Gravity

Defaulting to the abstraction level of adjacent or existing systems.

***Recognition:*** Your design operates at the same abstraction level as the system it replaces or resembles. You adopted this level implicitly — you cannot articulate why it is correct for this problem. The decision was inherited, not made.
***Corrective:*** "What abstraction level does this problem actually require?" The existing system's level is a data point, not a default.

## 8. Local Coherence

A detail follows a valid pattern and sounds right in isolation, but contradicts the purpose established in Orient.

***Recognition:*** Your output would be correct in a generic context — it follows established engineering conventions, uses appropriate technical language, and reads as a reasonable decision. But you have not checked it against the specific purpose of this work. The fluency of the output masks the contradiction. Common vectors: failure-mode defaults that negate the feature ("if the safety check fails, skip it"), error paths that undo the work, fallbacks to the behavior the feature exists to replace.
***Corrective:*** Restate the purpose from Orient. Re-evaluate the detail: "If this fires, does the feature still accomplish its goal?" If no, the detail defeats the feature.

## Preservation Variants

These fire specifically when existing state creates gravitational pull —
migration, upgrades, technology selection. Migration cost trends toward
zero as tooling improves; carrying cost compounds. Evaluate both sides.

**Fabricated Costs** — Presenting migration costs that do not exist. **Recognition:** You claimed a migration cost without verifying it — the cost appeared in your reasoning before it appeared in evidence. **Corrective:** Before claiming any cost, verify it. Run the command. Read the docs.

**Compatibility Layering** — "Support both old and new." **Recognition:** Your design maintains two parallel systems or translation layers. **Corrective:** Two systems is almost always worse than one clean migration. Pick one. Migrate fully.

**Risk Asymmetry** — Treating change as risky and stasis as safe. **Recognition:** You evaluated the risks of changing but not the risks of staying. **Corrective:** Stasis accumulates hidden debt. Evaluate both risks explicitly.

**"It Works" as Sufficient** — Working is the minimum bar. **Recognition:** Your defense of the current approach is that it functions, with no comparison to alternatives. **Corrective:** "It works and there is no materially better approach today" is the actual defense.
