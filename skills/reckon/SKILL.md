---
name: reckon
description: >-
  First-principles cognitive discipline — position and reasoning as one act.
  Use when creating specs, architectures, processes, solutions, or
  methodologies. Use when analyzing costs, structures, strategies, or
  decisions. Use when reframing problems. Use before accepting any frame,
  cost, constraint, or convention without verification. Establishes what is
  actually needed and what is actually true (position), then reasons forward
  from verified constraints and navigational principles with every inference
  earning its chain (momentum). Dead reckoning: advance from an established
  fix using trusted constants.
metadata:
  version: "5.0.0"
  updated: "2026-06-11"
---

# Reckon

*What is actually true? What is actually needed? Reason from that — and trace every step.*

## The Move

Six steps. Always the same.

0. **Orient.** Before touching anything, establish the purpose of the inquiry and the principles you will reason from. For design: What must this enable? Who does it serve? What do they need to accomplish? For analysis: What is actually being examined? What question are we trying to answer? For cost or structure: What is the claimed structure, and what is the actual structure? These answers are the actual constraints. Everything else — existing code, existing patterns, existing implementations, current prices, current processes — is evidence about one attempt or one state, not the constraints themselves. Select the navigational principles that govern reasoning in this domain — the §Navigational Principles section directs you to the canonical corpus where they live. They are the trusted constants you will reason FROM.

1. **Decompose.** Strip the situation to its actual constituents. Orient determines the decomposition mode:
   - *Requirements decomposition* — for design work: What must be true? What is assumed? What was inherited from the prompt, the existing system, or the adjacent example?
   - *Constituent decomposition* — for cost and structure analysis: What is this made of? What does each component actually cost? Where is the gap between material reality and current price or complexity?
   - *Process decomposition* — for workflow and efficiency analysis: What are the actual steps? Which steps serve current needs and which are inherited ritual?

   The Assumed-Constraint Patterns below are the common forms inherited assumptions take across all modes.

2. **Verify.** For each constraint: is this real (physics, contract, measured need) or inherited (convention, precedent, comfort)? If you cannot point to evidence, it is assumed.

3. **Reconstruct.** Build from verified constraints and selected principles only. What emerges may resemble existing solutions or may not. Both are fine. What matters is that every element earns its place — and every inference earns its chain. At each reasoning step: What ground or principle does this follow from? If the answer is "the previous step" without tracing further, the chain has drifted. If the answer is "this is like that other thing," you are reasoning by analogy, not from ground. Trace back or stop.

4. **Compare.** Does the reckoned design match what exists? If yes, the existing approach is validated. If no, weigh real migration cost against carrying cost.

5. **Default to the reckoned design.** Inherited assumptions compound. When reckoned and existing designs diverge, the reckoned design wins unless migration cost is concrete and measured.

**Why Orient comes first.** 80% of solving a problem is defining the problem. Orient exists because without it, decomposition has no anchor — you will decompose whatever is in front of you, which is usually the existing system. Orient points decomposition at the right target: the need, not the implementation. Orient also selects the navigational principles — without them, reconstruction has no direction, and correct ground leads to unprincipled reasoning.

**The two faces of reckoning.** Reckoning has a static face and a dynamic face. The static face is position: strip assumptions, verify constraints, establish what is actually true. The dynamic face is momentum: reason forward from that position using navigational principles, with every inference tracing its chain back to ground or principle. Dead reckoning — the navigator's discipline — captures both: advance from an established fix using trusted constants. Position without momentum is inert ground that never reaches a conclusion. Momentum without position is fluent reasoning from an unverified starting point. The two faces are one act.

**The descriptive/normative distinction.** There are two kinds of truth relevant to reckoning. *Descriptive truth* is what currently exists — the code, the configuration, the running system, the current cost structure. *Normative truth* is what's actually needed — the requirements, the capabilities, the outcomes that matter. For design, ground in normative truth. For cost or structure analysis, ground in material truth — what things are actually made of, what they actually cost, what each component contributes. Material truth is normative in the sense that it is the verified reality against which the current price or structure should be evaluated, not a description of the current state. In both cases, descriptive truth is evidence, useful for gap analysis or baseline comparison, but never the starting point. Confusing these — treating what currently exists as the definition of what should exist — is the most common reckoning failure.

