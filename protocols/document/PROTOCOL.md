---
name: document
description: >-
  Use after verification to review and update project documentation before
  submission, or when existing docs need classification for drift, missing
  coverage, or obsolescence. This is the focused documentation review protocol
  that records documentation coverage and tracking outcomes.
---

# Document

## Goal

Ensure documentation remains accurate and tracked as code evolves.

## Constraints

- `code-is-ground-truth`: when docs and code disagree, investigate. Code
  behavior is descriptive truth; docs are claims that must be checked.
- `drift-is-debt`: stale documentation compounds. Each drifted doc trains
  readers to distrust all docs, making accurate docs worthless too.
- `same-pr`: documentation updates ship in the same PR as the code change that
  caused them. If deeper work is needed, create a tracking work-unit rather than
  leaving drift untracked.

## Requirements

- `changelog-before-land`: user-visible changes include a CHANGELOG entry
  before landing so consumers can understand what changed without reading code.
- `docs-in-acceptance-criteria`: user-facing changes include documentation
  updates as explicit acceptance criteria in the work-unit.

## Procedures

### documentation-review

Fires after verification, before `submit`.

1. **Identify changed files.** Diff working tree or commit against base branch.
2. **Map changes to documentation.** For each changed file:
   - README — if the change affects setup, usage, or public API
   - ARCHITECTURE.md — if module boundaries, data flow, or structure changed
   - API reference — if public signatures, types, or behavior contracts changed
   - Inline doc comments — if function behavior changed
   - CHANGELOG — for any user-visible or API-visible change
   - ADRs — if the change implements or reverses a recorded decision
   - work-unit-model.md — if work-unit states, graph format, or maintenance rules changed
3. **Classify each mapped document:**
   - `accurate` — no update needed
   - `drifted` — claims no longer match code (update required)
   - `missing` — should exist but does not (creation required)
   - `obsolete` — references removed functionality (rewrite or delete)
4. **Update or track.** Update drifted or missing docs in the same PR. If
   deeper work is needed, create a tracking work-unit with `decompose`.
5. **Audit numeric claims.** Replace brittle counts with source-of-truth
   references, or explicitly verify and trace any remaining dynamic numbers.
6. **Apply audience test.** For each updated or created doc: "Would the
   intended reader know what to do after reading this?"
7. **Deliver `documentation-record`.** Invoke the
   `documentation-record` MCP tool. The object below is MCP tool input, not
   artifact body. `instance_id` is a tool parameter that names the artifact
   instance; it is extracted before validating artifact content, becomes the
   workspace filename, and must not appear in the artifact body. Runa injects
   `work_unit` from session context; the agent does not supply `work_unit`. Do
   not write the workspace JSON file directly:

   ```
   documentation-record({
     instance_id: "<slug>",
     updated_docs: ["..."],
     verified_accurate_docs: ["..."],
     tracking_work_units: ["..."]
   })
   ```

   Runa validates the remaining artifact body fields against the
   documentation-record schema, persists the artifact, and records it in the
   artifact store.

### evaluate-existing-docs

When encountering existing documentation:

1. For each documentation file, classify it as `accurate`, `drifted`,
   `missing`, or `obsolete` by comparing claims against actual code behavior.
2. Prioritize fixes: `missing` critical docs first, then `drifted`, then
   `obsolete`.
3. Create work-units for each fix using `decompose`.

## Triggers

- after code changes that modify documented behavior
- when existing docs need drift, missing, or obsolete classification
- before `verify`
- before `land` for user-visible changes

## Corruption Modes

- `drift-tolerance`: documentation is known stale but updating feels expensive.
  Run `documentation-review`. Track what you cannot fix now.
- `ceremony-over-substance`: docs updated to check a box. Changelog entries
  say "updated X" without explaining what changed. Ask: "Would a reader who
  missed this PR understand what changed from this doc update alone?"
- `ground-truth-confusion`: docs say one thing, code does another, and the
  docs are treated as authoritative. Run the code, observe behavior, then
  decide what must change.
- `agent-outpacing-docs`: multiple PRs land per day, doc reviews defer, drift
  compounds. Documentation review is part of completion, not separate work.

## Principles

- `less-accurate-beats-more-stale`: a small set of maintained docs is more
  valuable than a comprehensive set of drifted ones.
- `code-is-truth`: code behavior is the ground truth. Documentation is a model
  of that truth, subject to verification.

## Cross-References

- `orient`: provides the always-on documentation writing discipline that
  identifies audience, artifact choice, and depth before review time.
- `reckon`: grounded constraints define what architecture docs or ADRs must
  enable before they are reviewed as accurate.
- `specify`: behavior contracts are the authoritative source for what public
  behavior must be reflected in documentation.
- `decompose`: user-facing changes include documentation expectations in work-unit
  acceptance criteria; create tracking work-units here when review finds deeper
  follow-up work.
- `implement`: inline documentation changes alongside implementation; review checks
  whether those claims still match behavior.
- `verify`: this protocol runs after verification; its output feeds `submit`.
- `land`: CHANGELOG coverage and documentation status are recorded at landing.
