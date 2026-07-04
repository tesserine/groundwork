---
name: verification-craft
description: >-
  Use when authoring or reviewing a verification gate over methodology prose,
  generated text, or other text artifacts. The discipline for proving the
  protected invariant by consulting its authority, reading model coherence, or
  asserting substrate structure instead of matching vocabulary as a proxy.
metadata:
  version: "1.0.0"
  updated: "2026-07-04"
---

# Verification Craft

Verification gates exist to prove an invariant. A gate consults the
invariant, the owning authority, or substrate structure; it does not match
literal vocabulary against authored prose as a proxy for whether that prose is
correct.

This skill currently states the vocabulary-proxy face of the rule. A later
positive-form face can join this same home as a sibling section: new faces add
their form and boundary under the same craft, without rewriting the rule below.

## The Rule

A prose or text-artifact gate names the protected invariant first, then chooses
the form whose red state is the invariant being false. The correct form is the
smallest one that would fail for a hollow delivery and keep passing through a
meaning-preserving rewrite.

## Re-Grounded Forms

### Authority-Consultation

Use authority-consultation when another substrate owns the truth: a manifest,
schema, workflow contract, script, or declared skill home. The gate reads that
authority at run time and derives the expected surface from it, so changing the
authority flips the gate without editing a copied list.

Worked example: the artifact-delivery boundary gate in
[`tests/test_protocol_artifact_delivery_docs.py`](https://github.com/tesserine/groundwork/blob/252024f/tests/test_protocol_artifact_delivery_docs.py)
uses `tooling.prose_conformance.delivery_boundaries` to derive producing
protocols from `manifest.toml`, read each artifact schema, and verify the
delivery prose against those authorities.

### Model-Coherence

Use model-coherence when the invariant is that text presents the current
model, boundary, or lifecycle. The gate reads the text against the named model:
required commitments are present, retired states are absent only when their
tokens are the invariant, and a meaning-preserving rewrite still passes.

Worked example: `test_entry_surfaces_ground_on_the_whole_ticket` in
[`tests/test_forge_capability.py`](https://github.com/tesserine/groundwork/blob/252024f/tests/test_forge_capability.py)
uses `tooling.prose_conformance.entry_surface_coherence` to check the
read-ticket comment-log lifecycle across `acquire` and `take` instead of
pinning one sentence about entry context.

### Structural

Use a structural gate when the substrate shape is the invariant: a parsed
example, a table row, a link target, a workflow command, a fenced block, or a
serialized field. The gate parses or extracts the structure and asserts that
shape directly.

Worked example: `test_every_templates_dependency_graph_block_is_mermaid` in
[`tests/test_dependency_graph_notation.py`](https://github.com/tesserine/groundwork/blob/252024f/tests/test_dependency_graph_notation.py)
checks the dependency-graph blocks as Markdown structure and requires the
canonical Mermaid representation, rather than checking surrounding prose for a
preferred explanation.

## Retain Boundary: Token Is Invariant

A literal-token check is legitimate when the token is the invariant. Retain
that form for retired identifiers, schema fields that must be absent or
present, hard-code detectors, URL schemes, command strings, and other concrete
atoms whose occurrence is itself the state being tested.

Worked example: `RETIRED_FORGE_IDENTIFIER_PATTERNS` in
[`tests/test_forge_capability.py`](https://github.com/tesserine/groundwork/blob/252024f/tests/test_forge_capability.py)
retains per-document absence checks for retired forge identifiers such as
`forge_tags` and `RUNA_FORGE_`. Those identifiers are not prose proxies; their
presence is the forbidden state. The retained detector scans the full owning
surface and tolerates trivial casing or separator variants of the same
identifier.

Do not re-ground token-is-invariant checks away merely because they are literal
matches. Re-ground only the checks where a phrase stands in for whether prose
is correct.

## Paraphrase-Residual Boundary

A forbidden-state gate does not enumerate anticipated paraphrases. Its
completeness rests on two parts together:

- the positive authority-consultation or model-coherence check that proves the
  current state is present; and
- token-is-invariant detectors for the specific retired identifiers or retired
  text over the full owning surface.

That boundary accepts a residual: a novel paraphrase with no retired token may
pass. Closing that residual by adding guessed phrasings recreates the
vocabulary proxy. If the residual becomes too large, strengthen the positive
authority or coherence check; do not grow a synonym list.

## Authoring Procedure

1. Name the protected invariant.
2. Name the owning authority or substrate, or state that the text's coherence
   against a model is the authority.
3. Classify the gate as authority-consultation, model-coherence, structural,
   or token-is-invariant.
4. Add a proof fixture: mutate the authority, remove the required content,
   change the structure, or insert the specific retired identifier or text
   that the gate claims to catch.
5. Scan the full owning surface. A hand-listed pair of files is not enough
   when the invariant belongs to the docs tree, every protocol, or every
   installed skill.

## Corruption Modes

- `vocabulary-proxy`: a phrase list is treated as proof that prose is correct.
- `authority-copy`: the gate copies the current manifest, schema, or skill
  facts instead of reading the authority at run time.
- `paraphrase-chase`: a forbidden-state gate grows a list of imagined
  rewordings instead of relying on the positive check plus token-is-invariant
  detectors.
- `token-overcorrection`: a literal detector is removed even though the token
  is the invariant.
- `surface-undercount`: the gate checks one or two convenient files while the
  invariant belongs to a wider owning surface.

## Cross-References

- [`tooling/prose_conformance.py`](https://github.com/tesserine/groundwork/blob/252024f/tooling/prose_conformance.py) carries
  the shared helper forms for the current re-grounded gates.
- [`docs/architecture/decisions/0008-prose-is-projection.md`](../../docs/architecture/decisions/0008-prose-is-projection.md)
  records why prose must consult its owning substrate or be gate-bound.
- [`skills/contract/SKILL.md`](../contract/SKILL.md) owns the hollow-delivery
  tooth every verification gate must satisfy.
