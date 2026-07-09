# ADR-0010: Content Kinds — Behavior and Meaning

**Status:** Accepted — operator-ratified 2026-07-10 (delivered with groundwork#582) \
**Date:** 2026-07-10 \
**Amends:** [ADR-0007](0007-dimension-agnostic-contract-machine.md) — the
criterion-level `check_kind` apparatus it introduced retires; its
dimension-agnostic one-machine core stands, and is what this decision
restores to full strength. \
**Traces to:**
[Contract-First](https://github.com/pentaxis93/principles/blob/main/compositions/contract-first.md),
[Verifiable Completion](https://github.com/pentaxis93/principles/blob/main/principles/verifiable-completion.md),
[Single Home](https://github.com/pentaxis93/principles/blob/main/principles/single-home.md),
[Honest Signal](https://github.com/pentaxis93/principles/blob/main/principles/honest-signal.md),
[Grounding](https://github.com/pentaxis93/principles/blob/main/principles/grounding.md);
origin [groundwork#582](https://github.com/tesserine/groundwork/issues/582)
(the 2026-07-10 contract-discipline audit).

## Context

[ADR-0007](0007-dimension-agnostic-contract-machine.md) built one contract
machine: every dimension a first-class citizen, every criterion carrying
identical obligations — statement of done, hollow delivery, a check. The
epic's symmetry invariant says those obligations are *identical* across
dimensions. The machine is sound and this decision does not touch its
core; the [contract skill](../../../skills/contract/SKILL.md) remains the
home of the discipline and the
[contract schema](../../../schemas/contract.schema.json) the home of the
surface.

The invariant, however, was resolved **to the floor**. A limitation of the
execution environment — which class of check may gate continuous
integration — entered the specification ontology as
`check_kind: "attested"`, a kind-of-check on equal footing with
`"executable"`. Because an attested check was cheaper to author than an
operational one, it became the conventional apparatus of two whole
dimensions: documentation and code-quality criteria defaulted to reviewer
attestation, and "identical obligations" came to mean *everyone may sink
to the cheapest check* rather than *everyone rises to a real one*. The
root cause is structural, not behavioral: a deployment fact lived inside
the specification artifact, and every downstream author then designed to
it in good faith.

The 2026-07-10 operator audit of the contract discipline surfaced this
and is this decision's origin. Its authority, however, is the principle
below and the probe evidence carried in this document — not the
conversation that surfaced them.

## The governing principle

**A resource or cost limitation may override a check's binding; it never
authors the contract's ontology.**

`check_kind` is the leak this decision retires: a deployment fact that
lived in the specification ontology and floored the symmetry invariant.
What a criterion *is* — what it claims and how that claim is natively
checked — belongs to the contract. Where and how the check *runs* — and
what a given environment can afford today — belongs to a policy layer the
contract never encodes. The two concerns separate below.

## Decision

### Two content kinds

Every contract criterion carries exactly one **content kind**. The kinds
cut across artifact types rather than following them:

- **behavior** — what the artifact *does*. Natively checked by
  **execution**: the system runs, a documented procedure reproduces its
  stated outcome, a fitness function holds over the tree.
- **meaning** — the argument, distinction, or insight the artifact
  *transmits*. Natively checked by **reconstruction**: a cold recipient,
  equipped only with the artifact, is graded against a stated
  proposition.

The routing discriminator is a decision procedure, not a vocabulary:

1. *Following the artifact reproduces a stated outcome* → **behavior**.
2. *The artifact's distinction generalizes in a cold recipient graded
   against a stated proposition* → **meaning**.
3. *The claim is content-identity across homes* → the parked residue
   (next section), neither kind.

The kind set is **closed and grows only by ADR**. The residue rule is the
set's sensor: a criterion genuinely fitting neither kind is the signal
that a third kind is earning its place — the door stays watched, never
open by default.

The former artifact-category dimensions — behavior, documentation,
code-quality — are re-grounded as **source and coverage lenses**: they
enumerate where criteria come from and what a change must cover, and they
never determine a check. A documentation-lens criterion may be behavior
(its procedure runs) or meaning (its argument transmits); the lens says
what must be covered, the kind says how the criterion is checked. What
the schema's `dimension` field carries next is
[#583](https://github.com/tesserine/groundwork/issues/583)'s scope, not
decided here.

### The parked residue: semantic restatement

One residue class emerged from the probe, systematic across both
contracts: the *no-semantic-restatement* half of Single-Home criteria —
"this surface does not re-encode that home's content in other words."
That claim is neither what the artifact does nor an argument it
transmits; it is content-identity across homes, checked by comparison.

Interim typing: **behavior-kind fitness with an interpreter-bound
evaluator** — the binding layer (below) carries it without strain. One
class from two contracts does not earn a kind: it is named, given this
interim home, and **parked at the third-kind door — neither ratified as a
kind nor dissolved by fiat.**

### Checks are operational procedures

A criterion's check is **contract content in operational form** — four
fields, always:

- **actor** — who or what performs the check: the system under test, an
  instantiated cold recipient, or a fitness function.
- **procedure** — the steps the actor performs.
- **observable** — the pass/fail the procedure yields.
- **declared cases** — concrete conforming and falsifying values: the
  input that passes and the input that fails, stated in the contract.

Nothing is inherently attested. Every criterion — behavior or meaning —
states the procedure that would check it, whether or not today's
environment runs that procedure mechanically.

### Meaning checks: two shapes

Both are reconstruction-native:

- **transmission** — a cold recipient equipped only with the artifact
  *applies, classifies, or authors*, and the output is graded against the
  stated proposition.
- **soundness** — a reviewer reconstructs the artifact's own ground-map:
  every normative claim traces to a principle or the stated general
  problem, never to an exemplar's authority.

One well-formed criterion of each shape, adapted from the probe's
re-typings:

**Transmission** (from #531's `cold-author-in-kind`):

> **proposition:** the delivered guidance is sufficient for an author
> with no session context to produce a principle-derived criterion in
> kind. \
> **kind:** meaning · **actor:** instantiated cold recipient (fresh
> agent, artifact-only context). \
> **procedure:** the recipient authors one criterion for a stated novel
> methodology unit using only the delivered text; the output is graded
> against the guidance's own quality bars — grounded, hollow named, check
> operational. \
> **observable:** the authored criterion meets every bar — pass; misses
> any — fail. \
> **conforming case:** the recipient produces a criterion whose hollow a
> lazy delivery would actually commit and whose check names actor,
> procedure, and observable. \
> **falsifying case:** the recipient produces a restated acceptance
> criterion with a bare pass/fail assertion and no hollow — the guidance
> transmitted vocabulary, not capability.

**Soundness** (from #531's `exemplar-generalized`):

> **proposition:** every normative claim in the delivered document traces
> to a principle or the stated general problem, not to the worked
> example's authority. \
> **kind:** meaning · **actor:** reviewer as reconstruction instrument. \
> **procedure:** enumerate the document's normative claims; for each,
> reconstruct the chain of ground to a principle or the stated problem;
> flag any claim terminating at "the exemplar does it this way." \
> **observable:** every claim traces — pass; any exemplar-grounded norm —
> fail. \
> **conforming case:** a claim grounded in Single Home's
> consult-don't-model corollary. \
> **falsifying case:** "criteria should number eleven because the
> reference contract has eleven."

### Execution binding is policy

Where and how a check *runs* is a **binding**, selected per criterion —
policy content, single-homed and separate from contract semantics:
**`ci`** (the procedure runs mechanically and gates the merge),
**`harness`** (the procedure runs mechanically outside the merge gate —
e.g. the cold-recipient harness of
[#586](https://github.com/tesserine/groundwork/issues/586)), or
**`manual`** (a named actor performs the procedure and signs the
performance). The binding register's single home is
groundwork **`policy.toml`** (`[execution-binding]`), a root-level file
beside `manifest.toml`, created by
[#584](https://github.com/tesserine/groundwork/issues/584). It sits
beside the manifest rather than inside it for the reason
[ADR-0005](0005-principles-corpus-configuration.md) drew for its own
surface: the manifest is the invariant topology the runtime executes,
while a binding register is revisable operational policy — different
revision cadence, one file each.

The environment constraint that produced the original leak lives in that
policy home as one revisable line, and is stated exactly once in this
decision: **no interpreter-graded check gates CI.** When the constraint
falls, the line is revised at its home and no contract changes.

**Attestation is redefined.** It is not a kind of check; it is the
**manual binding** of a criterion's stated operational procedure — a
named actor performs the contract's own procedure and signs that
performance. `check_kind` retires on the path stated below.

**Bindings strengthen monotonically:** manual → harness → ci. Migrating
a criterion's binding up the ladder requires no contract edit — the
procedure was always the contract's; only where it runs changes.

### Evidence is binding-stamped

Every performed result records the binding that discharged it
([#585](https://github.com/tesserine/groundwork/issues/585) carries the
[completion-evidence schema](../../../schemas/completion-evidence.schema.json)
consequence). Two consequences follow:

- **Honest signal:** a manually-discharged criterion is never presentable
  as machine-verified — the stamp is the surface telling the truth about
  what checked it.
- **Debt register:** the binding profile is queryable per contract and
  per repository, so per-criterion degradation stays permanently visible
  and its trajectory is managed downward, not forgotten.

### Recovered CI coverage, demonstrated

The probe (evidence below) shows the floor design consigned to
attestation checks that bind deterministically **today**:

1. **Ordering, data-flow, and routing gates over declared surfaces** —
   #465's `placed-at-acquisition-boundary` (an ordering invariant over
   the declared sequence) and `regrounds-residue-not-record` (a data-flow
   gate: the proceed path's inputs include live substrate) re-type as
   behavior and bind as fitness functions over the tree.
2. **Structural help-surface gates** — the `wish --help` case: the
   mechanical discriminator is a non-empty argument-contract section
   distinct from the slogan line, so a slogan-over-blank-arguments hollow
   fails a structural gate with no interpretation involved.
3. **Executable documentation examples** — a documented procedure runs
   and reproduces its stated outcome, the behavior kind's native check
   applied to prose.

### Retirement path and graded retrofit

`check_kind` retires through the contract-schema v-next unit
([#583](https://github.com/tesserine/groundwork/issues/583)) — never an
edit this decision performs. Retrofit of already-generated surfaces
adopts the grading #539 established: **met-cold ⇒ scheduled; touched ⇒
in-change.** Landed contract and evidence records are never rewritten —
they are true records of the machine that produced them.

## Follow-on graph

Filed with this decision as origin, blocked on its ratification; ordering
after ratification is the operator's:

- [#583](https://github.com/tesserine/groundwork/issues/583) —
  contract-schema v-next: `kind` + operational check; `check_kind`
  retires. Registered consumer:
  [weforge-ops#5](https://github.com/pentaxis93/weforge-ops/issues/5).
- [#584](https://github.com/tesserine/groundwork/issues/584) —
  binding-policy home: `policy.toml`.
- [#585](https://github.com/tesserine/groundwork/issues/585) —
  completion-evidence v-next: binding-stamped results.
- [#586](https://github.com/tesserine/groundwork/issues/586) —
  transmission-harness epic (post-M1): cold-recipient checks at the
  harness binding.
- [#587](https://github.com/tesserine/groundwork/issues/587) — re-ground
  epic #484's frame and #486/#487/#488 to this ontology.
- [#573](https://github.com/tesserine/groundwork/issues/573) (existing) —
  the ratified form's first client, re-authored at pickup.

## Evidence: the 25-criterion probe

Method: the two most recent contracts of record — #465's 14 criteria and
#531's 11 — were re-typed whole under the two kinds using the routing
discriminator above. Full record:
[#582's probe log](https://github.com/tesserine/groundwork/issues/582#issuecomment-4930143381);
carried here as the decision's evidence.

| criterion | old label | kind |
|---|---|---|
| 465 disposition-single-and-typed | beh/exec | behavior |
| 465 non-proceed-withholds-from-define | beh/exec | behavior |
| 465 freshen-record-required-fields | beh/exec | behavior |
| 465 finding-covers-dependency-graph | beh/exec | behavior |
| 465 proceed-body-is-standalone-spec | beh/exec | behavior |
| 465 fires-identically-both-modes | beh/exec | behavior |
| 465 discipline-enforced-in-ci | beh/exec | behavior |
| 465 reader-can-state-the-pass | doc/att | behavior |
| 465 reader-can-route-each-disposition | doc/att | behavior |
| 465 regrounds-residue-not-record | cq/att | behavior |
| 465 placed-at-acquisition-boundary | cq/att | behavior |
| 465 composes-homes-restates-none | cq/att | behavior + residue ⚑ |
| 465 enforcement-consults-not-models | cq/att | behavior |
| 465 record-is-positive-log-entry | cq/att | behavior |
| 531 trigger-boundary-decidable | beh/att | meaning |
| 531 mechanism-open-quality-closed | beh/att | meaning |
| 531 operational-hollow-detectable | beh/att | meaning |
| 531 structural-coherence-gates | beh/exec | behavior |
| 531 cold-author-in-kind | doc/att | meaning |
| 531 source-mapping-auditable | doc/att | meaning |
| 531 attestation-teeth-taught | doc/att | meaning |
| 531 evolvability-outcome-actionable | doc/att | meaning + behavior (clean split) |
| 531 quality-consult-not-model | cq/att | behavior + residue ⚑ |
| 531 exemplar-generalized | cq/att | meaning (soundness type specimen) |
| 531 schema-untouched | cq/exec | behavior |

Findings, in order of weight:

1. **Resolving power.** Re-typed, #465 is **meaning-silent** — zero
   meaning criteria on a methodology surface whose job includes
   transmitting judgment. The old model certified the unit covered
   because retrieval checks filled the documentation category. The
   rotation catches what the old axis blessed.
2. **Label orthogonality.** Six of #465's attested criteria re-type as
   behavior — ordering, data-flow, routing, and structural invariants
   CI-bindable today. Three of #531's behavior-labeled criteria re-type
   as meaning: they were never system behavior; the schema had no word
   for transmitted distinction.
3. **One systematic residue** — the semantic-restatement class, parked
   above.
4. **Two meaning shapes earned** — transmission and soundness, both
   instantiated above.
5. **Propositions confirmed in the wild** — #531's meaning criteria
   already carry proposition, probe, and hollow in nearly the target
   form; the pattern needs a schema home, not invention.

Verdict: 24/25 clean (three compound criteria split naturally, which the
model predicts and which sharpens them), one honest residue. The probe is
stronger than non-refutation: it demonstrates diagnostic superiority over
the model it replaces.

## Consequences

- **The symmetry invariant reads at the ceiling.** Every criterion, under
  every lens, carries an operational check; the identical obligation is a
  real procedure, not a floor everyone may sink to.
- **Costs accepted, visibly.** Retrofit is graded, so old and new
  ontologies coexist across the record with the boundary explicit;
  manual-bound criteria remain — permanently stamped, queryable, and
  managed downward rather than hidden; the semantic-restatement residue
  stays parked and unresolved by design.
- **Authoring changes now; validation changes at #583.** Contract authors
  route criteria by the discriminator and write operational checks from
  this decision forward; the current
  [contract schema](../../../schemas/contract.schema.json) remains the
  validation authority until v-next lands, per the series rubric that a
  Proposed decision is authoritative for direction while the operator may
  still revise it.
- **The leak class is closed at its source.** Any future environment
  limitation lands as a policy line at the binding home — the ontology
  has no field for it to occupy.
