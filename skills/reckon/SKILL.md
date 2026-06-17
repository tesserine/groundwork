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
  version: "5.2.1"
  updated: "2026-06-17"
---

# Reckon

*What is actually true? What is actually needed? Reason from that — and trace every step.*

## The Move

Six steps. Always the same.

0. **Orient.** Before touching anything, establish the purpose of the
   inquiry and the principles you will reason from. For design: What must
   this enable? Who does it serve? For analysis: What is actually being
   examined? What question are we answering? These answers are the actual
   constraints — everything else (existing code, patterns, prices,
   processes) is evidence about one attempt or one state, not the
   constraints themselves. Select the navigational principles that govern
   reasoning in this domain (§Navigational Principles); they are the
   trusted constants you reason FROM.

1. **Decompose.** Strip the situation to its actual constituents. Orient
   determines the mode: *requirements* decomposition for design (what must
   be true? what was inherited?), *constituent* decomposition for cost and
   structure (what is this made of? what does each part actually cost?),
   *process* decomposition for workflow (which steps serve current needs
   and which are inherited ritual?).

2. **Verify.** For each constraint: is this real (physics, contract,
   measured need) or inherited (convention, precedent, comfort)? If you
   cannot point to evidence, it is assumed.

3. **Reconstruct.** Build from verified constraints and selected principles
   only. Every element earns its place — and every inference earns its
   chain: at each step, name the ground or principle it follows from. If
   the answer is "the previous step" without tracing further, or "this is
   like that other thing," stop and re-derive.

4. **Compare.** Does the reckoned design match what exists? If yes, the
   existing approach is validated. If no, weigh real migration cost against
   carrying cost.

5. **Default to the reckoned design.** Inherited assumptions compound.
   When reckoned and existing designs diverge, the reckoned design wins
   unless migration cost is concrete and measured.

## The Discipline Beneath the Move

**Why Orient comes first.** 80% of solving a problem is defining it.
Without Orient, decomposition targets whatever is in front of you — usually
the existing system. Orient points it at the need. LLMs exaggerate human
anchoring and status-quo bias; the first information in context
disproportionately shapes everything after, so Orient makes the first
information the need, and the selected principles keep reconstruction from
defaulting to pattern-matching.

