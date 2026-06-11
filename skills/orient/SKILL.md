---
name: orient
description: >-
  Use when working in a groundwork-equipped project, at session start, task
  initiation, or any moment requiring methodology orientation or persistent
  documentation-writing guidance. Activates the full skill system as one
  connected methodology and carries the always-on documentation discipline.
metadata:
  version: "3.2.0"
  updated: "2026-06-11"
---

# Orient

## Overview

Groundwork is one connected methodology, not a skill collection. Every skill closes a specific failure mode in the topology from problem framing to shipped change. This skill is the map that shows how they connect.

*Documentation is communication to a specific reader, not a record that work happened.*

## Operating Stance

Skills are your default operating mode, not optional extras. When a skill's
trigger matches the current work, invoke it. The default is activation, not
restraint. The corruption mode to watch for is under-use — skipping skills
whose triggers match — not over-use. The triggers themselves provide the scope.

## Entry Point

Read the work-unit graph first. Whether starting a session, picking up work, or orienting mid-task, the work-unit graph tells you where you are: what's in progress, what's blocked, what's next. Work from the graph, not from memory.

Why the work-unit graph matters: agent sessions are bounded — context windows end, sessions close, agents rotate. The work-unit graph is the persistence layer that survives those boundaries. It holds what remains to be done, what blocks what, and what state each piece of work is in. Working from the graph instead of from memory is what makes multi-session progress reliable.

