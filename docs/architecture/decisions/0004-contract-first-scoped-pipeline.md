# ADR-0004: Contract-First Scoped Pipeline

**Status:** Superseded by [ADR-0007](0007-dimension-agnostic-contract-machine.md) \
**Date:** 2026-06-11 \
**Traces to:** [pentaxis93/principles](https://github.com/pentaxis93/principles)
(Sequence, Grounding, Parsimony, Single Home, Sovereignty, Traceability,
Verifiable Completion, Honest Signal, Dosed Compliance); ADR-0002 (Methodology
Sovereignty); ADR-0003 (Disposition as Artifact Type); runa
[interface contract](https://github.com/tesserine/runa/blob/main/docs/interface-contract.md)
and [session surface contract](https://github.com/tesserine/runa/blob/main/docs/session-surface-contract.md).

> ADR-0007 keeps the contract-first scoped pipeline but supersedes this
> decision's behavior-contract-as-spine artifact framing with a
> dimension-agnostic `contract` artifact and uniform `completion-evidence`
> results.

## Context

The scoped pipeline — the protocols that carry one already-selected work-unit
from entry to a landed change — had grown to nine protocols and ten artifact
types across rounds of incremental agentic upgrade work. Grounding against
the live substrate surfaced real defects:

- The entry (`take`) was built around *selecting* work, but in
  work-unit-first entry the work-unit **is** the entry — runa activates
  scoped protocols on a delegated work-unit. What remained was workspace
  preparation plus a thin `claim` artifact whose only function was giving
  take a capstone.
- The behavior contract — the methodology's own declared spine — was created
  at `specify`, one station *after* work began. BDD did not begin where work
  begins.
- The methodology contradicted itself about its own shape: `take` described
  a five-step lifecycle while the manifest ran nine protocols.
- Nine stations and ten artifacts did not scale down to small changes, and
  the back half (`verify → document → submit → review → land`) was a tail
  agents forgot when operating outside the cascade.
- The reviewer was handed only the `change-proposal` — judging "preserves
  intended behavior" without the behavior contract in context.

Each *discipline* in the pipeline removes a real failure an unsupervised
agent commits (see "Friction map" below). The defects were in the
*topology* and in the accreted instruction prose, not in the disciplines.

## Decision

### The topology: seven stations, one spine

```
take → plan → implement → verify → submit → review ⇄ (revision via submit) → land
```

**The entry is contract-first.** `take` receives the work-unit, prepares the
workspace, frames the work, and authors the `behavior-contract` — the
executable definition of done. The contract is the pipeline's spine:

- **required** by every station that exercises judgment about the change —
  `plan`, `implement`, `verify`, `submit`, `review`;
- **accepted** by `land`, the mechanical applier, for the completion record.

This is the clean ownership line: judgment stations cannot do their job
without the contract; the applier can, but records its closure.

**`specify` dissolves into the entry.** Authoring the contract *is* what
entry truly is once selection is gone. The Given/When/Then authoring
discipline moves to the `contract` skill — now the single BDD home for both
authoring (at `take`) and carrying (everywhere after). The `claim` artifact
is deleted: work-unit identity is runtime-enforced (runa injects `work_unit`
into every scoped artifact and validates canonical ids), so a separate
threading artifact was structure without function — it existed because
"take should produce *something*," which is grounding inverted.

**`document` dissolves into `verify`.** Documentation accuracy is completion
evidence — the old document protocol said so itself. One gate asks one
question — "is this work complete?" — and complete means: scenarios pass,
criteria covered, documentation truthful. The drift-review method lives in
`protocols/verify/references/documentation-review.md`; the outcome lives in
`completion-evidence.documentation`. The `documentation-record` artifact is
deleted. The always-on documentation-*writing* stance remains with `orient`;
inline docs remain implement's GREEN/REFACTOR work.

**`plan`, `implement`, `submit`, `review`, `land` remain separate stations.**
Each defends a distinct boundary with a distinct failure mode (Sequence: a
step earns its place by the failure its absence causes): premature mutation
(plan), untested code (implement), unverified claims (verify), undeliverable
or history-overwriting proposals (submit), unexamined change (review), wrong-
version application and stale closure (land). Merging any of these would blur
a boundary that is load-bearing; merging take+specify and verify+document
removed boundaries that were not (entry/contract share the boundary "work
begins"; verification/documentation share the boundary "work is complete").

### Entry: two sources, one artifact

The scoped pipeline activates on a `work-unit` artifact, but the live
planning surface is the forge tracker, and before this redesign the only
path to a work-unit artifact was `decompose`'s create path — which refuses
to adopt a pre-existing ticket (`create-ticket` is first-delivery-only).
The natural developer entry, "start on ticket #N" for a ticket already on
the tracker, had no path: `decompose` would not adopt it, `runa take <id>`
was retired, and runa-native decompose is future work.

The **methodology half** of that entry is decided here: the `acquire` skill.
Given a reference to an existing forge ticket on either forge, an agent in a
scoped session reads the ticket through the existing `read-ticket` mechanic
and materializes a `work-unit` artifact from it, after which `take` proceeds
unchanged. The governing constraints:

- **Acquisition produces the work-unit artifact; take's contract is
  untouched** (take still requires/triggers on `work-unit`).
- **One-way derivation**, ticket → artifact (Single Home): the ticket is the
  planning home, the artifact its execution-scoped snapshot, `handle` the
  back-link. Nothing in acquisition writes content back to the ticket.
- **Adopt, don't create.** Acquisition is the mirror of decompose's create
  path — decompose creates the ticket it delivers; acquisition adopts the
  ticket it is given — and creates no ticket. `handle` is the ticket's, and
  the tracker-backed `work-unit-<N>-<short-slug>` instance-id convention
  matches decompose's, so acquired and decomposed work-units are
  indistinguishable downstream.
- **No new mechanic, artifact type, or schema.** The forge read resolves
  through `read-ticket`; delivery is through the existing `work-unit` MCP
  tool. Acquisition is skill-side intake reaching the store through
  decompose's declared output tool — the same shape as `research`-record's
  `may_produce` bridge — so `decompose` remains the sole manifest producer
  of `work-unit`.
- **Gaps route to refinement, never to invention.** Where ticket content
  does not map onto required schema fields (no extractable acceptance
  criteria, empty body, non-open ticket), the materializer surfaces a named
  work-unit-quality defect routed to `decompose`'s `refine-work-unit`
  discipline rather than fabricating content.
- **Claiming stays take's.** Acquisition materializes; take claims the
  tracker in its workspace-prep step. The one-way boundary stays clean.

The **runtime half** — a cold-start entrypoint that accepts a ticket
reference and opens the scoped session in which acquisition runs (so the
operator types the equivalent of "take runa#14" against an empty store) —
needs a runtime change and stays flagged below as
[tesserine/runa#188](https://github.com/tesserine/runa/issues/188). The
methodology half is exercisable today: acquisition runs in a `decompose`-
scoped session (which serves the `work-unit` tool), and once the artifact
exists the cascade computes `take` next.

### Friction map — what each station removes

| Station | Unsupervised-agent failure it prevents |
|---|---|
| `take` | Coding toward an undefined "done"; dirty/unbranched workspace; working from memory instead of the work-unit; scope creep from the first minute |
| `plan` | Mutating with unresolved design choices; imagination-planning; re-opening tradeoffs mid-implementation |
| `implement` | Code without failing tests; testing-after; over-engineering beyond the test |
| `verify` | "Should work now" — completion claims without fresh evidence; silent documentation drift |
| `submit` | Verified work sitting unreviewable; forge-specific hacks; revision rounds overwriting history |
| `review` | The author's momentum approving itself; unexamined or out-of-scope change landing |
| `land` | Applying the wrong proposal version; stale tracker state; closure without a record |

The cross-cutting skills (`reckon`, `contract`, `debug`, `resolve`,
`research`, `code-review`, `orient`) fire on triggers, not at stations, and
were preserved as the cognitive layer — re-expressed to the architecture
standard, not redesigned away.

### The instruction standard

Every protocol main file: 3–7 high-level steps a reader grasps at a glance,
with depth factored into `references/` subdirectories and the deep
disciplines factored into skills. Repeated per-protocol artifact-delivery
blocks are retained deliberately — each protocol is injected standalone into
a fresh context, so per-unit self-containment is transmission-justified, not
duplication. Skills with large recognition catalogs (`reckon`, `debug`) keep
a compressed recognition *index* in the main file — the names must be in
context to fire passively — with full expositions in references.

### Resolution of the grounded tensions

1. **The entry's job once selection is moot** → the entry is where done gets
   defined: workspace + frame + behavior contract. (Above.)
2. **Self-contradicting shape** → the five-step lifecycle prose is gone;
   every surface (manifest, protocols, orient, README,
   connecting-structure) now states the same seven-station shape. The
   session-open/close framing in old take — which made the *session* the
   unit and invited stopping mid-pipeline — is replaced by work-unit-scoped
   stations under the runtime's cascade.
3. **What threads the pipeline** → the behavior contract, not a claim.
   `claim` and `behavior-contract` did not merge; `claim` was deleted as
   unearned structure and the contract took the entry capstone.
4. **The fragile back half** → three moves: fewer stations (9 → 7); an
   unbroken trigger chain with no indirection (verify's evidence directly
   triggers submit; the dissolved document station no longer sits between);
   and instructions that end at the capstone with the runtime carrying the
   work onward — no protocol now describes a "session close" that invites
   stopping. Under the cascade, continuation is the runtime's job; the
   methodology's job is that no station's trigger dead-ends.
5. **Scale-down** → internal proportionality, not topology forks: "depth
   scales with the change" is stated in `orient` and at the scalable
   stations (`take`, `plan`). A trivial change traverses the same seven
   stations lightly (one-scenario contract, one-decision plan, one cycle).
   Branching the topology for "small" work was rejected: runa's trigger
   algebra would force a second artifact vocabulary and review/land would
   need to handle both — two methodologies wearing one manifest
   (Parsimony; "without forking into two methodologies").
6. **Where judgment about the change is exercised** → `review`, the
   independent-judgment gate. runa's session-surface contract places
   transition authority in typed disposition artifacts and explicitly
   excludes per-operation human approval — so the gate does not enforce a
   human signature; it enforces **independence from the author**, a change
   judged by a context that did not produce it. That context is a fresh or
   separate agent by default, the operator when chosen; human review is an
   available choice, not the gate's definition. The pipeline auto-carries
   through `submit` — a proposal must exist to be reviewable, and an
   undelivered change is invisible to judgment. The operator who wants
   tick-by-tick cadence has interactive mode (`runa go`); the operator who
   wants to *be* the reviewer reviews at the forge surface the proposal
   handle names, and the disposition records reviewer identity. Flows that
   "stopped short of submit" were accidents of the session framing removed
   in (2).
7. **The crisp entry tool** → split by layer. The methodology half — a
   ticket → work-unit materialization path — is decided here as the
   `acquire` skill (see *Entry: two sources, one artifact*). The runtime
   half — a cold-start entrypoint that opens the session acquisition runs in
   — stays flagged below as a coordinated runtime dependency
   ([tesserine/runa#188](https://github.com/tesserine/runa/issues/188)).

### What was deliberately preserved

- The forge-neutral `submit → review → land` reference arc (ADR-0002's six
  invariant operations, ADR-0003's typed dispositions, immutable proposal
  versions, the work_unit+version binding at land). It was recently
  reckoned, two-forge-proven, and correct.
- The TDD and verification iron laws verbatim in force (re-expressed, not
  weakened).
- The work-unit model, mechanics library, conformance machinery, and the
  prose-pinned delivery-contract tests (evolved only where the topology
  changed).
- Revision rounds flow through `submit` (not a back-edge to `implement`):
  runa's DAG has no mid-pipeline back-edges, and the revision loop through
  the proposal version history is the existing, working cycle. Submit's
  instructions now say explicitly that findings are addressed with the
  original disciplines (failing test first for behavioral findings).
- Verify keeps delivering honest evidence even when coverage is incomplete
  — gaps flow to review, which blocks. This is the current settled
  semantics; stopping the line inside verify is impossible to express in
  the trigger algebra without a runtime change, and honest-evidence +
  review-block achieves the same protection visibly.

## Flagged for the operator

- **Coordinated runtime dependency — cold-start acquisition entrypoint.**
  The methodology half of acquisition is delivered here (the `acquire`
  skill; see *Entry: two sources, one artifact*), and runs today inside a
  `decompose`-scoped session. What remains runtime-side is the cold-start
  affordance: an entrypoint that takes a bare ticket reference against an
  empty store and opens the scoped session acquisition runs in — so the
  operator types "take runa#14" with nothing materialized yet. That is the
  retired `runa take <id>` shape, filed as
  [tesserine/runa#188](https://github.com/tesserine/runa/issues/188); the
  redesign is shaped so the entrypoint slots in front of `take` without
  further methodology change.
- **Forge identity namespace.** The protocols reference only invariant
  operations resolved through `connector capability tool`; the resolver reads the
  runtime-owned `connector deployment *` identity atoms (the #389/#390 repair, on
  which this redesign now sits), with endpoint and repo-id remaining
  methodology-owned atoms.
- **Best-of-field call — verify may repair its own gate failures.** When
  fresh verification fails, verify's instructions route through `debug` and
  permit the minimal fix within the increment (then a fresh full gate)
  rather than stalling, because no protocol downstream of implement can
  re-fire it. This trades a sliver of gate purity for line movement; the
  alternative (fail the verify tick and require operator intervention) is
  available by policy if preferred.
- **Best-of-field call — reviewer independence.** The invariant the gate
  protects is independence from the author, not human review: the change is
  judged by a context that did not produce it. The methodology names the
  rubber-stamp risk and records reviewer identity, but does not mandate
  *who* the independent context is (fresh agent context, external agent, or
  operator). Mandating an operator-only review would contradict the session
  surface contract's no-per-operation-approval invariant; mandating a
  particular agent identity is runtime policy, not methodology. Human review
  is therefore an available choice within the gate, never the gate's
  definition.

## Consequences

### Good

- BDD begins where work begins; the contract is in context at every
  judgment, including review — the reviewer finally sees the specification
  being judged against.
- Two protocols, two artifact types, and one trigger indirection removed;
  every surviving part has a named failure it prevents.
- The methodology self-describes consistently at every level; protocols are
  glanceable (5 steps each) with depth one reference away.
- The pipeline scales down honestly: same path, proportional dose.

### Neutral

- The entry tick is larger (workspace + contract). Judged correct: the
  contract is authored while the framing is fresh, and the two were always
  one act in lived practice.
- groundwork-install drops the `specify` and `document` entries on sync;
  installed protocol copies carry their `references/` directories alongside.

### Bad / accepted risks

- Verify's tick now carries two concerns (evidence gate + documentation
  review). Accepted because both examine the finished change and one
  artifact records both; if the doc review proves heavy in practice it can
  be re-stationed without touching the spine.
- Recognition catalogs factored out of `reckon`/`debug` main files could
  reduce passive firing; mitigated by the in-file recognition indexes
  (names + one-line triggers stay in context).
