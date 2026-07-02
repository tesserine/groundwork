# Code-Quality Review

Reference for verify step 4: auditing the change against the declared
**code-quality contract** (the contract skill's code-quality dimension)
before the change is packaged for review.

The contract declared, at `take`, the principles-corpus universals this
change most stresses. This review audits the diff against each one. The
review is the gate; a self-report of cleanliness is not the evidence
(**Verifiable Completion**, **Honest Signal**).

## Method

Begin from the declared contract, splitting its code-quality criteria by
`check_kind`. An **executable** criterion — a structural projection whose
check is a fitness function — is verified by running its declared check
and recording the run in `completion-evidence.results[]`; the reference
implementation for layer edges is `tooling/import_direction.py`. The
audit below is the **attested** criteria's method. List the universals
those declared for this change; they are what the audit decides.

1. **Read the diff as the substrate.** Audit the committed change, not the
   author's account of it. For each declared universal, the universal's full
   content lives in the principles corpus (`~/.groundwork/principles/`) —
   consult it, do not re-derive it here.
2. **Find a locus or a finding, per universal.** For each declared
   universal, identify either the place in the diff where it holds or the
   place it fails. "Looks fine" is not a disposition; a locus or a finding
   is. The contract skill's
   [code-quality-contract.md](../../../skills/contract/references/code-quality-contract.md)
   carries each universal's question and its failing tell.
3. **Resolve each finding.** A failure is fixed in the same change, or
   tracked as a follow-up work-unit — never silently dropped. Closing the
   gap that admitted the failure, not only the failure, is the process half
   (**Recursive Improvement**).
4. **Feed the projection back.** A universal this change stressed that the
   projection does not yet name, or a projected item that keeps misfiring,
   is friction on the corpus — record it so the code-quality projection can
   grow. The corpus is the bounded asset the spiral acts on.

The declared code-quality criterion's performed result is recorded in
`completion-evidence.results[]` shaped by its `check_kind`: run (or
produced-artifact) evidence for an executable projection; for an attested
one, reviewer identity plus the per-universal disposition and finding for
each selected universal or projection. The verify report remains the review narrative, and the
`documentation` section remains the document-impact index — updated
documents, documents verified accurate, and follow-up work-units — not the
evidence home for a declared code-quality criterion.

## Cross-references

- [../../../skills/contract/references/code-quality-contract.md](../../../skills/contract/references/code-quality-contract.md)
  — the projection, each universal's question and failing tell.
- principles corpus (`~/.groundwork/principles/`) — the home of each
  universal's full content.
- [documentation-review.md](documentation-review.md) — the sibling audit for
  the documentation dimension.
