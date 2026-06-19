---
name: contract
description: >-
  The contract discipline: a contract is the executable definition of done
  across every dimension a change must satisfy — behavior, documentation,
  and code quality — considered as inputs, defined as validation, performed
  as evidence, and carried unbroken through implementation, verification,
  and closure. Use when authoring or reviewing a contract, refining
  acceptance criteria into Given/When/Then scenarios, declaring a change's
  documentation or code-quality obligations, and whenever code, tests, docs,
  or completion claims must stay traceable to a declared contract instead of
  drifting toward implementation convenience.
metadata:
  version: "2.3.0"
  updated: "2026-06-19"
---

# Contract

A contract is the executable definition of done. It is **Contract-First**
given concrete form — declare the seam, build to it, verify against it,
keep the declaration the single home of the seam's truth — applied not to
one aspect of a change but to every aspect that must hold when the work
lands. A contract has dimensions; each declares what done means for one
aspect, in the form that gives that aspect teeth.

This skill is the home of the contract across its dimensions. It declares
the lifecycle that turns issue-shaped inputs into validation, evidence, and
landing record; per-stage protocols point here for their role and do not
duplicate this lifecycle. The contract remains the source of truth through
every later stage: plans link decisions to it, the build is shaped to it,
verification is decided against it, and landing records what shipped.

## The teeth principle

A contract dimension is real only when **a hollow delivery fails at least
one of its criteria.** This is **Verifiable Completion** (the principles
corpus universal) at the level of the contract: completion is an observable
state, evidence decides the claim, and a criterion a no-op satisfies
decides nothing. Of every criterion, in every dimension, ask: *could a
stub — a canned return, an absent doc, a rename that changes nothing — pass
this?* If yes, it is hollow; sharpen it until a hollow delivery fails.

The teeth principle is universal; the **form** of the check fits the
dimension. Behavior earns teeth through executable scenarios a stub fails.
Documentation earns them through a checklist of audience outcomes a
doc-less delivery fails. Code quality earns them through corpus principles
projected onto the change, each a locus a careless change fails. Forcing
one form — a test — onto every dimension is the mistake; the constant is
the failing-hollow-delivery test, not the apparatus that runs it.

## The dimensions

A contract declares the dimensions the work demands — behavior is always
present; documentation and code quality are declared as the change
warrants, and a subset is legitimate the way a behavior contract need not
exercise every code path. The lifecycle is inputs to validation ->
validation defined -> validation performed, carried through `implement` and
recorded at `land`.

| Dimension | Lifecycle |
|---|---|
| **Behavior** | Work-unit acceptance criteria are inputs to validation; `take` turns them into validation defined as executable scenarios or documentation-deliverable gates; `verify` reports validation performed as scenario or gate coverage; the result is carried through `implement` and recorded at `land`. |
| **Documentation** | Issue-craft recipient outcomes are inputs to validation; `take` turns them into validation defined as documentation outcomes; `verify` reports validation performed as an audience-outcome review; the result is carried through `implement` and recorded at `land`. |
| **Code quality** | Issue-craft corpus pointers and stressed universals are inputs to validation; `take` turns them into validation defined as reviewer-checkable projections; `verify` reports validation performed as diff loci or findings; the result is carried through `implement` and recorded at `land`. |

### Stage Handoffs

The stage boundary is part of the contract, not local protocol folklore:

- issue-craft produces inputs to validation: the work-unit criteria,
  recipient outcomes, and corpus pointers that describe what each dimension
  must consider.
- `take` consumes inputs to validation and produces validation defined: the
  behavior contract plus declared documentation and code-quality outcomes.
- `implement` consumes validation defined and keeps the change traced to it:
  tests, docs, and code-quality decisions name the scenario or dimension
  they advance.
- `verify` consumes validation defined and produces validation performed:
  scenario results, documentation review, and code-quality findings.
- `land` consumes validation performed and records what shipped, including
  explicit gaps if any remain.

### Pointer-as-default

Issue-craft must consider every dimension, but consideration is not a
mandatory per-dimension declaration. A dimension carrying no special input
is still validated: its general contract remains the validation pointer.
The rule is: density across dimensions is unequal; consideration is equal. A
refactor may need detailed code-quality inputs and only the general
documentation contract; a user-facing capability may need dense user
documentation inputs and ordinary code-quality projection. Silence is valid
only after the dimension was considered and the general contract is enough.