**Chain of inference.** The dynamic face's discipline is the chain. Every conclusion traces back through intermediate inferences to verified ground or navigational principle. The chain breaks in three ways: an inference follows from the previous inference without tracing to ground (chain drift), an inference follows from analogy rather than principle (pattern projection), or a principle is cited but does not actually govern the inference (principle as decoration). When the chain breaks, stop and re-derive from the last verified link.

**Chain completion.** A chain that is valid at every link can still be incomplete. The chain breaks when a link fails to trace to ground. The chain terminates prematurely when the conclusion is reached but not verified against its full consequence surface. Premature termination feels like completion — the chain was honest, every link traced back, the conclusion follows from ground and principle. But a conclusion that holds on one consequence path may fail on another. The completion test: before closing any chain — before endorsing, rejecting, or resolving — ask "What else does this conclusion affect?" and trace those paths. The chain is finished when the conclusion has been evaluated against every behavior it touches, not just the behavior that prompted the inquiry.

**Reckoning is the opposite of analogy.** Analogy copies solutions and their embedded assumptions. Reckoning derives solutions from constraints and discovers which assumptions were load-bearing. The static face catches inherited assumptions; the dynamic face catches analogical reasoning from correct ground. Both are necessary because agents ground correctly and then reason by analogy — the grounding was correct, the reasoning from the ground was unprincipled.

**Why this matters more for agents:** LLMs exaggerate human cognitive biases — anchoring, confirmation, primacy, status quo. Research shows effect sizes "unusually large," behaving as "caricatures of human cognitive behavior." First information in context disproportionately shapes all subsequent reasoning. Without Orient, the first information is typically the existing system, and everything flows from there. Orient ensures the first information is the need. Without navigational principles, reconstruction defaults to pattern-matching — the most available solution shape fills the space left by stripped assumptions.

---

## Navigational Principles

First principles you reason FROM during reconstruction. They are not goals to optimize — they are constants that govern how verified constraints compose into solutions. Select the ones relevant to the domain during Orient; they fire during Reconstruct.

