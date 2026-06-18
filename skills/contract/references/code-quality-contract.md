# Code-Quality Contract

The code-quality dimension of the contract. The behavioral dimension
declares what the system does; the documentation dimension declares what the
recipient can do; this declares what must hold of the change's **internal
form**.

Its teeth come from the resolved **principles corpus**, not from an invented
style rulebook: the universals that bear on a change, consulted from the
corpus and projected onto the diff as reviewer-checkable items.

## Why the corpus, not a rulebook

A separate code-quality rulebook would be a second home for invariants the
corpus already owns — and a second home drifts from the first. So this
dimension consults the corpus rather than restating it (consult, don't
model). The corpus owns each universal's content; this module owns only how
a universal lands on a diff and how the projection is generated. When the
two would disagree, the corpus is authoritative and the projection is what
changes.

## The recursive property

Projecting the corpus is what makes the contract synergistic and recursive.
Because the same universals that govern the whole system decide each change,
landing a unit does double work under **Recursive Improvement**: it improves
the object (this diff) and tightens the corpus's grip on the codebase (every
landed change is one more place a universal is enforced). The spiral runs on
the corpus as its bounded asset — a projection that keeps misfiring, or a
change that stresses a universal not yet projected, is friction that becomes
corpus change material. Sharpen a universal and every future contract's
code-quality dimension sharpens with it.

## The teeth of a code-quality contract

An item has teeth only if **a careless change fails it, checkably against
the diff.** "The code is clean" passes anything; a projected universal does
not. The review of each item finds one of two things: the **locus** in the
diff where the universal holds, or the **place** it fails. A finding is
evidence; "looks fine" is not (**Verifiable Completion**, **Honest
Signal**).

## Projecting the corpus

The projection is generated, not hardcoded. When the contract is authored,
consult the resolved corpus (`~/.groundwork/principles/`), select the
universals this change most stresses, and write each as a checklist item in
one shape:

- the universal as a **question** asked of the diff,
- the **failing tell** a careless change leaves, and
- the condition under which it **holds** — a locus a reviewer can point at.

Selecting from the resolved corpus, rather than a list frozen here, is what
keeps the dimension honest as the corpus evolves and across deployments that
resolve a different corpus. The items below illustrate the shape; they are
not the set — the set is whatever the resolved corpus and the change at hand
demand.

- *Question:* does every element added or kept trace to a verified need?
  *Failing tell:* a defensive abstraction, a speculative parameter, a
  compatibility shim, a "might need." *Holds when:* the constraint each new
  element serves can be named, or the element is gone.
- *Question:* does each shared fact or behavior the change touches derive
  from, or consult, one authoritative home? *Failing tell:* a hand-synced
  second copy, a guard that re-derives what an authority already declares, a
  doc paraphrasing a schema. *Holds when:* the one home and the mechanical
  derivation are identifiable.
- *Question:* do the change's durable claims — names, comments, tests —
  state what is, in the positive present? *Failing tell:* a comment
  narrating history, a test asserting an absence. *Holds when:* the claim is
  checkable against the present substrate alone.
- *Question:* does every surface the change adds or moves tell the truth
  about what it is, does, and supports? *Failing tell:* a name borrowing
  prestige, a fallback masking failure, silent acceptance of an unsupported
  condition. *Holds when:* wrong assumptions fail loudly where they arise.

## Declaring the contract

At `take`, the contract declares the universals this change most stresses —
the subset it puts under real pressure, named from the resolved corpus, not
a ritual recital. A subset is legitimate; under-declaration is not. A change
that touches a shared asset without declaring the universal that governs
single homes, adds an abstraction without the one that governs earning a
place, or moves a public surface without the one that governs honest
surfaces, has declared around its own risk.

## Verifying the contract

At `verify`, the reviewer audits the diff against each declared item and
records, per item, the locus where it holds or the finding where it fails.
The method is `protocols/verify/references/code-quality-review.md`. The
review is the gate; a self-report of cleanliness is not the evidence.

## How the projection grows

The shape above is a way to write items, not a closed set. As the resolved
corpus grows, or as a change stresses a universal the last projection did
not name, project it the same way and consult its corpus document for the
content. The corpus is the authority; the projection is its working face
onto a diff, regenerated per change.

## Cross-references

- principles corpus (`~/.groundwork/principles/`) — the home this dimension
  consults and projects; each universal's full content lives there.
- `protocols/verify/references/code-quality-review.md` — the audit that
  verifies this contract.
- [../SKILL.md](../SKILL.md) — the contract skill and the teeth principle
  this projection instantiates.
