# ADR-0003: Disposition as Artifact Type

**Status:** Provisional \
**Date:** 2026-05-31 \
**Traces to:** ADR-0002 (Methodology Sovereignty); `tesserine/runa`
`docs/interface-contract.md` (the three-primitive interface);
[Sovereignty](https://github.com/pentaxis93/principles/blob/main/principles/sovereignty.md).
Governed by
[Parsimony](https://github.com/pentaxis93/principles/blob/main/principles/parsimony.md)
and [Evolvability](https://github.com/pentaxis93/principles/blob/main/principles/evolvability.md)
(corollary *scale honesty*) — all at
[pentaxis93/principles](https://github.com/pentaxis93/principles), the
canonical corpus. (Originally cited via `tesserine/commons` PRINCIPLES.md P1
and `with-claude` principles #5/#10, since ascended.)

## Revision (2026-05-31): outcomes are a required-choice output, not `may_produce`

Post-decision governance review found the original mechanism incomplete. The
*decision* below stands unchanged — disposition is the artifact type (sub-choice
(a)), and the within/cross rule holds. What changes is how the "exactly one
outcome per run" obligation is enforced, and the cross-repo consequence.

The original draft declared the outcome types as `may_produce` and located the
"exactly-one-outcome" guarantee in the C-2 graph plus the conformance check. That
is insufficient. Grounded against runa (`libagent/src/model.rs`):
`ProtocolDeclaration` has four flat output lists — `requires`, `accepts`,
`produces` (all required), `may_produce` (all optional) — with no grouping or
cardinality, so "produce exactly one of {A, B}" is inexpressible. The C-2 graph
and the conformance check are **authoring-time**; runa is the only **runtime**
enforcer of outputs, and `may_produce` makes it *abstain*. A run that reaches no
terminal (an erroring agent) then emits no outcome type and **nothing catches it
at runtime** — land never fires, the revise cycle never fires, the work unit
stalls silently. Worse, this is a regression: the pre-(a) single-`produces`-type
design *did* fail at runtime when review produced nothing; `may_produce` drops
that guarantee. A load-bearing invariant with no runtime enforcer is what #10
forbids. (A completion *anchor* in `produces` does not fix it: review could
complete having emitted the anchor but no verdict, still stalling land/revise.)

**This is structural, not semantic — so it does not reopen the field predicate we
rejected.** "Exactly one of a declared set is produced" is output-type cardinality,
the same currency `produces`/`may_produce` already trade in. runa need not know
what the outcomes *mean*, only that one of a declared set must appear. Content-/
semantics-blindness is preserved.

**Corrected mechanism.** Add a **first-class required output choice** to runa: a
named, required output group with **exactly-one-of** cardinality over a registered
type set — a third output edge alongside `produces`/`may_produce`, runtime-enforced.
review declares its two outcomes in this group; runa fails the protocol if the run
does not produce exactly one. The C-2 contract gains the matching declaration and
the conformance check maps the C-2 outcome terminals onto the runa group (see the
revised *Routing* and *Conformance obligation* below). Per Parsimony, build
exactly-one-of over a set (N≥2, which also serves escalation #233); do **not**
pre-build a general min/max cardinality language.

**Consequence delta:** the original "no runa change / single-repo" consequence is
**superseded** — a bounded runa interface change (the third edge) plus an
`interface-contract.md` revision are now in scope, and a runa substrate unit is
sequenced ahead of #331. As a bonus the required-choice edge also resolves the
freshness concern: the produced outcome is now real completion evidence, so
review's `on_change` suppression is reliable. The C-2-/conformance-only path (no
runa change) is ruled out — it leaves the invariant with no runtime enforcer.

## Context

A protocol can route on its own outcome *within* itself — `verify.toml` has two
terminals that branch on a `coverage_status` edge condition; the review flow
classifies findings as `approved` or `needs_revision`. But the **cross-protocol**
activation layer is outcome-blind. runa activates a successor protocol on artifact
**type + validity + timestamp**; it never reads a payload field. So "land only
when review is **approved**" cannot be expressed by the current substrate, because
a type-level trigger on the review output would also fire for a `needs_revision`
result and activate land on a non-release state.

This is a **recurring shape**, not a land-specific quirk. The same need appears in
review (approved vs needs-revision), verify (covered vs incomplete), and escalation
(#233, route by severity): in each, the successor must be chosen by *how* the
predecessor finished. The end state is therefore a uniform, first-class way to
represent a protocol's outcome and route on it — not a one-off gate.

The #329 reference-arc design doc named this gap but mislocated it. Its Decision 3
concluded that landing-on-disposition requires **a new runa field predicate** — a
trigger of the form `review-findings.disposition == "approved"` — and recorded #332
as blocked on that runa-side addition. This ADR overturns that conclusion. The gap
is not a missing runtime capability; it is a representation choice, and the correct
representation needs no change to runa at all.

### What grounds the decision

- **runa cannot, and should not, read inside an artifact.** `libagent/src/trigger.rs`
  defines exactly five trigger forms — `on_artifact`, `on_change`, `on_invalid`,
  `all_of`, `any_of` — each keyed on an artifact-type *name*. There is no field,
  payload, or predicate surface. This is deliberate: the interface contract states
  runa "does not interpret methodology semantics," and its own approval example
  routes on a *type* (`on_artifact("auto-approve")`), not a field.
- **Content-blindness is the correct placement of decision authority, not a
  limitation to route around.** A field predicate in runa would put the deciding
  logic — the equality test, the threshold — inside the runtime, and would couple
  runa to every methodology's field names and value vocabularies across the
  repo boundary. The contract makes outcome *semantics* methodology-owned; the
  producing protocol is the right place to decide the verdict.
- **A field predicate cannot be scoped to disposition.** The intent is narrow but
  the mechanism is general: one cannot build "runa reads the disposition field,"
  only "runa can read a field" — an open-ended field-predicate language. The next
  routing need (severity, a coverage threshold) points straight at it. Mechanisms
  outlive the intentions that justify them.

## Decision

### The primitive

A protocol's **outcome is the artifact type it produces.** Outcome-bearing
protocols whose outcome must drive a successor produce a **distinct artifact type
per terminal disposition**, drawn from a registered outcome vocabulary. The result
is not written into a field; it *is* which kind of artifact was produced.

Worked example (the reference arc): the `review` protocol produces **either**
`change-approved` **or** `change-needs-revision`. Which one it produces is the
disposition. The full review record — reviewer, reviewed-at, reviewed version,
classified findings — rides inside whichever type was produced.

This realizes the primitive entirely in the **methodology layer
(commons/groundwork), with runa unchanged.**

### The governing rule

> A fact becomes an artifact **type** only when a *successor protocol* must route
> on it. A fact that only steers *within* one protocol stays a **field**.

The number of outcome types thus equals the number of distinct cross-protocol
routing destinations the methodology genuinely has — no more. `verify.toml`'s
internal `coverage_status` edge condition is correct as a field today precisely
because no successor currently routes on covered-vs-incomplete; it becomes a typed
outcome only when one does. Continuous- or many-valued routing reduces to typed
outcomes the same way: the producing protocol applies the threshold (a methodology
semantic) and emits the **verdict** as a type. The methodology decides; runa
dispatches.

### Routing

Successors route with the **existing** trigger vocabulary:

- `land` activates on `on_artifact("change-approved")`. It never sees a
  `change-needs-revision`, so a non-release state cannot activate it.
- The revise / re-review cycle continues on `on_change("change-proposal")`, per
  #329 Decision 1 — a new immutable proposal version re-fires review. The cycle is
  driven by new proposal versions, not by a disposition-agnostic review type.

"Exactly one outcome per run" is enforced at runtime by a **required-choice output
group** (see the 2026-05-31 Revision above): review declares its two outcome types
in a named, required exactly-one-of group; runa fails the protocol unless the run
produces exactly one member. The C-2 graph still expresses the same shape at
authoring time — mutually-exclusive, exhaustive terminals (ADR-0002), each mapping
to one group member — and the conformance check verifies the manifest group matches
the set of outcome-terminal `artifact_produced` values, so the methodology layer and
the runtime agree on the same single source (the C-2 terminals). The earlier draft's
`may_produce` declaration is superseded: it left the obligation unenforced at runtime.

### The sub-choice: outcome *is* the type, with no separate field

Two representations were on the table:

- **(a)** Outcome *is* which typed artifact was produced — no disposition field.
- **(b)** A single record artifact carrying a literal `disposition` field, **plus** a
  separately reified routing-signal artifact for runa to trigger on.

**This ADR settles on (a).** Reasons:

- **Parsimony (#5).** (a) has one source of truth: the type carries both the record
  and the routing signal. (b) holds the disposition fact in two places — a field
  value and an artifact's existence — that no single mechanism can collapse, and
  that must be kept in agreement forever. That irreducible second source is what
  Parsimony forbids ("if two mechanisms must agree, find the single mechanism
  underneath them").
- **Scale-Honest Design (#10).** (b)'s coherence is hand- or check-policed across a
  multiplying methodology; (a) makes disagreement structurally impossible — there is
  no second place to disagree.
- **The one thing (b) buys is not lost under (a).** (b)'s single rich review record
  survives in (a): the produced outcome type carries the full findings record.
- **Different dispositions carry different supporting data, which argues *for*
  distinct types.** Today's `review-findings` schema is one type emulating two via a
  conditional `if/then` (an `approved` instance may contain no blocking finding; a
  `needs_revision` instance must contain at least one). That conditional is the tell
  that two shapes are crammed into one type. Splitting them is the accurate model,
  not a workaround forced by runa's blindness.
- **The (a) schema cost is bounded and DRY-able.** The outcome types share most
  fields (work-unit, reviewed version, reviewer, findings). A shared `$defs` base
  `$ref`'d by each type carries the common envelope; each type adds only its
  disposition-specific constraint. The shared base is one source — unlike (b)'s
  split fact.

### Conformance obligation

What makes this a *primitive* rather than a per-gate habit is a conformance check,
named here as an outcome (its enforcement, not its implementation):

1. An outcome-bearing protocol's terminals each declare an `artifact_produced` that
   is a member of the registered outcome vocabulary (not an arbitrary or shared
   record type used across dispositions).
2. A successor that routes on an outcome triggers on one of those registered
   outcome types via `on_artifact` (or composed with it), never on a
   disposition-agnostic type.
3. The within/cross rule is enforceable: a fact routed on by a successor must be a
   type; it must not be smuggled as a field a successor cannot see.
4. The manifest's required-choice output group for an outcome-bearing protocol
   matches the set of `artifact_produced` values across its outcome terminals — the
   methodology layer and the runtime declare the same single source.

This is an addition to the C-2 / C-5 conformance surface that already dispatches
C-2/C-3/C-4, coordinated with the new runa output edge (Revision above). It need not
be implemented in the session that records this ADR; it is sized as a substrate
addition and lands with the runa edge ahead of the consuming arc (see below). It is
not trivial enough to claim done here.

### The bounded runa change now in scope, and what still does not change

This decision adds **one** thing to runa: a required-choice output edge (the
exactly-one-of group, Revision above) and the matching `interface-contract.md`
revision. That is bounded — one new output modality, built as exactly-one-of, not a
general cardinality language. What still does not change: runa remains
content/semantics-blind (the group is type cardinality, not field reading); no
trigger form changes; routing still uses the existing `on_artifact`/`on_change`
vocabulary. runa has no ADR convention (its `interface-contract.md` is its canonical
boundary doc), so the runa-side decision is recorded as that contract's revision,
commissioned with its enforcement as a single coherent change (a contract edge
without a runtime check would be worse than none).

## How #330–#334 consume it

- **#330 (submit C-2 contract).** Unchanged in shape: `submit` produces
  `change-proposal` (the input, not an outcome — proposals are not split by
  disposition). No new dependency.
- **#331 (review protocol + code-review skill).** `review` produces the typed
  outcomes `change-approved` / `change-needs-revision` instead of a single
  `review-findings`-with-disposition-field, declared in a required-choice output
  group. Authors the two outcome schemas (shared `$defs` base; per-type
  blocking-finding constraint) replacing `review-findings.schema.json`. **Depends on
  the runa required-choice edge and the matching C-2/conformance support landing
  first** (sequenced ahead of #331); it cannot honestly declare the group until the
  edge exists.
- **#332 (land C-2 contract).** **Its runa-substrate dependency is removed.** Land
  activates on `on_artifact("change-approved")` using the existing trigger
  vocabulary. #329 Decision 3's field-predicate prerequisite is superseded by this
  ADR; #332 is no longer blocked on any runa-side work.
- **#333 / #334 (GitHub / SourceHut mechanics + dogfood).** Unaffected by the
  representation choice; the disposition reflection (`reflect-disposition`) reports
  the outcome the produced type already names.

`verify.toml` is a **latent consumer**, not a Step-2 obligation: it produces one
`completion-evidence` from both terminals today, which is correct while no successor
routes on covered-vs-incomplete. It adopts the primitive (splitting into typed
coverage outcomes) when a successor needs to route on its outcome. Recorded as a
follow-up, not rescoped into this arc (Sufficiency).

## Consequences

### Good

- The cross-protocol outcome-routing gap is closed without a field predicate and
  without any new open-ended runtime surface; the one runa addition is bounded
  type cardinality (exactly-one-of), and the "exactly one outcome" invariant gains a
  real runtime enforcer (Revision above).
- One source of truth for each outcome; coherence drift between a field and a signal
  is structurally impossible.
- runa's content-blindness — its strongest scale and sovereignty property — is
  preserved, and the decision authority sits with the producing methodology.
- The within/cross rule gives a clean, parsimonious test for when a fact must be a
  type, bounding type count to genuine routing destinations.

### Neutral

- Outcome-bearing protocols gain one schema per disposition instead of one schema
  with a disposition field; the shared `$defs` base keeps the duplication to a single
  source. `review-findings.schema.json` is replaced by fresh authoring (consistent
  with ADR-0002's fresh-authoring migration), and the cost lands inside #331, which
  was deferred pending this decision — not as rework of landed code.
- The conformance check is a named obligation, implemented with the consuming arc,
  not in this session.

### Bad

- The #329 reference-arc design doc carries a now-superseded Decision 3 (the runa
  field-predicate prerequisite). Left unannotated it teaches a false requirement;
  it should be marked superseded by this ADR (a cheap docs follow-up).
- A future need to consume "the review outcome for a work unit regardless of
  disposition" would read a union of two types rather than one. No Step-2 consumer
  needs this; if one arises, a registered-vocabulary query (or an umbrella
  `accepts`) serves it without reintroducing a disposition field.
