# ADR-0002: Methodology Sovereignty

**Status:** Provisional — revised 2026-05-28 (regrounded on a second forge; see Revision below) \
**Date:** 2026-05-02 (revised 2026-05-28) \
**Traces to:** `tesserine/commons` PRINCIPLES.md P1 (Sovereignty); `tesserine/commons` ADR-0001 (Sovereignty).

## Revision (2026-05-28): regrounded on two forges

The original decision was reckoned against a single forge (GitHub). Its
WHAT/HOW separation is sound, but the *placement* of the line leaked
forge-specifics into the WHAT layer, and a one-forge derivation cannot prove
forge-neutrality. This revision re-derives the line against two
topologically-different forges — GitHub (branch + PR + platform merge) and
SourceHut (pushed proposal ref + SSH ref update, no platform merge, status as
metadata) — and resequences the rollout so the forge-touching arc proves the
architecture rather than trailing it.

**What stands unchanged:** the Methodology Sovereignty principle (each *unit* is
single-shape; units reference, never embed); the six content categories and
per-category formats (C-1…C-6); the directed-graph C-2 contract; two-tier
verification; fresh-authoring migration; and the epic + per-phase-deferral
vehicle.

**Correction 1 — articulation.** Unit-purity is the *constraint*; the *structure*
it yields is a two-layer protocol: a WHAT contract (C-2) that composes shared
HOW mechanics (C-3) **by reference**. The protocol-as-experienced carries both
layers; no single document mixes them; one HOW unit serves every protocol that
references it.

**Correction 2 — the line, re-placed.** A unit is WHAT only if it is invariant
across two topologically-different forges. The arc's invariant operations are
therefore *deliver-change-proposal*, *review*, *revise*, *apply-approved-change*,
*reflect-disposition*, and *close-out* — **not** `create-pr` or `pr-merge`. "PR"
and "merge" are HOW and never appear in a workflow contract. This supersedes the
`create-pr` example in *Per-category formats* below.