- **[Behavioral dimension](#the-behavioral-dimension)** — what the system
  does. The most developed dimension and the worked exemplar below; its
  form is BDD.
- **[Documentation dimension](references/documentation-contract.md)** —
  what each recipient can do once the work lands. Three sub-modules — user,
  developer, discovery — each a checklist of audience outcomes.
- **[Code-quality dimension](references/code-quality-contract.md)** — what
  must hold of the change's internal form: the relevant principles-corpus
  universals projected onto the diff.

New dimensions join here as they earn their place; satisfying the teeth
principle and the inputs-defined-performed lifecycle is what makes a
dimension one.

## The behavioral dimension

What the system does, specified once and traced everywhere. This is the
contract's most developed dimension and the worked example of a dimension
with teeth — the stub test below is the behavioral instance of the teeth
principle above. Behavior is specified once, then everything traces to it:
plans link decisions to scenarios, tests prove named scenarios,
verification reports scenario-level coverage, landing records what coverage
shipped.

Reference: [Dan North, Introducing BDD](https://dannorth.net/introducing-bdd/).
Language-specific patterns:
[references/language-patterns.md](references/language-patterns.md).

### Authoring the Contract

1. **Start from the criteria.** Each work-unit acceptance criterion is
   refined into one or more scenarios. Every scenario names the criterion it
   refines — no orphan scenarios, no uncovered criteria.
2. **Ask behavior before mechanics.** "What should this do?" precedes "how
   to test it?" The behavior question surfaces the right scenario; the
   mechanics question optimizes the wrong one.
3. **Name scenarios as sentences.** A scenario name is a behavior statement
   readable as specification: `rejects_expired_tokens_with_401`, not
   `test_auth`. If the names alone don't describe what the system does, the
   specification has disappeared and only code remains.
4. **Structure as Given/When/Then.** Given establishes context (setup only),
   When performs one action (the behavior trigger), Then asserts observable
   outcomes — never internal state.
5. **One behavior per scenario.** A scenario proving three things masks
   which one broke. Split it.
6. **Rank by behavior gap.** Happy path first, core before edge, foundation
   before dependents, user-visible before internal.

#### Example

```python
def test_rejects_expired_tokens_with_401():
    """Expired authentication tokens return 401, not a silent fallback."""
    # Given
    token = create_token(expires_at=one_hour_ago)
    client = create_test_client()

    # When
    response = client.get("/api/protected", headers=auth_header(token))

    # Then
    assert response.status_code == 401
    assert "expired" in response.json()["error"].lower()
```

The name is the specification line; the assertions check observable
outcomes. A test asserting `validator._cache` or `result.internal_state`
breaks on refactor and specifies nothing.

### Robustness — the stub test

A well-formed scenario can still specify nothing. "Observable, not internal"
guards one direction — assertions that reach into internals break on refactor
and pin implementation. The opposite failure is as fatal: a Then so shallow a
canned return satisfies it. `create-ticket returns a complete-scoped handle` is
observable, and a connector that builds the handle string while creating no
ticket passes it. The scenario proves the shape of a return, not that the work
happened.

A contract is robust when **every scenario fails on a stub** — a vacuous or
canned implementation must break at least one Then. That single property is
what makes green mean functional; a contract whose scenarios a stub passes is a
definition of done that nothing has to do.

Three shapes of hollow scenario, with the repair:

- **Shape, not effect.** The Then asserts the structure of a return — a
  well-formed handle, a schema-valid payload — which a stub fabricates. Assert
  the effect a stub cannot fake instead: not "create-ticket returns a handle"
  but "the ticket named by the handle reads back"; not "the connector validates
  the operation" but "the operation issues the provider request," checkable
  against a recording transport with no live side effect.
- **No falsifying case.** Every scenario is a positive — "valid input is
  accepted." A validator that accepts everything passes them all, so the
  vacuous validator and the correct one are indistinguishable. Add the negative
  the degenerate implementation fails: "a malformed payload is rejected," "a
  wrong-but-well-formed identity is refused." A schema that quietly stops
  validating — a detached `$ref`, a dropped constraint — is caught only by a
  fixture that must be rejected.
- **Uncovered surface.** One representative operation is proven; the rest are
  asserted only at the shape level, and a delivery stubs the unproven ones and
  ships green. Every operation or capability surface carries its own
  stub-failing scenario — not one exemplar standing in for the set.

#### The completeness check

Before the contract is delivered, and again by whoever reviews it before
acceptance, validate it against itself. Of each scenario ask: *could a stub — a
canned return, a no-op, a validator that always says yes — pass this?* If yes,
it is hollow; strengthen it until a stub fails. The contract is complete when
the answer is no for every scenario and every criterion is covered by at least
one such scenario. The check is cheap, it runs before any code exists, and it
is the line between a contract that defines done and one that describes the
happy shape of done.

Hollow: `create_ticket_returns_complete_handle` — asserts the returned handle is
well-formed; a connector that fabricates the handle and never calls the forge
passes. Robust: `create_ticket_persists_a_retrievable_ticket` — Given a
recording transport (or a real forge on the gated path), When create-ticket
runs, Then the transport received the create request with the mapped fields and
the ticket named by the returned handle reads back. The fabricating stub fails
the first Then; the no-request stub fails the second.

### Documentation-deliverable behavior gates

Some work-units deliver methodology documentation rather than runtime
behavior. Their behavior dimension still needs teeth: validation defined is
the set of structural, coherence, and conformance gates that prove the
documented discipline works as a surface a recipient can use. Structural
gates include reference-link resolution and script-path resolution.
Conformance gates include template-schema conformance where a document
describes a shaped artifact or protocol output. Coherence gates include
internal coherence: the document's lifecycle, names, and handoffs agree
within the skill and with the protocol references it points to.

These gates stand in for runtime scenarios only when the deliverable is
documentation. A hollow documentation change fails at least one gate: broken
links fail structural validation, a template that no longer matches its
schema fails conformance, and a lifecycle that says different things in two
sections fails internal coherence.

### Carrying the Contract

- **Implementation maps to behavior.** Every implementation increment names
  the scenario it advances. Each RED test corresponds to a named scenario.
  Work that cannot be traced to a scenario is unanchored — scope creep or a
  missing specification; resolve which before proceeding.
- **Behavior is the unit of progress.** Execution order follows behavior
  gaps, not code adjacency. Work advances by proving another scenario.
- **Completion is behavior coverage.** "All tests pass" is incomplete unless
  it names which scenarios those tests prove and which criteria those
  scenarios cover. Report coverage, not command output.

#### When an existing test fails after a change

Classify before touching it:

- **Bug introduced** — the behavior is still required; fix the
  implementation.
- **Behavior moved** — the behavior lives elsewhere now; redirect the test.
- **Behavior obsolete** — the system no longer needs it; delete the test
  (and its scenario). Never weaken assertions to make a failure go away.

**Delete freely.** Scenarios and tests for behaviors nobody needs are noise,
not safety.

## The documentation dimension

Documentation earns its place in the contract because **Transmission** is a
principle: work completes when the recipient can act on it, not when the
maker finishes. So the documentation contract declares, per recipient, the
outcome that recipient must reach — and is satisfied only when they can
reach it.

Its teeth are a checklist, not a test, and the teeth principle decides the
checklist's shape: an item has teeth only if a doc-less or hollow-doc
delivery fails it. The tell is phrasing each item as an **audience
outcome** — what the reader can now do — not artifact existence. "A new
user completes the primary task from the README alone" fails a doc-less
delivery; "a README exists" passes anything.

Three sub-modules, one per recipient: **user**, **developer**, and
**discovery & marketing** — the last being the reader who does not yet know
the project exists. The full discipline, with each pillar's checklist and
hollow-item test, is
[references/documentation-contract.md](references/documentation-contract.md).

The dimension keeps a single home at each layer: the audience taxonomy and
writing stance live in the `orient` skill's documentation discipline; this
contract declares the outcomes; the `verify` protocol's documentation
review audits the change against the declared contract and records the
result in `completion-evidence`. The contract declares, orient styles,
verify checks — no layer restates another.

## The code-quality dimension

Behavior says what the system does; documentation says what the recipient
can do; the code-quality dimension declares what must hold of the change's
internal form. Its teeth come not from an invented style rulebook but from
the **principles corpus**: the universals that bear on this change,
projected onto the diff as reviewer-checkable items. The corpus is the one
home of quality invariants; the dimension consults it rather than
re-deriving a second, divergent rulebook that would drift from it (consult,
don't model).

The projection is what makes the contract synergistic and recursive.
Because the same universals that govern the whole system decide each change,
landing a unit does double work: it improves the object and tightens the
corpus's grip on the codebase. That is **Recursive Improvement** operating
on the corpus itself — the system getting better at getting better. Sharpen
a principle and every future contract's code-quality dimension sharpens with
it.

Its teeth: each item is phrased so a careless change fails it, checkable
against the diff — not "the code is clean" (which anything passes) but a
projected universal a reviewer can point at, finding either the locus where
it holds or the place it fails. How the projection is generated from the
resolved corpus, and grows with it, is
[references/code-quality-contract.md](references/code-quality-contract.md).

## Corruption Modes

**Contract dropoff.** The contract is treated as a phase that ended when
coding began. *Recognition:* completion claims say "tests pass" without
citing which behaviors have evidence.

**Testing implementation.** Assertions reference private fields, internals,
or intermediate state. *Recognition:* the test would break on a
behavior-preserving refactor.

**Hollow scenario.** A Then so shallow a stub passes it — the shape of a
return, not the effect. *Recognition:* a canned return or a no-op
implementation would satisfy the assertion; the vacuous and the correct
implementation are indistinguishable under it.

**Vague names.** Test names are labels, not behavior statements.
*Recognition:* you cannot reconstruct what the module does from names alone.

**Multi-behavior scenarios.** One scenario, several When/Then sequences.
*Recognition:* a failure could mean any of several behaviors broke.

**Test hoarding.** Tests kept for behaviors the system no longer needs.
*Recognition:* fear of deleting because "they might catch something."

**Framework overthinking.** Evaluating test frameworks instead of writing
behaviors. *Recognition:* runners configured, assertion libraries compared,
no behavior specified yet.

The modes above name the behavioral dimension's failures; two corruptions
threaten any dimension:

**Hollow dimension.** A dimension whose criteria a hollow delivery passes —
a checklist of artifact-existence items, a code-quality line that says
"clean," a scenario a stub satisfies. *Recognition:* you cannot name the
hollow delivery that would fail it.

**Modeled, not consulted.** A dimension that re-derives its authority
instead of consulting it — a code-quality rulebook paraphrasing the corpus,
a documentation checklist re-listing the audience taxonomy `orient` already
owns. *Recognition:* two homes for one truth, kept in agreement by hand.

## Principles

- **Words shape thinking.** "Given," "when," "then," "should" force thought
  about what the system does rather than how it is built. The language is
  the method.
- **Specification, not verification.** The contract's primary value is
  stating what the system does; catching regressions is the byproduct.
- **Teeth before form.** The constant across dimensions is that a hollow
  delivery fails a criterion; the form of the check is chosen to fit the
  aspect, never the aspect bent to fit one form.
- **Each dimension consults its single home.** Behavior traces to
  scenarios, documentation to `orient`'s audience taxonomy, code quality to
  the principles corpus. A dimension that keeps its own editable copy of its
  authority has stopped being a contract and become a second source of
  truth.

## Cross-References

- `work-unit-craft` and `decompose`: produce the inputs each dimension
  considers before validation is defined.
- `take` (protocol): consumes dimension inputs and defines validation using
  this discipline.
- `plan` (protocol): maps scenarios to a decision-complete design.
- `implement` (protocol): executes RED-GREEN-REFACTOR per named scenario.
- `verify` (protocol): performs validation against each defined dimension —
  scenario and criterion coverage for behavior, and the documentation and
  code-quality contracts via its review references.
- `land` (protocol): records performed coverage and explicit gaps per
  dimension.
- `orient` (skill): owns the documentation audience taxonomy and writing
  stance the documentation dimension consults.
- principles corpus (`~/.groundwork/principles/`): the single home of the
  universals the code-quality dimension projects.
- [references/documentation-contract.md](references/documentation-contract.md):
  the documentation dimension's three sub-modules and checklists.
- [references/code-quality-contract.md](references/code-quality-contract.md):
  the code-quality projection and how it grows with the corpus.
