# Schemas

This directory contains JSON Schemas for groundwork runtime artifacts and
authoring substrates. Most of these schemas are methodology-private and are
defined only in this repository.

`workflow-contract.schema.json` is an authoring substrate for C-2 workflow
contracts from ADR-0002. It is validated by `tooling.workflow_contracts`, not
declared as a runtime artifact type in `manifest.toml`.

`mechanic.schema.json` is an authoring substrate for C-3 mechanics from
ADR-0002. It is validated by `tooling.mechanics`, not declared as a runtime
artifact type in `manifest.toml`. Mechanics cover non-forge runtime actions.
Mechanic parameters are shell environment variable names because invocation
data is supplied through the child process environment; secret parameters use
`secret = true` and must remain values, not rendered command text.

`change-proposal.schema.json`, `change-approved.schema.json`, and
`change-needs-revision.schema.json` are the C-4 artifact schemas for the
submit -> review handoff from ADR-0002 and ADR-0003. `change-proposal`
carries a forge-neutral envelope plus the connector-issued `{ id, display }`
handle for the delivered proposal. The review disposition is the produced
outcome type: `change-approved` cannot carry blocking findings, and
`change-needs-revision` must carry at least one blocking finding.

`work-unit.schema.json` is the planning-to-execution bridge. Every work unit
is tracker-backed and carries the connector-issued `{ id, display }` handle.
Planning-phase work-unit bodies do not carry a top-level `work_unit` field.

The vendored forge capability schema at
`schemas/forge-capability/v2/forge-capability.schema.json` is the authority for
the connector handle definition and the eight canonical forge operations.
Groundwork artifact schemas carry self-contained copies of the handle schema so
runa can validate artifacts without an external registry or network fetch, and
conformance checks that those copies do not drift from the vendored contract.

`freshen-record.schema.json` is an authoring substrate for the freshen record
produced when an acquired work-unit is re-grounded at the acquisition boundary
(`skills/acquire/SKILL.md`). It is the single home of the freshen disposition
set (the `disposition` enum), the record's four required elements, and the six
dependency-graph facets (the `graph_finding` required keys). It is deliberately
not a `manifest.toml` artifact type: the record's home is a tracker comment, not
a workspace artifact, so declaring an artifact type would mint a second
workspace home and an MCP tool for something that must not accrete in the
workspace. Placement in `schemas/` alone registers it with the conformance
sweep; the acquire surface renders the set, elements, and facets as projections
gate-bound to this schema.

The scoped contract spine is lens-agnostic. `contract.schema.json`
declares criteria for any lens; each criterion names its `lens` — the
source-and-coverage grouping its content comes from, per
[ADR-0010](../docs/architecture/decisions/0010-content-kinds-behavior-and-meaning.md) —
the numbered work-unit acceptance criterion or explicit body-ground obligation
source it refines, the statement that defines done, the hollow delivery that
would fail it, its content `kind`, and its `check`. What determines how a
criterion is checked is its `kind`, never its lens: `behavior` content is
checked by executing its procedure and reading the stated observable;
`meaning` content is checked by grading a reconstruction against its stated
proposition. The `check` object carries the operational procedure either
way — `actor`, `procedure`, `observable`, and declared `conforming_case`
and `falsifying_case` — whether or not today's environment runs it
mechanically; where a check runs is binding policy, not contract content.
`completion-evidence.schema.json` records one
performed result shape per contract criterion.
Root schemas remain ordinary top-level object schemas with no root `oneOf`,
`anyOf`, `allOf`, or `$ref`, so runtime tool advertisement continues to expose
them as MCP artifact tools.

Downstream consumers that build against a Groundwork schema contract pin a
release tag or the merged full commit SHA. They do not pin a branch name or
pre-merge ref.

`intent.schema.json` is different: it is a vendored copy of the canonical
intent contract maintained by `tesserine/commons`. Groundwork currently vendors
intent spec `2.0.0` from `schemas/intent/v2/intent.schema.json`. Groundwork
keeps the runtime copy here so runtime consumers still read schemas from
groundwork, not from commons.

The vendored intent schema carries provenance metadata identifying the
canonical authority, the canonical schema and prose URLs, and the intent spec's
full semver. This pre-release vendoring pins the commons merge commit because
no release tag yet contains the intent path; released vendoring should use
immutable release-tag or commit-SHA URLs. When updating the vendored copy,
update both the schema content and the provenance metadata together so
conformance stays explicit.
