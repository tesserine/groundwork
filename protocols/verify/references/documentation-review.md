# Documentation Review

Reference for verify step 4: auditing the change against the declared
**documentation contract** (the contract skill's documentation lens),
and keeping existing documentation honest against drift, before the change
is packaged for review.

## Constraints

- `code-is-ground-truth`: when docs and code disagree, investigate. Code
  behavior is descriptive truth; docs are claims that must be checked.
- `drift-is-debt`: stale documentation compounds. Each drifted doc trains
  readers to distrust all docs, making accurate docs worthless too.
- `same-change`: documentation updates ship with the code change that
  caused them. Deeper work gets a tracking work-unit rather than untracked
  drift.
- `standard-raising`: retrofit to a raised documentation standard is
  graded by recipient exposure — a surface where a recipient lands cold
  (met-cold) is audited against the raised standard as a scheduled
  retrofit unit; a change touching a below-standard surface brings it to
  the standard in the same change (the `same-change` rule applied to
  standard-raising); interior, maker-met artifacts stand until touched
  (accept-legacy). Landed contract and evidence records stand as true
  records of the machine that produced them. This rule's home is here;
  other surfaces consult it.
- `changelog-before-land`: user-visible changes carry a CHANGELOG entry so
  consumers understand what changed without reading code.

## Method

Begin from the declared contract. From the documentation contract authored
at `define`, list the pillars it declared (user / developer / discovery) and
the outcome each must reach; those outcomes are what this audit confirms.
The steps below keep the surrounding documentation honest against drift.

1. **Identify changed files.** Diff the working tree or branch against the
   base.
2. **Map changes to documentation.** For each changed file:
   - README — if setup, usage, or public API is affected
   - ARCHITECTURE doc — if module boundaries, data flow, or structure changed
   - API reference — if public signatures, types, or contracts changed
   - Inline doc comments — if function behavior changed
   - CHANGELOG — for any user-visible or API-visible change
   - ADRs — if the change implements or reverses a recorded decision
   - Command help (invocation surface) — if the change ships or alters a
     command's invocation: `--help`, subcommand help, usage, interactive
     prompt flows
   - Error output (failure surface) — if the change ships or alters a
     failure path a recipient meets
   - Machine self-description — if the change ships or alters an MCP tool
     description, a schema, or a manifest entry an agent discovers
3. **Classify each mapped document:**
   - `accurate` — no update needed
   - `drifted` — claims no longer match code (update required)
   - `missing` — should exist but does not (creation required)
   - `obsolete` — references removed functionality (rewrite or delete)
4. **Update or track.** Update drifted and missing docs in this branch. If
   deeper work is needed, file a tracking work-unit — the deferral is
   recorded, never silent.
5. **Audit numeric claims.** Replace brittle counts with source-of-truth
   references, or verify any remaining dynamic numbers.
6. **Apply the audience test.** For each updated or created doc: would the
   intended reader know what to do after reading this?
7. **Confirm each declared outcome.** For every pillar the contract
   declared, confirm a recipient of that pillar can now reach the declared
   outcome — the audience test applied to the contract, not only to touched
   files. An outcome a doc-less delivery would still fail is unmet; the
   change is incomplete until it is met or the gap is tracked as a follow-up
   work-unit.
8. **Cold-read changed first-contact surfaces.** For each command help,
   error output, or machine self-description the change ships or alters:
   render the surface and record a finding per question of its outcome
   form (the contract reference's meeting-surface axis), as a reader with
   no session context. The performed result enters the declared
   criterion's `completion-evidence.results[]` as the manual performance
   of the criterion's stated procedure.

The declared documentation criterion's performed result is recorded in
`completion-evidence.results[]` as attested evidence: reviewer identity plus
the finding for each selected pillar or outcome. The `documentation` section
remains the document-impact index — updated documents, documents verified
accurate, and follow-up work-units — not the evidence home for a declared
documentation criterion.

## Corruption Modes

- `ceremony-over-substance`: changelog entries that say "updated X" without
  explaining what changed. Ask: would a reader who missed this change
  understand it from the entry alone?
- `ground-truth-confusion`: treating drifted docs as authoritative over
  observed code behavior.
- `agent-outpacing-docs`: deferring doc review because changes land fast.
  Documentation review is part of completion, not separate work.

## Principles

- `less-accurate-beats-more-stale`: a small set of maintained docs is worth
  more than a comprehensive set of drifted ones.
