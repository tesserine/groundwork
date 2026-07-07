# Principle-Derived Contracts

Principle-derived contracts are the contract discipline for open-ended
methodology, design, and re-derivation units. They still produce ordinary
`contract.criteria[]` entries. The difference is how the criteria are
authored: the author derives the quality bar from the work-unit ground and
the governing principles instead of enumerating a checklist that already
chooses the mechanism.

This reference is part of the [contract skill](../SKILL.md). It extends the
same teeth principle, dimensions, and evidence lifecycle; it does not create
a second rulebook.

## Trigger and Boundary

Use this pattern when the deliverable's shape is itself under discovery:
a methodology rule, a design, a re-derivation, an architecture judgment, or
another artifact whose correct form must emerge from ground and principles.
The routing question is: **must the work decide the form of the answer, or
do the acceptance criteria already name observable behavior that can be
refined directly?**

If the criteria already name well-scoped behavior, use the ordinary
contract authoring path. A principle-derived contract adds no value to a
normal feature, bug, or narrow documentation update whose outcome is already
concrete.

Derivation never relaxes teeth. A derived criterion is valid only when it
names the hollow delivery it catches and the act that will fail that
delivery. "Consult the principles" is not a criterion; it becomes one only
when a reviewer can perform the consultation and point to the locus where
the delivery holds or fails.

## Derivation Method

1. Ground the need from the work-unit body, including acceptance criteria,
   desired outcome, non-goals, and explicit contract inputs.
2. Select and read the governing principles at the resolved principles
   corpus, such as `~/.groundwork/principles/` in an installed environment.
3. For each contract dimension the work has, derive what must be true of
   any acceptable answer. Keep the mechanism open and close the quality
   bar.
4. Author each criterion in the existing schema: `statement` names the
   required product state, `hollow_delivery` names the plausible lazy
   delivery, `check_kind` selects executable or attested evidence,
   `check` names the performed act, and `acceptance_criterion` carries the
   criterion's work-unit source.
5. Run the completeness pass: no criterion may prescribe the mechanism, no
   criterion may be unfailable, every numbered acceptance criterion or
   explicit body-ground obligation under pressure is mapped, and every
   present dimension has a teeth-bearing criterion.

The principles corpus owns the universals. This reference names the
principles that bear on a derivation by their corpus names and consults
them; it does not restate their content as local doctrine.

## Mechanism-Open, Quality-Closed

A principle-derived criterion leaves mechanism conclusions open: transport,
structure, names, artifact form, station shape, and implementation route
remain the implementer's work unless the work-unit itself makes one of
them part of the required outcome.

The quality space is closed. Every delivered choice must be grounded in the
current substrate, traceable to the work-unit or body ground, single-homed
where it creates or moves authority, checked against the governing
principles, and evidenced through the contract's existing performed result
surface.

Two failure directions matter:

- **Mechanism-smuggling checklist.** The criterion names the answer the
  derivation must produce. Repair it by naming the quality the answer must
  satisfy and leaving the form to the derivation.
- **Unfailable derivation.** The criterion invokes principles but names no
  failing delivery. Repair it by naming the plausible hollow and the
  reviewer act that catches it.

## Operational Hollows

Hollow deliveries are not only explicit prose claims. In an open-ended
unit, a stale or wrong premise can survive as a load-bearing rule, handoff,
artifact requirement, constraint, or ownership assignment even when no
sentence states the stale premise.

Author operational-hollow checks by inventorying the delivery's
load-bearing elements:

1. Enumerate rules, handoffs, artifact requirements, constraints, and
   ownership assignments added or preserved by the delivery.
2. For each element, name the premise or constraint it rests on.
3. Verify that premise against current ground and the governing principles.
4. Fail any element whose only support is stale ground, inherited
   mechanism, or local convenience.

The `hollow_delivery` field should name the operational form when that is
the real risk: "a required handoff remains even though no current constraint
needs it" is sharper than "the rationale is stale."

## Source Mapping

Every criterion maps to a source on the existing `acceptance_criterion`
field in `contract.criteria[]`. The field names either a numbered
acceptance criterion or an explicit body-ground source. A criterion with no
auditable source is floating and should be rejected during authoring or
review.

| Source | Form in `acceptance_criterion` | Review result |
| --- | --- | --- |
| Numbered acceptance criterion | `AC2 — Mechanism-open, quality-closed criteria are taught` | The criterion refines the numbered acceptance criterion. |
| Body-ground source | `Body ground (Desired outcome: future agents can author this kind of contract)` | The criterion carries an explicit work-unit body obligation that a numbered AC did not fully express. |
| Floating criterion | `Quality should be excellent` | Reject it; the source is not auditable. |

Body-ground mapping is not scope expansion. It is the auditable form for
obligations already present in the work-unit body, such as desired outcome,
contract inputs, non-goals, or grounding notes.

## Attested Checks With Teeth

An attested check has teeth when it names all three parts:

- the act the reviewer performs, such as enumerate, walk, classify,
  consult, or map;
- the loci the act examines; and
- the finding that would fail the criterion.

Weak attestation asks only for assent: "reviewer confirms the contract is
good." Teeth-bearing attestation is performable: "reviewer inventories each
load-bearing handoff in the reference, maps each to current ground, and
records any handoff whose premise is unsupported."