**Correction 3 — the artifact layer.** The `patch` artifact becomes
**`change-proposal`**: a forge-neutral envelope (`work_unit`, `branch`, `commit`,
`base`, `summary`) plus a **required `version`** (each review round is an
immutable version on both forges; GitHub's mutable PR is the degenerate case)
and a **forge-tagged `handle` variant** (`oneOf` keyed by `forge_tag`: GitHub →
PR URL, a pointer outward to a server object; SourceHut → an immutable proposal
ref under `refs/proposals/`). A new
**`review-findings`** artifact carries the review disposition, and `land`
triggers on that disposition, not on the raw proposal (folds #243). The
`patch.pr_reference`-required schema is retired.

**2026-05-31 supersession:** ADR-0003 replaces the single
`review-findings`-with-disposition artifact with typed review outcome artifacts:
`change-approved` and `change-needs-revision`. The Correction 3 direction still
holds - land gates on the review disposition rather than the raw proposal - but
the disposition is now the produced artifact type.

**Correction 4 — forge HOW stays orthogonal to mode cadence.** HOW varies by
*forge* (PR vs patch mechanics, apply mechanic, status target). Mode does not
create a second artifact path: autonomous and interactive sessions both reach
runa's validated session surface and artifact store. Interactive mode differs
by cadence only — the operator issues `runa go --work-unit <id>` one tick at a
time while the configured agent speaks the cascade tools inside that tick.
Forge mechanics therefore compose with the runa session surface; no mechanic is
authored per (forge × mode) cell.
Status-reflection is a forge-tagged mechanic invoked at stage edges (GitHub →
PR/issue state; SourceHut → tracker-ticket state), mandatory in practice but
producing no artifact, so it stays HOW. lists.sr.ht / patchset submission for
external contributor teams is a named, deliberate deferral.

**Resequenced rollout** (supersedes *Migration shape* below):

0. **Reground** — this revision. Establishes the corrected line and the
   `change-proposal` / `review-findings` artifacts. Cheap; comes first.
1. **Minimal substrate for the arc** — the C-2 contract schema+parser, the C-3
   mechanic schema+parser (with `forge_tag`), the C-4 `change-proposal` and
   `review-findings` schemas, and a conformance runner narrowed to those
   categories. Closes with R1: the C-2 format exercised once on a simple,
   already-forge-neutral protocol (`verify` or `take`) before the arc.
2. **Reference arc** — author `submit → review → land` on both forges (contracts
   + forge-tagged mechanics + mode-adapter composition) and dogfood it. This is
   the two-forge proof.
3. **Generalize** — remaining mechanics; the other seven protocols; discipline
   and ADR conformance; the body-pattern linter; CI gate; verification migration
   (folds #255); cleanup and authoring guides; the README articulation upgrade.

Per-phase decomposition deferral and the per-phase
`decomposition-assumption-update` gate carry over: only Step 1 is decomposed now.

## Context

Methodology documents in this codebase carry two structurally distinct kinds
of content:

- **WHAT** — intent, outcome, contract, invariant. The reasoning a unit
  declares for the agent to internalize or for the runtime to validate.
- **HOW** — procedure, tool invocation, recipe. The mechanics by which an
  agent produces or transforms artifacts.

The substrate exhibits the difference observably. Skill documents
(`skills/*/SKILL.md`) are uniformly cognitive content addressed to agent
reasoning — instructions to thinking, not to tooling. Protocol documents
(`protocols/*/PROTOCOL.md`) currently mix the two: workflow narration sits
at the same indent level as forge-specific JSON field paths, git refspec
patterns, MCP-tool invocations expressed as code, and shell heredoc syntax.
The mixing is structural, not incidental, and it accumulates: every fix to a
mixed-shape protocol lands as more prose at the same indent, because the
format admits no other surface.

The mixing has two downstream consequences. First, embedded HOW is
yesterday's HOW frozen into a WHAT-shaped document; it cannot be re-grounded
on each fresh execution because the document specifies the HOW directly
rather than what-the-HOW-must-achieve. Second, behavior verification at the
methodology layer is unavailable — when a unit's behavior is entangled in
mixed-shape prose, no parser-level check applies, and substring-presence on
prose strings becomes the entire verification surface for protocol behavior.

The principle this decision rests on is `tesserine/commons` PRINCIPLES.md P1
(Sovereignty), which declares: *the operator declares WHAT — direction,
vision, intent; the agent owns HOW — execution, implementation, craft. It
applies at every interface, at every scale.* A methodology document is a
human-authored artifact addressed to an agent; the document plays the
operator role, the invoking agent plays the agent role, and a unit that
mixes WHAT and HOW crosses the sovereignty boundary inside its own
boundary. ADR-0001 (Sovereignty) enumerates illustrative interfaces; the
methodology-document interface is covered by P1's general fractal claim and
does not require enumeration extension.

## Decision

### Principle

**Methodology Sovereignty.** Each methodology unit specifies content of a
single shape — WHAT or HOW — not both. The document boundary is the unit
boundary; per-document shape purity is the constraint. Units may reference
each other; they may not embed content of the other shape.

This is P1 fractal at the methodology-document interface. HOW is not absent
or unimportant; HOW is sovereign-to-the-agent and lives in HOW-shaped units
distinct from WHAT-shaped units. The methodology contains both shapes; no
single unit mixes them.

### Content categories

Methodology content decomposes into six categories. Two top-level shapes
(WHAT and HOW); within each, sub-shapes are determined by representation
need, not domain.

| # | Category | Shape | Purpose |
|---|---|---|---|
| 1 | Disciplines | WHAT | Cognitive content the agent applies during execution: how to think, when to halt, what to investigate. |
| 2 | Workflow contracts | WHAT | Per-protocol specification of interface (when fires, what consumes/produces) and workflow (the cognitive shape of execution). |
| 3 | Mechanics | HOW | Agent-callable recipes for tool invocation: forge operations, MCP tool calls, git refspec patterns, shell heredoc patterns. |
| 4 | Artifact schemas | WHAT | Per-artifact-type specification of structure: required fields, value constraints, cross-references. |
| 5 | Verification specifications | HOW with referenced WHAT | Mechanisms that establish methodology conformance and (where specified) behavior. |
| 6 | ADRs and foundational principles | WHAT | Operationalized architectural decisions and the bedrock principles they trace to. |

Topology is not a category; it is workflow contracts' interface-typed
sub-shape, currently centralized in `manifest.toml`. The graph emerges from
per-protocol typed interfaces; it is a derived view, not authored substrate.

### Per-category formats

Per category, format and tier:

| Category | Format | Tier |
|---|---|---|
| C-1 Disciplines | Markdown body + JSON Schema-validated YAML frontmatter + body-pattern linter | Structural-impossibility (frontmatter); after-the-fact detection (body) |
| C-2 Workflow contracts | TOML + JSON Schema; internal shape is a directed graph with conditional edges and explicit terminals | Structural-impossibility |
| C-3 Mechanics | TOML + JSON Schema with required `forge_tag` for forge-specific recipes | Structural-impossibility |
| C-4 Artifact schemas | JSON Schema 2020-12 | Structural-impossibility |
| C-5 Verification (conformance) | Code (parsers + linters) dispatched per category | Structural-impossibility for shape; after-the-fact for body |
| C-5 Verification (behavior) | Not specified at the methodology layer | Deferred to integration in user projects |
| C-6 ADRs and principles | Markdown body + JSON Schema-validated frontmatter | Structural-impossibility (frontmatter); inspection (body) |

The directed-graph shape for C-2 is load-bearing: workflow contracts
contain branching, convergence, loops, and terminal-state distinctions that
a flat ordered array cannot encode as first-class structure. Encoding flow
as graph prevents the same accumulation pathway (mixing) from reopening at
the sub-structural layer. Conditions on outgoing edges from a single node
are mutually exclusive (parser-enforced); loops require a typed exit
condition; every terminal is reachable from a designated start node.

The `forge_tag` on C-3 mechanics structurally encodes forge-neutrality: a
workflow contract references a forge-invariant operation (e.g.,
`deliver-change-proposal` — **not** `create-pr`; see Revision 2026-05-28);
methodology configuration selects which forge-tagged mechanic resolves the
reference. Forge substitution lives at config time, not at workflow-contract
time.

### Two-tier verification deployment

The conformance runner — a build step that walks the methodology tree and
dispatches each unit to its category-specific verifier — operates at two
points:

- **Authoring time.** A contributor running the runner on their working
  tree gets per-unit pass/fail with specific errors. Sovereignty interface:
  contributor ↔ methodology source.
- **PR time.** CI runs the runner on the PR's tree; failures block merge.
  Sovereignty interface: project ↔ shared methodology.

Activation-time verification (runtime loading the methodology and re-running
conformance before firing protocols) is explicitly **not specified**. The
two-tier deployment covers the methodology's own sovereignty boundary;
activation-time verification would impose runtime-side coupling and is
left for a later decision if drift between PR-merge and activation surfaces
as a defect.

### Migration shape

> **Superseded by the Revision (2026-05-28) resequenced rollout above.** The
> phased rollout below is retained for record; the active sequence is the
> four-step plan in the Revision.

Existing `protocols/*/PROTOCOL.md` files do not parse as C-2 workflow
contracts and are not editable into them. Migration is **fresh authoring
per protocol**, not in-place conversion.

The rollout is phased:

1. **Substrate.** Schemas, parsers, and the conformance runner; CI
   integration.
2. **Discipline conformance.** Frontmatter schema validation and
   body-pattern linting applied to existing skills (a lift-and-fit; skills
   are observably WHAT-pure under the looser format today).
3. **Artifact schema review.** Cross-reference and registry consistency
   passes over existing schemas.
4. **Mechanic library.** Reusable HOW recipes extracted from current
   protocol bodies, authored as C-3 units with `forge_tag` where
   applicable.
5. **Per-protocol workflow contracts.** One PR per protocol, ordered
   smallest-first so the format is exercised on simpler protocols before
   the most-mixed one. Each PR authors the new C-2 contract referencing
   existing skills, extracted mechanics, and artifact schemas; the old
   `PROTOCOL.md` is removed in the same PR.
6. **Verification migration.** Per-protocol substring-assertion tests are
   replaced by conformance-runner coverage; behavior testing, where it
   exists, moves to integration testing in user projects.
7. **Cleanup.** Transitional scaffolding removed; per-category authoring
   guides published; the README's principle articulation is extended from
   inter-protocol to intra-unit form.

The conformance runner operates per-unit, so mixed-state during phase 5
(some protocols converted, others not) is structurally tolerated:
unconverted protocols are not treated as C-2 contracts, and the methodology
continues to function via `manifest.toml`'s typed interfaces, which are
unchanged across the migration.

### Vehicle

A top-level architectural epic in `tesserine/groundwork`, with one sub-epic
per migration phase. Each sub-epic is independently reviewable; sub-epic
acceptance gates the next.

Per-phase decomposition is deferred until the prior phase clears
acceptance. A phase's acceptance includes a statement of what (if anything)
the phase's deliverable changed about the next phase's scope, or an
explicit confirmation that no change is required. This prevents later
phases from being decomposed against assumptions that earlier phases'
deliverables should have updated.

## Consequences

### Good

- The accumulation pathway that produces mixed-shape protocol bloat
  becomes structurally impossible under the C-2 directed-graph format. No
  fix can land as another bullet in a step's narrative because the step
  has no narrative.
- Methodology Sovereignty operates as P1 fractal at a previously
  unenumerated interface; the principle is realizable in current substrate
  (skills already implement it) and structurally enforced in the new
  substrate.
- Forge-neutrality is a unit-layer property (C-3 `forge_tag`), not a
  repository-layer property. Future relocation to per-forge repositories
  remains admissible at higher scale; not motivated now.
- Per-phase decomposition deferral prevents later phases from inheriting
  design-memo assumptions that should have been updated in light of prior
  phases' deliverables.
- The conformance runner unifies what were previously per-protocol bespoke
  test files into one dispatched mechanism; per-category authoring guides
  give parser errors actionable context.

### Neutral

- Existing `PROTOCOL.md` files cannot be in-place converted; they are
  replaced by typed workflow contracts.
- Behavior verification at the methodology layer is deferred to
  integration in user projects. The methodology specifies conformance
  verification only.
- Authoring-time verification is a contributor-side build step, not a
  pre-commit hook. Contributors choose when to invoke it; CI is the
  binding enforcement surface.

### Bad

- Authoring complexity at the workflow contract layer is higher than
  free-prose authoring. Contributors author a directed graph with typed
  conditions instead of writing prose narrative. Per-category authoring
  guides carry the authoring-obviousness load; without them, parser
  errors are not actionable for new contributors.
- Activation-time conformance verification is a real verification surface
  this decision does not cover. If methodology drift between PR-merge
  and runtime activation surfaces as a defect, a future ADR may revisit;
  until then, the gap is named and accepted.
