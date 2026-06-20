# Schemas

This directory contains JSON Schemas for groundwork runtime artifacts and
authoring substrates. Most of these schemas are methodology-private and are
defined only in this repository.

`workflow-contract.schema.json` is an authoring substrate for C-2 workflow
contracts from ADR-0002. It is validated by `tooling.workflow_contracts`, not
declared as a runtime artifact type in `manifest.toml`.

`mechanic.schema.json` is an authoring substrate for C-3 mechanics from
ADR-0002. It is validated by `tooling.mechanics`, not declared as a runtime
artifact type in `manifest.toml`. Mechanic parameters are shell environment
variable names because invocation data is supplied through the child process
environment; secret parameters use `secret = true` and must remain values, not
rendered command text. Deployment-resolved parameters use `deployment_value` to
declare which forge deployment value the resolver supplies from the
`GROUNDWORK_*` environment contract; the resolver consults this declaration
rather than inferring parameter categories from names.

`change-proposal.schema.json`, `change-approved.schema.json`, and
`change-needs-revision.schema.json` are the C-4 artifact schemas for the
submit -> review handoff from ADR-0002 and ADR-0003. `change-proposal`
replaces the old PR-shaped `patch` artifact with a forge-neutral envelope plus
a forge-tagged handle: GitHub proposals point at a pull request, and SourceHut
proposals point at an immutable `refs/proposals/...` ref. The review disposition
is the produced outcome type: `change-approved` cannot carry blocking findings,
and `change-needs-revision` must carry at least one blocking finding.
The SourceHut proposal-ref schema pattern is only a coarse fail-fast filter;
mechanics use `git check-ref-format` as the authoritative ref-name boundary.

`work-unit.schema.json` is the planning-to-execution bridge. It remains
forge-neutral and unpartitioned: tracker-backed units may carry an optional
forge-tagged ticket `handle`, while non-tracker units omit `handle`, and
planning-phase work-unit bodies do not carry a top-level `work_unit` field.
Supported ticket handles are GitHub issue handles
`{ forge_tag, url, number }` and SourceHut ticket handles
`{ forge_tag, tracker_id, number }`; Groundwork artifact validation enforces
registry membership and GitHub URL/number agreement.

Change-proposal and work-unit handle forge tags, plus mechanic-authored
`forge_tag` values, resolve against the declarative `[[forge_tags]]` registry
in `manifest.toml`.
Manifest `[[mechanics]]` entries may declare `forge_tags = [...]` to bind an
operation handle to forge-specific C-3 mechanics; conformance requires exactly
one matching `mechanics/**/*.toml` file for each declared operation/tag pair.

The behavior artifact spine uses one artifact type per station and a required
`behavior_form` discriminator instead of parallel scenario/gate artifact types:
`behavior-contract`, `implementation-plan`, `test-evidence`, and
`completion-evidence` each require `behavior_form: "scenario"` or
`behavior_form: "gate"`. Scenario form carries executable Given/When/Then
behavior through `scenarios`, scenario-keyed mappings, scenario-keyed evidence,
and scenario coverage. Gate form carries documentation-deliverable behavior
through structural/coherence/conformance `gates`, gate mappings, gate evidence,
and gate coverage. In `completion-evidence`, both forms enforce the same
status-to-evidence invariant: `covered` criteria carry passing evidence and no
failures, `partial` criteria carry evidence plus at least one failure signal,
and `uncovered` criteria carry no evidence or failures. Gate coverage treats a
failed gate result and a non-empty `failures` list as the two valid partial
failure channels. Root schemas remain ordinary top-level object schemas with no
root `oneOf`, `anyOf`, `allOf`, or `$ref`, so runtime tool advertisement
continues to expose them as MCP artifact tools.

Downstream consumers that build against a Groundwork schema contract pin a
release tag or the merged full commit SHA. They do not pin a branch name or
pre-merge ref.

`request.schema.json` is different: it is a vendored copy of the canonical
request contract maintained by `tesserine/commons`. Groundwork keeps the runtime
copy here so runtime consumers still read schemas from groundwork, not from
commons.

The vendored request schema carries provenance metadata identifying the
canonical authority, an immutable release-tag or commit-SHA URL for the
canonical schema and prose, and the request spec's full semver. When updating
the vendored copy, update both the schema content and the provenance metadata
together so conformance stays explicit.