**The two faces.** Position (static): strip assumptions, verify
constraints, establish what is true — for design, ground in *normative*
truth (what's needed), never in descriptive truth (what exists). Momentum
(dynamic): reason forward with every inference tracing back to ground or
principle. Position without momentum never reaches a conclusion; momentum
without position is fluent reasoning from an unverified start. Dead
reckoning — advance from an established fix using trusted constants — is
both faces as one act.

**The chain.** A conclusion is trustworthy only when its path back to
ground or principle is explicit. The chain breaks by drift (links trace
only to the previous link), by analogy (a link rests on resemblance), or by
decoration (a principle is cited but does not govern). And a valid chain
can still terminate prematurely: before closing, ask "what else does this
conclusion affect?" and trace those paths — the chain is finished when the
conclusion has been evaluated against every behavior it touches.

**Reckoning is the opposite of analogy.** Analogy copies solutions and
their embedded assumptions. Reckoning derives solutions from constraints
and discovers which assumptions were load-bearing.

## Navigational Principles

First principles you reason FROM during reconstruction. They are not goals
to optimize — they are constants that govern how verified constraints
compose into solutions. Select the relevant ones during Orient; they fire
during Reconstruct.

The principles are defined in the resolved principles corpus, not here —
they are consulted, never duplicated. Which corpus that is resolves
through methodology configuration, and it is materialized locally at
setup. Resolve its location in order: when `~/.groundwork/principles/`
exists, that is the corpus — read it; the embedded default at
`principles/` applies only in a bare groundwork checkout with no
installed corpus. A groundwork *source* checkout's `principles/`
directory is that embedded default, not the resolved corpus: an agent
working in or beside a groundwork source tree still reads the installed
corpus at `~/.groundwork/principles/`, never a source tree's
`principles/`. (Selection and lifecycle:
`docs/principles-corpus.md` in the groundwork repository.)

During Orient, having resolved the location above, read the index at
the resolved corpus root (its `README.md`, or `PRINCIPLES.md` for the
embedded default) and select what governs reasoning in this domain. The
corpus speaks for itself: no principle is privileged in advance of
Orient, and selection is per-domain, per-inquiry. What stays in this
skill is the cognition methodology — the move, the chain discipline, the
recognition-and-corrective machinery — not the principle definitions.

## Recognition Index

When any of these fires, stop and re-derive. Full expositions with
recognition and corrective for each:
[references/analogical-signals.md](references/analogical-signals.md) (the
dynamic error — analogy from correct ground) and
[references/assumed-constraints.md](references/assumed-constraints.md) (the
static error — inherited assumptions accepted as constraints).

| Signal | One-line trigger |
|---|---|
| Pattern projection | "This is like that other thing." |
| Precedent inference | "Other systems do X, so this should too." |
| Historical extrapolation | "Historically it costs/takes Y." |
| Familiarity as fitness | "This worked there, so it fits here." |
| Chain drift | Each step follows only from the previous step. |
| Incremental analogy | The existing solution, adjusted, presented as derived. |
| Problem-as-given | Optimizing inside the handed frame, unquestioned. |
| Description as design | What the system does, restated as what it should do. |
| Borrowed structure | Categories imported from an adjacent system. |
| Precedent as constraint | Past decisions or sunk investment treated as requirements. |
| Complexity preservation | Structure kept because removing it seems risky. |
| Audience assumption | Designing for the voice in the prompt. |
| Abstraction gravity | The adjacent system's abstraction level, inherited. |
| Local coherence | A locally-valid detail that defeats the Orient purpose. |
| Preservation variants | Fabricated migration costs · compatibility layering · risk asymmetry · "it works" as sufficient. |

To actively drill to bedrock rather than wait for a signal — Socratic
drilling and recursive why: [references/excavation.md](references/excavation.md).

## When to Reckon

You are about to accept a frame, a cost, a constraint, a structure, or a
"how things work" — or to create something — or to reason forward from
established ground. Ask: "Have I established what is actually true and
needed, and am I reasoning from ground and principle rather than pattern
and analogy?"

## When NOT to Reckon

- **Mid-execution.** Finish the current step, then reassess. Reckoning
  fires at decision points.
- **Verified external constraints.** Users at scale, contracts, and
  regulations are ground truth — they survive decomposition.
- **Diminishing returns.** If reckoning produces the same design as the
  inherited approach, the approach was correct. Reckoning is verification,
  not contrarianism.

## Corruption Modes

Static face: **skipped Orient** (decomposition with no anchor targets the
existing system); **performative grounding** (decomposition that always
confirms the inherited frame is rationalizing); **survey as design**
(organizing implementation facts is not designing — if the output would be
true as a README of the current system, nothing was designed); **infinite
decomposition** (decomposing without rebuilding is stalling); **rejection
as reflex** (some precedents are correct; reckoning is verification, not
contrarianism).

Dynamic face: **grounded-then-analogical** (correct position, then
pattern-matching fills the space the stripped assumptions left — the
corruption that created this skill); **plan as precedent** (an earlier
decision in the same session becomes an inherited frame; new evidence is
answered with "the plan excluded this" instead of fresh reckoning);
**premature termination** (a valid chain closed before its consequence
surface was traced); **principle as decoration** (remove the citation and
the reasoning doesn't change); **untraceable chain** (the conclusion may be
right, but a chain that cannot be shown cannot be trusted).

---

*The default is to float — in inherited frames, borrowed categories,
accepted costs, unquestioned structures, precedent as constraint,
descriptions of what is, and analogical reasoning from correct ground.
Orient returns you to what is needed. Verify returns you to what is
true. The selected principles give you direction. The chain keeps you
honest. Reckon from there.*