See [`work-unit-model.md`](https://github.com/tesserine/groundwork/blob/main/docs/architecture/work-unit-model.md) for the work-unit state model, dependency graph format, and graph maintenance rules.

## The Flow

Five stages, in dependency order. Each produces what the next consumes.

1. **Frame constraints.** `reckon` establishes what the work must enable — verified constraints and principled reasoning, not inherited assumptions.

2. **Define behavior.** `specify` defines the behavior contract in Given/When/Then scenarios. This contract threads through every subsequent stage.

3. **Decompose.** Converge to a decision-complete design (`plan`), break the design into agent-executable work-units (`decompose`), and initiate the work session (`take`).

4. **Execute and verify.** Implement through RED-GREEN-REFACTOR (`implement`), review documentation accuracy with `document`, verify behavior-level evidence before claiming done (`verify`), and package verified changes into a PR (`submit`). When a plan contains independent tasks, dispatch fresh subagents for each to keep execution context clean — stale context from earlier tasks pollutes later ones. Match subagent model to task complexity: use cheaper/faster models for straightforward work, reserve the most capable model for subtle or cross-cutting changes.

5. **Land.** `land` closes the loop: merge, cleanup, behavior coverage record, documentation coverage status, and work-unit closure.

The stages are in order but not all required for every piece of work. Enter the topology where the work needs you. A bug fix with an existing work-unit enters at Execute. A new capability enters at Frame. The constraint is sequence — you can't land before executing — not completeness.

## Integration Principles

These thread across the topology. They aren't phases — they're disciplines that engage when relevant and stay active from that point forward.

**Sovereignty.** Every handoff passes outcomes (WHAT must be true), never implementation steps (HOW to achieve it). Work-units define acceptance criteria, not procedure. Plans define interfaces and decisions, not copy-paste instructions. Example: GitHub issue #5 prescribed "Replace ATTRIBUTION.md with a standard NOTICE file." An implementing agent planned exactly that — but NOTICE is an Apache convention (wrong for MIT), and the file should have been deleted. This skill teaches the map; agent judgment navigates it.

**Behavior traceability.** The behavior contract from stage 2 should be traceable at every subsequent stage. Plans link design decisions to behavior statements. Work-units map acceptance criteria to behaviors. Tests correspond to named scenarios. Verification cites behavior-level evidence. Landing records what coverage shipped.

**Documentation obligation.** User-facing changes carry documentation obligations: acceptance criteria include doc updates, completion claims include doc accuracy evidence, and landing records documentation coverage status. User-visible changes require a CHANGELOG entry.

**Records carry the delegation.** A work-unit's tracker record is the spec an implementing agent reads — the body is the standalone specification, comments are a log. When authoring or re-scoping a record, `work-unit-craft` provides the discipline: outcomes over prescription, and the corruption modes that make records mis-steer their readers.

**Reckon re-fires.** `reckon` is not step-one-once. New generative work mid-session requires reckoning anew. The trigger is creation, not sequence position.

**Research fires at any stage.** `research` provides reliable external evidence when decisions depend on facts outside the codebase — framing, design, decomposition, and implementation can all require it.

**Root cause before fixes.** When a test fails or behavior is unexpected, do not guess. Investigate root cause before proposing any fix. `debug` provides the investigation methodology — a cross-cutting discipline that fires at any stage, not only during execution. Once root cause is established, `implement` fix-bug owns the execution cycle. After 3 failed fix attempts, stop fixing and invoke `reckon` via the Skill tool to question the architecture.

**Introduce third force on friction.** Friction is a two-force collision: task momentum vs obstacle. Routing around is the collapsed triad — both forces lose. When operational friction appears — a missing tool, broken config, stale convention, undocumented requirement — stop and introduce the reconciling move: resolve it structurally before continuing. `resolve` provides the assessment methodology and scope guidance. Friction that exceeds side-quest scope becomes a follow-up work-unit via `decompose`. Unresolved friction compounds.

For the connecting structure — artifacts, manifest edges, schemas, and protocol topology — see [`connecting-structure.md`](https://github.com/tesserine/groundwork/blob/main/docs/architecture/connecting-structure.md).

## Corruption Modes

**Methodology as gates.** Recognition: you're checking off skills in order regardless of whether the work needs them, refusing to use a later-stage skill because you haven't completed an earlier stage that doesn't apply, or invoking a skill because its name matches a keyword in the conversation rather than because the topology calls for it. The Flow is a connected path with entry points, not a checklist where every box must be ticked.

**Behavior traceability loss.** Recognition: your tests pass but you can't name which behavior scenario each test verifies, or your completion claim says "all tests pass" without mapping results to named behaviors. Treating `specify` as a one-time preface rather than a contract that threads through execution.

**Work-unit discipline failure.** Recognition: you're deciding what to work on from the conversation or your own reasoning instead of reading the work-unit graph, or you've started implementation without checking whether the work-unit is blocked. The work-unit graph is the project's working memory — working from anything else means you're navigating from a snapshot that may already be stale.

**Sovereignty violation.** Recognition: your work-unit's acceptance criteria describe steps to perform rather than outcomes to verify, or your plan reads like a script to follow rather than decisions that constrain a solution space. When this fires, agents execute instructions instead of solving problems — and prescribed steps that encode wrong assumptions propagate unchallenged.

**Documentation drift.** Recognition: you're claiming completion but haven't checked whether the change affects any documentation, or you're aware of drifted docs but treating the update as separate future work. Drifted docs compound — each one trains readers to distrust all docs.

## Documentation Discipline

Carry this discipline at all times. `document` is the review protocol that runs
after code changes; this section is the always-on writing stance that decides
what documentation exists, who it serves, and how much detail it needs.

## Artifact Types

| Artifact | Audience | When Produced |
|----------|----------|---------------|
| README.md | New users, contributors, agents on first encounter | Project init; major capability changes |
| ARCHITECTURE.md | Contributors, agents understanding system structure | After grounding; significant structural changes |
| ADR | Future decision-makers (human and AI) | When a significant decision is made (MADR 4.0 format) |
| CHANGELOG.md | Users, operators, downstream consumers | Before landing user-visible changes (Keep a Changelog format) |
| work-unit-model.md | Contributors, agents working from the work-unit graph | When work-unit states, graph format, or maintenance rules change |
| API reference | API consumers, agents calling functions | During implementation, alongside code |
| Inline comments | Future maintainers, agents modifying code | At non-obvious decision points during implementation |

## Documentation Constraints

- `audience-first`: identify the reader before writing. No document exists
  without a stated audience.
- `minimum-viable-detail`: include enough to prevent mistakes, no more. Three
  clear sentences beat two verbose paragraphs.
- `source-of-truth-over-counts`: avoid hardcoded aggregate counts for dynamic
  sets. Prefer referencing the authoritative object or generating the value.
- `task-oriented`: organize docs around what the reader needs to accomplish,
  not around the file tree.

## Documentation Requirements

- `adr-for-decisions`: significant architectural decisions get an ADR.
  "Significant" means it affects contributor work, is hard to reverse, or is
  not obvious.

## Documentation Procedures

### audience-identify

Before writing any documentation:

1. Name the audience: end user, contributor, API consumer, or AI agent.
2. State what they already know.
3. State what they need to accomplish after reading.
4. Apply the audience test throughout: "Would this reader know what to do
   after reading this?"

Audience profiles:
- **End user**: needs to install, configure, and use the system. Assumes no
  internals knowledge.
- **Contributor**: needs architecture understanding and dev setup. Assumes
  programming competence but no project-specific knowledge.
- **API consumer**: needs behavior contracts and integration guidance. Assumes
  domain competence.
- **AI agent**: needs explicit file paths, concrete examples, and
  constraint-first organization. Assumes no persistent memory across sessions.

### write-artifact

1. Run `audience-identify`.
2. Use `reckon` if the artifact requires design decisions such as
   ARCHITECTURE docs or ADRs.
3. Write for the identified audience at the appropriate depth.
4. Apply `minimum-viable-detail`; cut any section the reader does not need at
   the point of use.
5. Verify the audience test passes before committing.

## Documentation Corruption Modes

- `structure-not-understanding`: document headings mirror the directory tree
  instead of the reader's task.
- `verbose-not-useful`: the document is long but a reader still cannot act.
- `audience-blindness`: no stated audience, or the document would not change if
  the audience changed.

## Documentation Cross-References

- `reckon`: identify what the document must enable before writing architecture
  docs or ADRs.
- `specify`: behavior contracts define what public behaviors documentation must
  explain.
- `decompose`: user-facing changes include documentation expectations in work-unit
  acceptance criteria.
- `implement`: inline comments and type-level documentation are written alongside
  implementation.
- `document`: review documentation accuracy after code changes and before
  `verify`.
- `land`: record documentation coverage status alongside behavior coverage.