The principles are defined in the canonical corpus at [pentaxis93/principles](https://github.com/pentaxis93/principles), not here — they are consulted, never duplicated, which is itself one of them ([Single Home](https://github.com/pentaxis93/principles/blob/main/principles/single-home.md)). Consult the [corpus index](https://github.com/pentaxis93/principles#readme) during Orient and select what governs reasoning in this domain. What stays in this skill is the cognition methodology — the move, the chain discipline, the recognition-and-corrective machinery — not the principle definitions.

Reckon's two faces resolve to three universals that govern most reasoning here:

- **Position** grounds in [Grounding](https://github.com/pentaxis93/principles/blob/main/principles/grounding.md): reason from what is needed, not from what exists — an adjacent problem's solution is evidence, not a template.
- **Momentum** answers to [Traceability](https://github.com/pentaxis93/principles/blob/main/principles/traceability.md): every inference earns its chain back to ground or principle.
- **Shape** answers to [Parsimony](https://github.com/pentaxis93/principles/blob/main/principles/parsimony.md): everything earns its place — among rival designs meeting the same constraints, fewer moving parts win until a constraint demands more.

The in-file register these three replace — each item raised to or attached within its canonical universal — is classified item by item in the corpus [SOURCES.md](https://github.com/pentaxis93/principles/blob/main/SOURCES.md), Register 5.

---

## Analogical Reasoning Signals

These catch the dynamic error — reasoning by analogy from correct ground — just as the Assumed-Constraint Patterns catch the static error of accepting inherited assumptions. When you notice any of these during Reconstruct, stop and re-derive from ground and principle.

### 1. Pattern Projection

"This is like that other thing."

***Recognition:*** Your reasoning maps the current problem onto a familiar pattern. The mapping feels natural — the structures seem similar, the concepts align. But you have not verified that the analogy holds at the constraint level. Similarities in shape do not imply similarities in structure.
***Corrective:*** "What are this problem's actual constraints, and does this pattern satisfy them — or does it satisfy a different problem's constraints that happen to look similar?"

### 2. Precedent Inference

"Other systems do X, so this should too."

***Recognition:*** Your design decision appeals to what other systems, projects, or implementations have done. The precedent feels authoritative — many systems cannot all be wrong. But many systems can all be copying each other. Consensus is not constraint.
***Corrective:*** "What constraint in this problem demands X? If the precedent did not exist, would I derive X from the constraints alone?"

### 3. Historical Extrapolation

"Historically it costs/takes Y."

***Recognition:*** Your estimate, budget, or timeline is derived from past instances rather than from the actual constituents of this instance. Historical data is evidence about past contexts, not constraints on the current one.
***Corrective:*** "What does this actually consist of, and what does each constituent actually cost?" Reckon from constituents, then compare with historical data.

### 4. Familiarity as Fitness

"This pattern worked there, so it fits here."

***Recognition:*** You are selecting an approach because it has worked in your experience, not because it was derived from this problem's constraints. The approach's familiarity masquerades as fitness. You feel confident because you have done this before, not because the constraints demand this solution.
***Corrective:*** "Would I choose this if I had never seen it before?" Derive the approach from constraints. If the same approach emerges, it is validated by derivation, not familiarity.

### 5. Chain Drift

Each step follows from the previous without tracing to ground.

***Recognition:*** Your reasoning is a sequence where each inference follows plausibly from the one before it, but no inference traces back to verified ground or navigational principle. The chain feels logical — each step is locally valid. But locally valid steps can drift arbitrarily far from ground. Three wrong inferences in sequence, each building on the previous.
***Corrective:*** "Does this inference trace to ground or principle, or only to the previous inference?" At each link, trace back. If the chain reaches ground or principle, it holds. If it reaches only the previous inference, re-derive from ground.

### 6. Incremental Analogy

The existing solution with adjustments.

***Recognition:*** Your design is the current implementation modified rather than derived. You started from what exists and made changes rather than starting from constraints and building. The result may be close to correct — incremental changes are often locally optimal. But local optima are not the same as reckoned solutions. You are making slight iterations on a theme when the theme itself may be the assumption.
***Corrective:*** "Did I derive this or adjust the existing solution?" Derive from constraints. If the derived solution resembles the adjusted one, the adjustment was valid. If not, the existing solution was pulling you off ground.

---

## Assumed-Constraint Patterns

These fire on all first-principles work — design, analysis, strategy, decomposition. When you notice any of these, stop and reckon.

### 1. Problem-as-Given

Accepting the problem statement without questioning scope, framing, or premises.

***Recognition:*** You are optimizing within the frame you were handed. You have not asked whether the frame is correct.
***Corrective:*** "What problem are we actually solving? Is this the right question, or the question we were given?"

### 2. Description as Design

Treating what the current system does as the definition of what it should do — documenting what is instead of designing what's needed.

***Recognition:*** Your "requirements" are descriptions of existing behavior. Every claim traces to existing code or configuration; none trace to user needs. You read the implementation and organized your findings instead of asking what it must enable.
***Corrective:*** "If this implementation did not exist, what would users need?" Start from the need. Use the existing implementation for gap analysis only after the design exists.

### 3. Borrowed Structure

Importing categories, patterns, or architecture from adjacent systems without verifying fit.

***Recognition:*** Your design's structure mirrors an adjacent system, a familiar pattern, or the categories in the request. You did not derive them from requirements — you inherited them. The analogy feels natural, perhaps too natural.
***Corrective:*** "What structure would emerge from the requirements alone?" Design fresh. Compare with the inherited structure afterward. Identify where the analogy breaks.

### 4. Precedent as Constraint

Treating past decisions, existing implementations, or prior investment as requirements.

***Recognition:*** "We did it this way before," "the existing system does X," or "we already invested in Y" appears in your reasoning as constraint rather than data point. The existing solution is your design starting point rather than a comparison target.
***Corrective:*** Precedent is evidence, not constraint. Past investment is irrelevant to future value. "If this precedent did not exist, what would we build?"

### 5. Complexity Preservation

Maintaining complexity because removing it seems risky.

***Recognition:*** You are preserving structure not because it serves current requirements, but because removing it might break something you do not understand — or adding structure for requirements that do not yet exist.
***Corrective:*** "What is the simplest design that meets requirements?" If simpler than what exists, the complexity needs justification or removal.

### 6. Audience Assumption

Designing for the requester, yourself, or an imagined user rather than verified actual users.

***Recognition:*** You have not identified who this serves. You are designing for the voice in the prompt.
***Corrective:*** "Who actually uses this? What do they actually need?" Ground the audience before grounding the design.

### 7. Abstraction Gravity

Defaulting to the abstraction level of adjacent or existing systems.

***Recognition:*** Your design operates at the same abstraction level as the system it replaces or resembles. You adopted this level implicitly — you cannot articulate why it is correct for this problem. The decision was inherited, not made.
***Corrective:*** "What abstraction level does this problem actually require?" The existing system's level is a data point, not a default.

### 8. Local Coherence

A detail follows a valid pattern and sounds right in isolation, but contradicts the purpose established in Orient.

***Recognition:*** Your output would be correct in a generic context — it follows established engineering conventions, uses appropriate technical language, and reads as a reasonable decision. But you have not checked it against the specific purpose of this work. The fluency of the output masks the contradiction. Common vectors: failure-mode defaults that negate the feature ("if the safety check fails, skip it"), error paths that undo the work, fallbacks to the behavior the feature exists to replace.
***Corrective:*** Restate the purpose from Orient. Re-evaluate the detail: "If this fires, does the feature still accomplish its goal?" If no, the detail defeats the feature.

### Preservation Variants

These fire specifically when existing state creates gravitational pull — migration, upgrades, technology selection. Migration cost trends toward zero as tooling improves; carrying cost compounds. Evaluate both sides.

**Fabricated Costs** — Presenting migration costs that do not exist. **Recognition:** You claimed a migration cost without verifying it — the cost appeared in your reasoning before it appeared in evidence. **Corrective:** Before claiming any cost, verify it. Run the command. Read the docs.

**Compatibility Layering** — "Support both old and new." **Recognition:** Your design maintains two parallel systems or translation layers. **Corrective:** Two systems is almost always worse than one clean migration. Pick one. Migrate fully.

**Risk Asymmetry** — Treating change as risky and stasis as safe. **Recognition:** You evaluated the risks of changing but not the risks of staying. **Corrective:** Stasis accumulates hidden debt. Evaluate both risks explicitly.

**"It Works" as Sufficient** — Working is the minimum bar. **Recognition:** Your defense of the current approach is that it functions, with no comparison to alternatives. **Corrective:** "It works and there is no materially better approach today" is the actual defense.

---

## Active Excavation

The patterns above are passive — they catch drift. These techniques actively drill to bedrock.

### Socratic Drilling

Five question types, applied in sequence or as the situation demands:

1. **Origin.** "Where did this come from? Who established it? When?" — Traces the genealogy of a constraint, cost, frame, or assumption. Many constraints are inherited from contexts that no longer apply.
2. **Assumption.** "What are we assuming when we accept this? What would have to be true for this to be correct?" — Surfaces hidden premises. The assumption beneath the assumption is usually where the inherited thinking lives.
3. **Evidence.** "What evidence supports this? Is the evidence current? Would we accept this evidence in a different context?" — Demands verification. Convention and repetition are not evidence.
4. **Alternatives.** "What would this look like if this constraint did not exist? What alternatives have we not considered because we accepted the frame?" — Opens the solution space that the inherited frame has closed.
5. **Consequences.** "If we accept this, what follows? If we reject this, what follows?" — Tests load-bearing status. If rejecting a constraint has no real consequences, it was not a real constraint.

### Recursive Why

Drill past surface explanations by asking "why" recursively until you hit bedrock — a physical law, a measured fact, a contractual obligation, or a verified user need.

***Recognition that you have hit bedrock:*** The answer is independently verifiable and does not depend on convention, precedent, or "how things are done." If the answer is "because that is how it has always been done" or "because the existing system does it that way," you have not reached bedrock — keep drilling.

***Recognition that you have overshot:*** You are questioning constraints that are independently verified (physics, contracts, measured data). Stop. That is ground.

### Chains and Techniques

Active excavation establishes ground. Navigational principles govern what you build from it. Apply techniques during Orient and Decompose to reach bedrock. Apply principles during Reconstruct to reason forward. At every step of reconstruction, the chain of inference must be explicit — each conclusion traces through the techniques that established its ground and the principles that governed its derivation.

---

## When to Reckon

**The trigger:** You are about to accept a frame, a cost, a constraint, a structure, or a "how things work" — or you are about to create something — or you are about to reason forward from established ground. Ask: "Have I established what is actually true and what is actually needed, and am I reasoning from ground and principle rather than from pattern and analogy?"

## When NOT to Reckon

- **Mid-execution.** Finish the current step, then reassess. Reckoning fires at decision points.
- **Verified external constraints.** Users at scale, contracts, and regulations are ground truth — they survive decomposition.
- **Diminishing returns.** If reckoning produces the same design as the inherited approach, the approach was correct. Reckoning is verification, not contrarianism.

---

## Corruption Modes

### Static-face corruptions

**Skipped Orient.** Jumping straight to decomposition without establishing what this must enable. The need shapes everything. If you decomposed without it, your decomposition targeted the wrong thing.

**Performative grounding.** Going through the motions without questioning. "I considered the requirements and they match what was given." If decomposition always confirms the inherited frame, you are rationalizing, not decomposing.

**Implementation survey as design.** Thorough research of the existing system presented as a design document. The research is valuable — for gap analysis. But organizing implementation facts is not designing. If your output would be equally true as a README for the current system, you have not designed anything.

**Structure survey as analysis.** Thorough research of an existing cost structure, process, or system presented as analysis. Gathering current prices, listing current steps, or documenting current architecture is data collection, not first-principles analysis. If your output describes what exists without questioning whether it should exist, you have not grounded anything.

**Infinite decomposition.** Using reckoning to delay decisions. Decomposition serves reconstruction. If you are decomposing without rebuilding, you have stalled.

**Rejection as reflex.** Dismissing all inherited structure because it is inherited. Some precedents are correct. Reckoning is verification, not contrarianism.

### Dynamic-face corruptions

**Grounded-then-analogical.** The static face fired correctly — assumptions stripped, constraints verified, ground established. Then reconstruction defaulted to pattern-matching: the most available solution shape filled the space left by stripped assumptions. The grounding was correct; the reasoning from the ground was unprincipled. This is the corruption that created reckon: correct position, analogical momentum.

**Plan as precedent.** A plan, a prior classification, or an earlier decision in the same session becomes inherited frame for subsequent decisions. The plan was an artifact from a prior context — it encoded assumptions that were reasonable at planning time. When new evidence arrives (a reviewer's finding, a test failure, a concrete defect), the plan's assumptions must be re-evaluated against the evidence, not cited as authority. Recognition: you are defending a decision by pointing to the plan, the approved scope, or a prior round's classification rather than reckoning the current finding from ground. "The plan excluded this" is not a constraint — it is a planning assumption that may not survive contact with new evidence. This corruption compounds over long sessions: early decisions accumulate authority through repetition, and each subsequent decision pattern-matches against the accumulated context rather than reckoning fresh. The corrective is the same as for any inherited frame: evaluate the current finding against the actual constraints, not against prior decisions about similar findings.

**Premature termination.** The chain reached a valid conclusion and stopped. Every link traced to ground or principle. But the conclusion had consequences the chain didn't evaluate. The reckoning felt complete because the chain was honest — no drift, no analogy, no decoration. But validity is not completeness. Recognition: you closed the chain after evaluating the consequence that prompted the inquiry without asking "what else does this conclusion touch?" The missed consequence is typically in a different dimension than the one you evaluated — a different command, a different consumer, a different failure mode, a different phase of execution. The corrective: before closing any chain, enumerate the consequence surface. If the conclusion affects behaviors beyond the one that prompted the inquiry, trace those paths before declaring the chain finished.

**Principle as decoration.** A navigational principle is cited but does not actually govern the inference. "By parsimony, we should..." followed by a design whose complexity is not justified by the principle invoked. The principle appears in the reasoning but did not constrain it. Recognition: remove the principle citation and the reasoning does not change.

**Untraceable chain.** The chain of inference from ground to conclusion exists but cannot be articulated. Each step "follows naturally" without explicit derivation. The conclusion may be correct, but its correctness cannot be verified because the chain is implicit. Recognition: you cannot state, for each inference, what ground or principle it follows from. If the chain cannot be shown, it cannot be trusted.

---

*The default is to float — in inherited frames, borrowed categories, accepted costs, unquestioned structures, precedent as constraint, descriptions of what is, and analogical reasoning from correct ground. Orient returns you to what is needed. Grounding returns you to what is true. Principles give you direction. The chain keeps you honest. Reckon from there.*
