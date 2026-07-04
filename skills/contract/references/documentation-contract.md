# Documentation Contract

The documentation dimension of the uniform contract machine declares what
each **recipient** can do once the work lands. It serves **Transmission**:
work completes when the recipient can act on it, not when the maker
finishes — so the contract is written as outcomes the recipient reaches,
and is satisfied only when they can reach them.

This reference owns the documentation dimension's authoring discipline, not
a separate contract structure. It consults `orient`'s audience taxonomy and
emits typed documentation criteria into `contract.criteria[]`; the usual
checking apparatus is `check_kind: "attested"` with performed evidence
recorded as a reviewer finding in `completion-evidence.results[]`.

## The teeth of a documentation contract

An item has teeth only if **a delivery with no docs, or hollow docs, fails
it.** The tell is the grammar: phrase every item as an **audience
outcome** — what the reader can now do — never as artifact existence.

- Hollow: "the README is updated," "a CHANGELOG entry exists," "an ADR was
  written." A delivery that touches the file but lands nothing passes these.
- Teeth: "a new user completes the primary task from the README alone," "a
  consumer understands what changed from the CHANGELOG entry without the
  diff," "the next maintainer finds the decision at the point they meet it."
  A hollow doc fails these.

The check, run when documentation inputs are shaped, when validation is
defined, and again when it is performed: *could a delivery that wrote
nothing useful for this recipient still pass this criterion?* If yes,
rewrite it as the recipient's outcome and keep the hollow delivery visible
on the criterion.

## Lifecycle

`work-unit-craft`/`decompose` supplies recipient outcomes as inputs to
validation. `define` turns those inputs into validation defined: typed
criteria in the uniform contract surface naming the pillar, recipient
outcome, hollow delivery, `check_kind`, and check descriptor. `verify`
performs validation by auditing whether those recipients can reach the
outcomes and recording the finding in the uniform evidence surface. A
subset is legitimate — a refactor with no user-visible effect carries no
user pillar; a first public release carries all three. What is illegitimate
is silence where the change clearly serves a recipient: a new user-facing
capability with no user pillar is an under-declared contract, not a small
one. Mechanically, the pillar outcomes selected for a change enter the
warranted acceptance-criteria set the shared contract/evidence detector
checks — the same under-declaration flag every dimension answers to. The
exemplar fixtures under `tests/fixtures/artifacts/` model both sides: the
rich pillar pair that passes that gate, and the hollow generic form it
catches (`tests/test_documentation_dimension.py` pins the pair).

The audience taxonomy, artifact types, and writing stance are **not**
restated here — they live in the `orient` skill's documentation discipline
(`skills/orient/references/documentation.md`), which this contract consults.
This module defines the outcome form; orient says who the readers are and
how to write for them.

## The three sub-modules

One per recipient. Each names the recipient, the outcome they must reach,
and example checklist items already in teeth-bearing form.

### User documentation

**Recipient:** someone using the system, assuming no knowledge of its
internals.

**Outcome:** they install, configure, accomplish the primary task, and
recover from the common failure — without reading source.

Checklist:

- A new user installs and reaches first success from the README alone,
  without reading source.
- The primary task has a worked example the user can follow end to end.
- The common failure names its cause and the recovery step, not only the
  error text.
- Every user-visible change in this work lands a CHANGELOG entry a consumer
  understands without the diff.
- Each public input and output the user touches (a CLI flag, a called API)
  is documented where the user meets it.

### Developer documentation

**Recipient:** someone changing or building on the system — a contributor,
an integrator, an AI agent landing cold.

**Outcome:** they locate where the change lives, understand the boundaries
it moves, and integrate against it — without reverse-engineering the code.

Checklist:

- A contributor locates where this change lives and what it touches from the
  architecture docs, not by full-text search.
- A non-obvious decision in the change is captured where the next maintainer
  meets it — inline at the decision point, or an ADR when the decision is
  significant or hard to reverse.
- An integrator calling this surface has its contract — signatures, types,
  errors, behavior — documented alongside the code.
- An AI agent landing cold has the explicit paths and constraint-first
  orientation it needs, assuming no session memory.

### Discovery & marketing communication

**Recipient:** someone who does not yet know the project exists.

**Outcome:** from the entry surface, within a few sentences, they can tell
what it is, who it is for, and why they would choose it over the status quo.

Checklist:

- The entry surface — the README lead, the project synopsis — states in its
  first few sentences what the project is and the problem it solves.
- A reader who does not know the project can tell within that span whether
  it is for them: the audience and the use case are named, not implied.
- The distinct reason to choose it — what it does that the alternatives or
  doing nothing do not — is stated, and stated honestly: no borrowed
  prestige, no capability claimed that the system does not have
  (**Honest Signal** governs this pillar most sharply).
- When the work changes positioning — a capability that changes who the
  project is for — the entry surface is updated in the same change.

## Verifying the contract

At `verify`, the documentation review audits the change against the defined
contract: for each selected pillar, it confirms the recipient can now reach
the defined outcome, and it keeps existing docs honest against drift. The
method is `protocols/verify/references/documentation-review.md`; the
criterion result is recorded in `completion-evidence.results[]` with an
attestation carrying reviewer identity and finding. The legacy
`documentation` summary in completion evidence remains the document-impact
index, not the evidence home for a declared documentation criterion.
Verification is evidence, not assertion: the audit finds, per criterion,
the place the outcome holds or the place it fails.

## Single home

Three layers, one home each, none restating another:

- **Taxonomy and stance** — `orient`'s documentation discipline: who the
  readers are, what artifacts serve them, how to write at the right depth.
- **Inputs and definition** — this module: the per-recipient outcomes a
  given change must reach.
- **Audit** — `verify`'s documentation review: the change checked against
  the defined outcomes, recorded in `completion-evidence`.

## Cross-references

- `skills/orient/references/documentation.md` — the audience taxonomy and
  writing stance this contract consults (includes the discovery reader
  profile).
- `protocols/verify/references/documentation-review.md` — the audit that
  verifies this contract.
- Transmission, Honest Signal — the principles-corpus universals this
  dimension serves (`~/.groundwork/principles/`).
- [../SKILL.md](../SKILL.md) — the contract skill and the teeth principle
  this checklist instantiates.
