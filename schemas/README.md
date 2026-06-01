# Schemas

This directory contains JSON Schemas for groundwork runtime artifacts and
authoring substrates. Most of these schemas are methodology-private and are
defined only in this repository.

`workflow-contract.schema.json` is an authoring substrate for C-2 workflow
contracts from ADR-0002. It is validated by `tooling.workflow_contracts`, not
declared as a runtime artifact type in `manifest.toml`.

`mechanic.schema.json` is an authoring substrate for C-3 mechanics from
ADR-0002. It is validated by `tooling.mechanics`, not declared as a runtime
artifact type in `manifest.toml`.

`change-proposal.schema.json`, `change-approved.schema.json`, and
`change-needs-revision.schema.json` are the C-4 artifact schemas for the
submit -> review handoff from ADR-0002 and ADR-0003. `change-proposal`
replaces the old PR-shaped `patch` artifact with a forge-neutral envelope plus
a forge-tagged handle. The review disposition is the produced outcome type:
`change-approved` cannot carry blocking findings, and `change-needs-revision`
must carry at least one blocking finding.

The old runtime `patch` artifact type is retired. Historical ADR and changelog
mentions remain as design history, but no live `patch` schema or artifact
fixtures are kept in this directory.

Change-proposal handle forge tags and mechanic-authored `forge_tag` values
resolve against the declarative `[[forge_tags]]` registry in `manifest.toml`.

`request.schema.json` is different: it is a vendored copy of the canonical
request contract maintained by `tesserine/commons`. Groundwork keeps the runtime
copy here so runtime consumers still read schemas from groundwork, not from
commons.

The vendored request schema carries provenance metadata identifying the
canonical authority, an immutable release-tag or commit-SHA URL for the
canonical schema and prose, and the request spec's full semver. When updating
the vendored copy, update both the schema content and the provenance metadata
together so conformance stays explicit.
