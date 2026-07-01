# Documentation Review

Reference for verify step 4: auditing the change against the declared
**documentation contract** (the contract skill's documentation dimension),
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
- `changelog-before-land`: user-visible changes carry a CHANGELOG entry so
  consumers understand what changed without reading code.

## Method

Begin from the declared contract. From the documentation contract authored
at `take`, list the pillars it declared (user / developer / discovery) and
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

The outcome feeds the `documentation` section of `completion-evidence`.

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
