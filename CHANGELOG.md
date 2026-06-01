# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added

- Workflow contract authoring substrate: a C-2 directed-graph JSON Schema,
  TOML parser, graph invariant checks, registry-reference validation, and
  fixture coverage for linear, branching, loop, and multi-terminal contracts
  (closes #293).
- Mechanic authoring substrate: a C-3 JSON Schema, TOML parser, optional
  forge-tag validation, registry-reference validation, and fixture coverage for
  forge-neutral, forge-tagged, and runtime-tool mechanics (closes #294).
- Change proposal review substrate: C-4 `change-proposal`,
  `change-approved`, and `change-needs-revision` artifact schemas, fixture
  coverage for GitHub and SourceHut handles, disposition/blocking-finding
  consistency through typed review outcomes, manifest-declared forge tags, and
  format-enforced artifact validation (closes #316).
- Narrowed Step 1 conformance runner for C-2 workflow contracts, C-3
  mechanics, C-4 artifact instances, and JSON Schema definitions, with
  aggregate pass/fail reporting and non-zero exit on failure (closes #297).
- Required-choice outcome group conformance substrate: C-5 manifest dispatch,
  `[[outcome_types]]` vocabulary validation, manifest required-output-choice
  member validation, outcome-trigger routing checks, and C-2 workflow terminal
  parity against the manifest group (closes #336).
- Source C-2 workflow contract exercise for the forge-neutral `verify`
  protocol, including default conformance coverage and a Step 1 R1 note
  recording that the format held for `verify`'s shape without schema/parser
  revision (closes #317).
- Step 2 reference arc design note resolving review-cycle semantics, finding
  classification ownership, approved-disposition land gating, and
  forge-operation resolution constraints for downstream authoring units
  (closes #329).
- Review protocol authoring surface: source C-2 `review` contract,
  `code-review` skill, manifest-registered required-choice outcome group, and
  typed review disposition routing through `change-approved` /
  `change-needs-revision` (closes #331).
- GitHub C-3 mechanic library for the reference arc:
  `deliver-change-proposal`, `apply-approved-change`, and
  `reflect-disposition` now have forge-tagged mechanics bound from
  `manifest.toml`, with conformance enforcing exactly one C-3 implementation
  for each declared operation/tag pair.
- SourceHut C-3 mechanic library for the reference arc: list-free
  `deliver-change-proposal` now stores the mbox and pushes the proposal ref,
  `apply-approved-change` fetches that ref and guards tree equality after
  plain `git am --3way`, and `reflect-disposition` records tracker-ticket
  state under `forge_tag = "sourcehut"`.

### Changed

- Submit and land now complete the disposition-gated reference arc:
  `submit` produces `change-proposal`, review emits `change-approved` or
  `change-needs-revision`, revision reactivates submit, and `land` activates
  only from `change-approved` while resolving the approved proposal by
  `(work_unit, against_version)`. The manifest-level `patch` artifact type and
  schema are retired (closes #340).

### Fixed

- SourceHut `deliver-change-proposal` now uploads the mbox artifact against a
  pushed git tag revspec instead of the proposal branch ref, matching
  SourceHut `uploadArtifact` requirements while preserving
  `change-proposal.branch` for downstream apply.
- C-5 manifest conformance now rejects disposition-agnostic outputs of
  outcome-bearing protocols through `on_change`, `on_invalid`, and composite
  triggers, while preserving valid re-review triggers on protocol inputs.
- Release-cut now ignores its own generated `release_lib` bytecode cache during
  the clean-tree pre-check, so the documented release ceremony works from a
  fresh checkout after prior `release-check` invocations (closes #311, #315).
- Step 1 conformance now validates C-2 workflow registry references and reports
  explicit path read failures as aggregate failures instead of aborting.
- Step 1 conformance now classifies explicit relative TOML paths from inside
  `workflow-contracts/` or `mechanics/` directories by resolving them before
  dispatch; TOML files outside those unit directories remain unsupported.
- Step 1 conformance directory arguments now use the same unit discovery rules
  as the default runner, while explicitly named non-units still fail.
- Directory-discovered C-2 workflow contracts and C-3 mechanics now validate
  registry references against the directory-local `manifest.toml`, and C-5
  rejects malformed known manifest keys instead of silently treating them as
  absent.
- Mechanic substrate validation now rejects empty `examples` arrays and
  registry-loaded mechanics whose `forge_tag` is not declared in
  `manifest.toml`; generic runtime mechanics remain forge-neutral by omitting
  `forge_tag` (closes #322).
- Interactive install now projects the artifact delivery adapter into every
  protocol entry without depending on protocol prose formatting, so wrapped MCP
  delivery text cannot omit the adapter from installed protocol skills.

## [0.2.0] — 2026-05-17

### Added

- Official interactive install tooling for Claude Code and Codex:
  `scripts/groundwork-install` installs, syncs, reports status for, and
  uninstalls Groundwork skills and protocols from a clean pinned checkout into
  `~/.claude/skills/` and `~/.agents/skills/`. Installed entries are copied
  rather than symlinked, protocols are projected as skill-shaped entries, and
  ownership tracking prevents uninstall from removing operator-managed entries.
  Re-running install against the same unchanged pinned source leaves current
  managed entries untouched while still restoring managed target drift
  (closes #306).
- Release ceremony tooling for the Groundwork methodology release surface:
  `manifest.toml` is now the version-of-record, `scripts/release-check`
  verifies release metadata and tag identity, `scripts/release-cut` performs
  the atomic release operation, and GitHub Actions publish tag-backed releases
  from changelog notes. The verifier rejects tag-time releases with pending
  Unreleased entries, validates manifest-declared schemas as JSON, and
  preserves pre-existing local tags during release-cut failures (closes #301).

### Fixed

- Release tag-push workflows now restore annotated tag refs after checkout and
  verify the restored tag still matches the triggering event before enforcing
  annotated-tag trust (closes #308).
- Interactive install now prepares every discovery root before mutating managed
  entries, so a non-preparable later root cannot leave earlier roots with
  marker-bearing entries that lack an install state record.
- Interactive install now derives installed skill and protocol payloads from the
  pinned commit content instead of the checkout working tree, so ignored local
  artifacts under `skills/` or `protocols/` cannot leak into discovery
  directories.
- Protocol artifact-delivery sections now distinguish MCP tool input from
  artifact body content across all ten artifact-producing protocols. The
  examples still show the flat MCP input shape, including `instance_id`, while
  clarifying that runa extracts routing parameters before schema validation,
  injects `work_unit` for scoped protocols, and requires delivery through the
  MCP tool rather than direct workspace writes (refs #299, closes #300).

## [0.1.2-rc.1] — 2026-05-05

### Added

- New authoring guide `docs/authoring/skills.md` for the `SKILL.md`
  frontmatter convention. Compiles the post-audit convention
  (settled in #245) into follow-direct form so a methodology author
  writing a new skill can produce valid frontmatter from one document
  alone, without reverse-engineering it from existing skills or the
  canonical reference. `docs/architecture/connecting-structure.md`
  forward-references the new guide from the "Authoring surfaces and
  authority" section (closes #227).
- `docs/architecture/decisions/0002-methodology-sovereignty.md` —
  ADR establishing that each methodology unit specifies content of a
  single shape (WHAT or HOW), not both.

### Changed

- `submit` now treats PR presence as the primary deliverability rule: when an
  open PR exists, it records the PR URL plus head SHA, head branch, head
  repository, and base repository, fetches the PR head object through the
  matching PR base repository remote, classifies local `HEAD` against that PR
  head by ancestry after commit analysis has completed, and pushes updates to
  the discovered PR head repo/ref instead of assuming `origin <branch>` backs
  the PR. When multiple open PRs share the same branch name, they are
  disambiguated by head repository against a matching local remote before any
  PR is selected.
  When no PR exists, upstream tracking is read from the classification-time
  branch state, `git log main..HEAD` determines whether the branch has
  deliverable commits for a new PR under first-push or already-pushed
  semantics, and upstream-ahead commits determine only whether a push is needed
  before PR creation; an already-pushed branch still needs a PR, while an empty
  base-branch comparison reports `clean-branch-no-changes` (closes #253).
- Main-sync guidance in `take` and `land` now uses explicit fetch plus
  fast-forward merge instead of `git pull --ff-only`, so protocol execution
  does not inherit a user's global `pull.rebase` setting (closes #251).
- `schemas/request.schema.json` now vendors the commons canonical request
  schema with inline provenance metadata, and `schemas/README.md` documents
  the vendoring discipline for methodology runtime schemas (closes #247).
- Normalized in-scope prose to the canonical hyphenated `work-unit` /
  `work-units` spelling across protocols, skills, architecture docs, README,
  and changelog entries. Machine-facing `work_unit` identifiers remain
  unchanged (closes #242).
- Protocol bodies now describe runa-managed execution end-to-end: `survey`
  activates on a `request` artifact rather than being self-invoked by the
  agent; `decompose` is reframed as `work-unit` artifact production rather
  than GitHub-issue management (the close event moves to `land`); `take`
  consumes the injected `work-unit` and produces its `claim` capstone
  rather than listing the forge tracker to select work; all ten producing
  protocols now name their capstone delivery path through runa's MCP tool
  surface instead of leaving agents to infer a non-MCP path. Planning-phase
  artifacts (`requirements`, `work-unit`) describe agent-supplied payloads
  directly; scoped execution artifacts (`claim`, `behavior-contract`,
  `implementation-plan`, `test-evidence`, `completion-evidence`,
  `documentation-record`, `patch`, `completion-record`) distinguish
  agent-supplied fields from runa-injected `work_unit`; `submit` and `land`
  no longer hard-require the `gh` CLI — forge tooling becomes conditional
  with graceful degradation. `work-unit` now also carries optional `scope`
  and `out_of_scope` boundary arrays, and tracker-backed first delivery uses
  reversible `instance_id` convention `work-unit-<N>-<short-slug>` so
  `take` framing and dependency references remain structurally recoverable
  across protocol boundaries (closes #214, #215, #216, #217, #218, #222).
- Protocol self-description language aligned across five runa-managed
  protocols: `take`, `implement`, `verify`, `submit`, and `land` now
  describe themselves as protocols rather than skills, matching the
  protocol/skill distinction runa makes operational. Legitimate skill
  delegations (to `orient`, `reckon`, `research`, `debug`) remain framed
  as skill invocations (closes #219).
- Canonical repository references now point at the `tesserine` organization
  across schema `$id` values, documentation links, and artifact fixtures,
  replacing stale pre-migration repository URLs left behind by the org move.
- Breaking vocabulary rename: artifact type `issue` becomes `work-unit`, and
  protocol `begin` becomes `take`. Consumers using the old vocabulary must
  update manifests, schema paths, protocol references, and fixture names.
- Four planning/specification protocols (survey, decompose, specify,
  plan) now declare `may_produce = ["research-record"]` in
  `manifest.toml`. With this wiring, an agent inside any of these
  protocol sessions can persist a fresh research-record through runa
  rather than producing it as a loose skill artifact.
- Skill and protocol frontmatter now keeps only minimal
  harness/reader-facing identification data. Runa contract
  declarations live only in `manifest.toml`, and removing the mirrored
  protocol `may_produce` fields eliminates the already-existing
  `research-record` drift case those duplicates had accumulated.
- Canonical reference (`docs/architecture/connecting-structure.md`)
  gains Runtime Layers and Skill-Produced Artifacts sections that
  document the four-layer agentd/harness/runa/groundwork model and
  the `may_produce` bridge from skill output into runa's validated
  artifact store. The Agent Interface section is rewritten to
  describe the MCP-tool-per-declared-output-artifact mechanism at
  interface level, citing runa's interface contract for the
  internal filtering rules rather than restating them.

## [0.1.0] — 2026-04-04

First release. Groundwork is a methodology plugin for
[runa](https://github.com/tesserine/runa) that encodes opinions about how
software should be built — from problem framing through shipped change — into
protocols, skills, and artifact schemas that a runa instance orchestrates.

### Protocol topology

- `manifest.toml` declares 12 artifact types and 10 protocols with their
  dependency edges (`requires`, `accepts`, `produces`, `may_produce`), trigger
  conditions, and scoping. This is the single file runa reads to understand
  the methodology.
- Two planning-phase protocols (unscoped): **survey** produces requirements
  from an external request; **decompose** produces session-sized work-units with
  acceptance criteria and dependency edges.
- Eight execution-phase protocols (all `scoped = true`, work-unit threaded):
  **take** claims a work-unit and opens the session → **specify** writes the
  behavior contract as Given/When/Then scenarios → **plan** converges on a
  decision-complete design → **implement** executes through RED-GREEN-REFACTOR
  → **verify** gates completion with behavior-level evidence → **document**
  ensures documentation accuracy → **submit** packages the change into a PR →
  **land** merges and closes the loop.
- Artifacts form a directed acyclic graph from request through
  completion-record. Execution order emerges from the dependency graph — it is
  not declared.
- All protocol triggers are `on_artifact`. No signal-based triggers.
- Three protocols (implement, plan, verify) carry upstream attribution via
  `LICENSE-UPSTREAM` files.
- Reference materials bundled with protocols: issue templates
  (`decompose/references/templates.md`), Given/When/Then language patterns for
  Rust, Python, TypeScript, Go, and Java
  (`specify/references/language-patterns.md`), and testing anti-patterns
  (`implement/references/testing-anti-patterns.md`).
- Structural linter (`decompose/scripts/issue_lint.py`) validates issue bodies
  against template schemas.

### Skills

- Six cross-cutting disciplines, agent-managed rather than runa-triggered.
  Each fires when its trigger condition matches the current work.
- **orient** — methodology map and documentation discipline. Loads the
  connected skill system at session start so subsequent skills operate as one
  methodology rather than in isolation.
- **reckon** — first-principles reasoning. Position and momentum as one act:
  establish what is actually needed, reason from ground with traced chains,
  catch inherited assumptions.
- **debug** — root-cause investigation before fixes. Stop, read, reproduce,
  trace, then hypothesize-and-test. Three-fix escalation rule: after three
  failed attempts, question the architecture. Carries upstream attribution via
  `LICENSE-UPSTREAM`.
- **resolve** — friction resolution through the reconciling force. When
  operational friction appears, stop and resolve structurally instead of
  routing around. Scope guidance distinguishes inline side quests from work-units.
- **research** — systematic multi-source research with citations. Six-phase
  workflow (clarify, decompose, gather, evaluate, resolve, synthesize).
  Produces a typed artifact (research-record) that other protocols can accept.
- **contract** — behavior traceability through implementation and verification.
  Carries the behavior contract forward so tests, code, and completion claims
  map to named scenarios.
- Reference material: defense-in-depth validation pattern
  (`debug/references/defense-in-depth.md`).

### Artifact schemas

- Twelve JSON Schemas (draft 2020-12), one per artifact type declared in
  `manifest.toml`.
- Planning-phase artifacts carry no `work_unit` field: **request** (external
  input), **requirements** (scope, constraints, priorities),
  **work-unit** (work-unit with acceptance criteria and dependencies).
- Execution-phase artifacts carry a `work_unit` envelope for runa's scoped
  validation: **claim** (threading root), **behavior-contract** (Given/When/Then
  scenarios), **implementation-plan** (design decisions, affected files,
  behavior mapping), **test-evidence** (results mapped to scenarios),
  **completion-evidence** (criterion-level coverage),
  **documentation-record** (docs reviewed and tracked), **patch** (PR
  reference), **completion-record** (final state with coverage summary and
  gaps).
- Cross-cutting: **research-record** with optional `work_unit` — produced by
  the research skill, accepted by survey, decompose, specify, and plan.
- Test fixtures (`tests/fixtures/artifacts/`) provide valid and invalid
  examples for all 12 artifact types.

### Architecture documentation

- `docs/architecture/connecting-structure.md` — artifact flow design, trigger
  semantics, work-unit scoping model, schema design rationale, and agent
  interface.
- `docs/architecture/work-unit-model.md` — work-unit working states (draft, ready,
  in-progress, blocked, closed, stale), dependency graph format, and graph
  maintenance rules.
- `docs/architecture/decisions/0001-internal-development-history-policy.md` —
  ADR establishing that repo artifacts document state, not transitions.
