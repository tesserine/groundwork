# The Skill Ontology and the Core/Protocol Seam

## Audience and Purpose

This note is for the agents and contributors who will draw the core/protocol
seam — the seam-ADR task of epic
[#466](https://github.com/tesserine/groundwork/issues/466) — and run the
per-asset audit that seam rests on. It is the conceptual foundation that work
consumes: the domain model of *skill* the factoring is built on, the typing it
produces, and the experiment that grounds it.

The content here is **constraints, not implementation instructions**. It names
what the seam ADR and the audit must make true, and the deeper structure they
are accountable to. The seam ADR distills these constraints into a ratified
decision with every belief traced to its enforcing file; this note is the prior
stage whose output that decision requires.

## Status

Design note, not an ADR — it precedes and feeds the seam ADR. **Provisional in the
strongest sense.** It is the crystallization of a two-domain reckoning
(groundwork × gazette): a first sketch, deliberately coarse, that sharpens as
domains accumulate. Where the ontology proves a stable cross-methodology
principle — it governs gazette as much as groundwork — it ascends to the
[commons](https://github.com/tesserine/commons) convention register or the
[principles corpus](https://github.com/pentaxis93/principles). It is grounded
here, at the factoring's present need, until the audit validates it; it is not
yet carved as ecosystem convention.

## Grounding: the two domains

The factoring is read from two methodologies, not one. groundwork carries
software from problem to merged change; [gazette](https://github.com/tesserine/gazette)
carries a historical record to a published periodical and maintains continuity
issue over issue. Held together they separate what is invariant from what is
domain.

What the two **share**: a `manifest.toml` topology runa reads, typed artifact
schemas, a chained pipeline whose stages each require the prior stage's output,
and a grounding gate (groundwork's `verify` against evidence; gazette's
`factcheck` against per-claim source trails). The pipelines are isomorphic in
shape — a planning front, a production middle, a grounding gate, a terminal that
emits the durable artifact plus continuity — and they share even a protocol
*name*: `survey`. A discipline that appears under one name in two unrelated
domains is the loudest signal that it is core, not delivery.

What differs is purely domain: the artifact types (`work-unit`,
`contract`, `implementation-plan` vs. `brief`, `beat`, `dispatch`,
`draft`), the pipeline steps (`define → … → land` vs. `survey → … → publish`), and
the forge mechanics.

The decisive observation: gazette today has schemas and a manifest and **no
`skills/`, no protocol bodies, no cognitive core of its own** — yet its
protocols plainly need reasoning. gazette is either going to duplicate the
cognitive disciplines or consume a shared core that does not yet exist as an
adoptable unit. The second case is the friction this epic names. **gazette is
the consumer already waiting on the extraction.**

## The domain model of skill

Skill-space is a **continuum, not a set of objects.** A skill does not exist
until some interval of that continuum is cut out, contained, and named; outside
the cut there is no object there. The continuum's identity element — the
formless whole with no input and no output form — is the limit toward which
decomposition runs; every named skill is a *band* cut from it at a chosen scale.

There are exactly two primitives: **the whole, and the cut.** Everything else is
derived. The familiar systems that look like catalogs of atomic units — the
chromatic scale, the colour spectrum, the periodic table — are the same
structure: a continuum plus a culturally-fixed cut at a tractable scale, none of
them carving joints that exist independently of the cut.

Two consequences follow, and they are the spine of the rest of this note:

- Granularity is **arbitrary in theory.** "One skill" has no natural boundary; a
  skill can always be decomposed into finer skills or composed into a coarser
  one, with no level privileged by the structure itself.
- Granularity is **pinned in practice** — but only at the layer where an
  external boundary reaches in. That boundary is the next section.

## The single anchor

The **typed artifact crossing is the only objective boundary in the system.** A
protocol earns its existence from a typed crossing: it *requires* one validated
artifact and *produces* another. The artifact-type graph is the domain's real
commitment about what discrete forms the work passes through — change it and you
change what runa validates and sequences. Everything determinate in the system
traces back to this single source.

It casts determinacy into two layers:

- **Directly, into the form layer** — the schemas are the typed crossings made
  explicit.
- **Indirectly, into the skill layer** — through the one-skill-per-protocol
  convention (below), the crossings pin the boundaries of the *wrapped* skills,
  one per protocol.

So the architecture is **determinate where it is enforced, free where it is
not.** The typed seams need hard boundaries so artifacts validate and sequence;
the cognitive interior is free continuum, cut wherever serves clarity. This is
the right shape, not a compromise.

One corollary the audit must respect: the **unwrapped cognitive substrate** —
`reckon`, `orient`, `research`, and whatever they further decompose into — is
pinned by *nothing*. No protocol wraps it; no crossing reaches it. It therefore
has **no objective boundary, permanently** — "how many substrate skills are
there, and where does `reckon` end" has no found answer, ever. The substrate is
cut by **authoring fiat at a tractable scale, held provisionally, and marked as
authored**, so a later reader never mistakes a chosen cut for a discovered one.
Wrapped skills are placed objectively (follow the graph); substrate skills are
placed by judgment.

## Two typing axes

Every asset has a coordinate on two orthogonal axes.

**Axis 1 — domain coupling.** Neutral ↔ domain-specific. The membership test:
*an asset is core iff it is reusable by a methodology in another domain.* Run
each asset through the projection to gazette. `reckon`, `orient`, `research`
survive; the `define → land` pipeline, the software schemas, the forge mechanics
do not.

**Axis 2 — form.** How the asset is consumed: **skill** (advisory cognition,
composable, guidance-readable, runtime-optional) | **protocol** (a typed
enforcement shell) | **mechanic** (a concrete external operation) | **schema**
(the artifact form). Orthogonal to domain.

The axes are independent and must stay so. **A skill is not always a
universal** — `code-review` is a skill that is domain-specific. The model is not
"skills are universals, protocols are domains"; it is universals *and* domain
skills both present, with all *migratable* domain-specificity pushed out of the
cognition into the wrapper, the schema, and the mechanic, and whatever remains
genuinely domain-bound in a skill marked as such (next sections).

## The protocol/skill convention

A **protocol wraps exactly one skill.** This is a convention we impose, not a
law discovered — since "one skill" is arbitrary in a divisible continuum, fixing
it at one-per-protocol is the engineering choice that makes the layer
tractable, the same kind of self-imposed bound as one work-unit per pipeline
run.

The division of labour at the wrap:

- The **protocol owns the typed interface** — it enforces the input and output
  artifact types, the crossing runa validates and sequences.
- The **skill carries the cognitive how-to** — the step-by-step reasoning, the
  instructions, the discipline.

**Cognition composes freely inside skill-space; the enforcement layer stays
flat.** A wrapped skill may invoke sub-skills and draw on the unwrapped
substrate without limit — that composition crosses no typed seam, so it is free.
The wrapper does not compose: one protocol, one wrapped skill, however deep that
skill's interior goes. The flat enforcement layer pins the *top* skill
granularity; composition lives below it. A skill may be wrapped by **zero**
protocols — that is the substrate, the ingredients other skills compose.

The factoring direction this sets: **factor the cognitive how-to out of the
protocol bodies fully.** Each protocol shell becomes a thin typed wrapper that
invokes a skill; the reasoning lives in the skill, reusable. Full extraction is
the only clean engineering result, and the cost — a real rewrite — is the price
of the iterative methodology, paid once.

## The projection relation

Domain skills are not independent of their universals; they are **projections**
of them. The convention that carries this:

- A **domain-scope tag** on every skill: `universal` or `domain:<x>`.
- A **`projects-from`** edge from a domain skill to its universal parent. This is
  not a new relation type — it is an ordinary skill invocation that *declares*
  "this is my universal parent, and I add only my domain delta." (A projection
  is to invocation as a prime is to a number: it has every property of the
  general thing, plus a marked one that makes it useful.)

The rule that gives this teeth — and keeps a single home — is structural: **a
projection may extend its universal but never override it.** The universal
quality-review discipline (the gratitude test of
[Transmission](https://github.com/pentaxis93/principles/blob/main/principles/transmission.md),
the pride-in-work invariant) lives **once**; `code-review` and gazette's
`factcheck` are thin projections that add only their domain delta and inherit
the rest. The skill graph ends up mirroring the principle graph — the same
universal→domain projection relation, one level down.

## The recurring boundary

The universal↔domain line **is a Sovereignty WHAT/HOW boundary**: the universal
is the WHAT (the cognition that must happen), the domain projection is the HOW
(the typed, domain-specific form it takes here). Engineering the skill/protocol
seam to coincide with that line makes one boundary do triple duty — skill is the
universal WHAT, protocol is the domain HOW, the typed crossing is the seam where
only what must cross is named. This is the
[Contract-First](https://github.com/pentaxis93/principles/blob/main/compositions/contract-first.md)
transform boundary: the protocol re-represents one universal discipline in a
domain's typed basis, the way a transform carries the same content into a
different basis.

The same cut recurs at several scales — protocol↔skill, universal↔projection,
and contract↔review-skill across the whole pipeline (the multidimensional
contract is the standing WHAT the pipeline's HOW answers to, declared at `define`
and binding every judgment station). One boundary, many scales.

## Phase is sequence, not a type

The lifecycle phases — planning, implementation, review, governance — are **not
a third typing axis.** They cut across the domain axis (each phase has a core
discipline and a domain projection), and after the form/domain split there is no
per-run core asset left for "phase" to name. What remains of phase is **order** —
each stage's output is the next stage's required input — and that ordering is
already enforced by runa from the manifest's requires/produces graph and
concretely set by each domain's manifest. The only universal at the phase level
is a *methodology-authoring* discipline (how to shape any pipeline's stage
ordering), kin to `work-unit-craft` — meta, not per-run.

**ADR spine: two typing axes over the assets, with ordering delegated to runa +
the manifest.**

## Harmonics and the Mendeleev program

The recurrence structure of a self-similar continuum gives the skill graph a
second thing to look for, and a tool.

**Harmonics are a relation, not new objects.** A harmonic between two skills is
the *same sub-move appearing at the same relative position across different
parents* — an
[isomorphism](https://github.com/pentaxis93/principles/blob/main/ONTOLOGY.md#relationship-taxonomy)
edge (with kin for family resemblance). A *lower* harmonic is a finer sub-skill a
skill decomposes into; a *higher* harmonic is a coarser skill it participates in;
a *lateral* harmonic is the recurrence across siblings. The recurring lateral
harmonics are the **highest-value extractions** — a sub-skill shared by the most
parents is the one a single home most demands.

**Simplicity is precision.** A skill cut to fewer, cleaner moves does one thing
exactly; an over-worked skill carries *accidental harmonics* — extra sub-moves
that disperse it off its fundamental. This is the craftsmanship measuring-stick,
and it reads with two graduations: a **wrapped** skill is graded against *one
band / extends-without-override / domain-migrated-out*; a **substrate** skill is
graded against *tractable scale*. The witness marks in existing skills are where
one graduation was applied with the other's rule.

**The Mendeleev method.** In a well-formed periodic table, an element's
properties follow from its *position*, and the gaps predict undiscovered
elements and their properties from position alone ("the essence of an element is
its atomic number" — its essence is its place in the ordering, not an intrinsic
substance). Projected onto skills: a well-formed skill table places each skill
by position, has its properties follow from position, and **predicts
un-extracted skills, with their properties, from the shape of the holes.** This
turns the audit from classification into prediction.

## Distilled tables, and one open question

External systems that look like atomic catalogs — the chemical periodic table,
the chromatic scale, and the contemplative distillations (the Enneagram, the
Vedic houses, E. J. Gold's *periodic table of angels*) — are best read as **prior
traditions' distillations of useful primitives.** They are first-class *input*,
not answer keys, and not a structure to derive against in isolation.

The discipline for using them is exact, and it is the load-bearing caution:

- Because the continuum has no natural joints, there is **no true decomposition
  for a correspondence to be evidence *for*.** The goal is not the *true* cut but
  the *most useful* one — so provenance (whether a tradition derived, extrapolated
  to, or shares a common source with another) does not matter; what is held is a
  track-record-validated decomposition.
- Test any correspondence at the **structural** level — a recurring behavioral
  invariant carried by each pairing — never at the **formal** level — a shared
  slot in a grid whose row/column structure was fixed first and the contents
  fitted to it. A correspondence that is exact *by construction* carries no
  evidential weight; an independent convergence carries the most.

**The open question, recorded unresolved.** Gold's periodic table of angels
maps angels onto the chemical table's exact parameters — seven periods of
2/8/18/32, noble ranks on the right. Those numbers are real, not arbitrary: in
chemistry they are 2n², the eigenspectrum of the atom (a three-dimensional
central potential / spherical harmonics). One reading is that this is a *formal*
borrow, and that skill-space has its **own** spectrum set by its own boundary
condition — the typed artifact crossing — the way a vibrating string and a
drumhead are both fully harmonic yet share none of the same overtone numbers
because their geometries differ. The other reading, held open, is that the
specific numbers are themselves universal — derivations of a single harmonic (or
prime-structured) source underlying every level — in which case the
correspondence is exact in fact. **This note does not resolve which.** It is not
settleable by argument; it is settleable by construction.

## The audit: the convergence experiment, and the next move

The per-asset audit is, in one pass, three things: the core/delivery
**assignment**, the **grounding** the seam ADR rests on, and the **experiment** that
tests the correspondence above. It:

1. reads every skill and protocol body at current head;
2. places each asset on (domain × form);
3. tests whether each protocol reduces to **one universal skill + a domain
   wrapper** (the open "would it hold for 100% of cases" question);
4. draws the universal/projection seams (extend-not-override), tagging domain
   scope;
5. finds the recurring atomic beads — the lateral harmonics, the highest-value
   extractions;
6. applies the Mendeleev lens — position determines properties, and the gaps
   predict un-extracted skills;
7. lays the crossing-induced cuts against the distilled tables, tested
   **structurally, not formally.**

If the granularity the artifact-crossings induce **rhymes** with the distilled
primitives, the convergence is itself the validation — two independent
boundary-value problems landing on one spectrum, which is what a shared source
would produce — and the map is adopted with no independence hangup. If they
**diverge**, skill-space's geometry differs at the anchor and we cut for our own
purpose; the distilled table is not thereby false, only a different instrument.
Either way, **construction decides, not fiat.**

The result is the first two rows of a periodic table of skills for the Tesserine
methodologies — derived, provisional, and fine-tuned as further domains are
added.