Useful shapes include inventory-and-map checks, cold-reader walkthroughs,
authority consultation, model-coherence review, and reviewer findings with
substantive loci. For prose and text-artifact gates, consult
[verification-craft](../../verification-craft/SKILL.md) and choose the
smallest gate whose red state is the invariant being false.

## Evolvability Outcome

Durable methodology assets may carry an evolvability documentation outcome:
future friction has a named change-vector home and a bounded asset surface
to reshape. This is an outcome only when a future maintainer can act from
it.

The check has three facts:

- the change-vector home is named and live, such as a tracker issue against
  the contract skill;
- the asset boundary is identifiable, such as this reference plus the
  routing section in `../SKILL.md`; and
- a hypothetical friction item filed today would land at that home and
  reach that boundary.

A bare feedback link fails. It tells the reader where to complain, not what
surface changes when the method needs to evolve.

This reference satisfies the outcome it teaches: file future friction as a
`documentation`-labeled issue in `tesserine/groundwork` whose title names
principle-derived contract guidance and whose body references both
`skills/contract/SKILL.md` and
`skills/contract/references/principle-derived-contracts.md`. The bounded asset
surface is this reference plus the `Principle-Derived Contracts` routing
section in the contract skill.

## Worked Example

Suppose a work-unit asks for a workflow handoff to be re-derived because the
current handoff may encode a stale runtime assumption. The contract must not
decide the new handoff, the artifact shape, or the station name. It must
decide what any acceptable result proves.

Defect pair:

- Mechanism-smuggling criterion: "The workflow introduces a new
  `handoff-summary` artifact." Repair: "Every retained or introduced
  handoff is grounded in a current recipient need and has one owning home."
- Unfailable criterion: "The workflow follows the selected governing
  principles."
  Repair: "Reviewer inventories each handoff and authority claim, maps each
  to its current source, and records any unsupported or second-home claim as
  a failure."

Schema-valid example:

```json
{
  "work_unit": "workflow-handoff-rederive",
  "title": "Re-derived workflow handoff contract",
  "criteria": [
    {
      "id": "behavior-routing-decidable",
      "dimension": "behavior",
      "acceptance_criterion": "AC1 — Trigger and boundary are named",
      "statement": "A cold author can decide whether the handoff unit needs a principle-derived contract or ordinary behavior refinement.",
      "hollow_delivery": "The guidance sends every workflow update through derivation, including narrow behavior fixes that already have concrete outcomes.",
      "check_kind": "attested",
      "check": "Reviewer walks one open-ended handoff re-derivation and one well-scoped behavior fix through the routing question and records the deciding source sentence for each."
    },
    {
      "id": "documentation-future-friction-routable",
      "dimension": "documentation",
      "acceptance_criterion": "Body ground (Desired outcome: future friction has a concrete change-vector home)",
      "statement": "A maintainer who finds later handoff friction can name the live home for changing the guidance and the bounded asset surface to inspect.",
      "hollow_delivery": "The document gives a generic feedback link but no asset boundary or home that owns the method.",
      "check_kind": "attested",
      "check": "Reviewer files a hypothetical friction note on paper, names the target work-unit home and asset boundary from the delivered text, and records any missing route as the failing finding."
    },
    {
      "id": "code-quality-authority-single-homed",
      "dimension": "code-quality",
      "acceptance_criterion": "AC8 — Existing contract discipline remains single-homed and coherent",
      "statement": "New handoff-contract guidance lives in one contract reference and every principle or verification fact is consulted at its owning home.",
      "hollow_delivery": "The change duplicates principle definitions or verification-craft gate rules locally, creating a second editable authority.",
      "check_kind": "attested",
      "check": "Reviewer inventories each principle and verification-craft claim in the diff, maps it to consultation or local restatement, and fails any editable second home."
    }
  ]
}
```

Live exemplars: [pentaxis93/with-claude#158](https://github.com/pentaxis93/with-claude/issues/158)
and [groundwork#539's deliverable of record](https://github.com/tesserine/groundwork/issues/539#issuecomment-4903293985)
show this pattern in use. Consult them as examples of the pattern, not as
sources of universal workflow policy.

## Corruption Modes

**Mechanism smuggling.** The contract pre-decides transport, structure,
names, or artifact form without the work-unit making that mechanism part of
the required outcome.

**Principle haze.** Criteria invoke the principles but name no hollow
delivery and no act that could fail a plausible delivery.

**Operational blindness.** Review checks only explanatory prose while stale
premises remain encoded in rules, handoffs, artifact requirements,
constraints, or ownership assignments.

**Floating source.** A criterion has no numbered acceptance criterion or
explicit body-ground source in `acceptance_criterion`.

**Second rulebook.** The pattern restates the principles corpus, the
contract lifecycle, or verification-craft gate forms instead of consulting
their homes.

## Cross-References

- [../SKILL.md](../SKILL.md) — the contract skill, teeth principle,
  dimensions, and lifecycle this pattern extends.
- [code-quality-contract.md](code-quality-contract.md) — corpus projection
  for the code-quality dimension.
- [documentation-contract.md](documentation-contract.md) — recipient outcome
  form for documentation criteria.
- [../../verification-craft/SKILL.md](../../verification-craft/SKILL.md) —
  verification gates over prose and other text artifacts.
