# ADR-0005: Principles Corpus Configuration

**Status:** Provisional \
**Date:** 2026-06-12 \
**Traces to:** [pentaxis93/principles](https://github.com/pentaxis93/principles)
(Sovereignty, Single Home, Grounding, Parsimony); epic
[tesserine/groundwork#397](https://github.com/tesserine/groundwork/issues/397).

## Context

Reckon reasons from a principles corpus during Orient. Until this
decision, the corpus was an inline operational dependency: reckon's skill
text linked one repository (`pentaxis93/principles`) directly. The desired
property is not "no runtime dependency" — reckon *should* depend on a
corpus — but "no hard-coded dependency": the corpus must resolve through
configuration, with a minimal embedded default so a bare checkout reasons
offline with zero configuration.

Selecting the configuration surface required deciding between three
candidates observed in the substrate:

1. **`manifest.toml`** — the methodology topology surface runa reads.
2. **Environment atoms** — the deployment env-var lineage, since partially
   migrated to runtime-owned `RUNA_*` atoms (#389).
3. **A dedicated config file** — deployment-owned, outside the methodology
   tree.

## Decision

A dedicated, deployment-owned TOML config file at
`${XDG_CONFIG_HOME:-~/.config}/groundwork/principles.toml`, schema-validated
against `schemas/principles-config.schema.json`, parsed by
`tooling/principles_config.py`.

The config declares the **configured source** (`embedded` | `path` |
`git`). It is distinct from the **resolved local corpus** — the stable
local location (`~/.groundwork/principles/` under the managed runtime
root) that the resolution layer materializes the source into at setup,
and which reckon consults during reasoning. Absent configuration resolves
to the embedded default shipped in-tree at `principles/`.

### Why not `manifest.toml`

The manifest ships *with* the methodology and describes its invariant
topology to runa. Corpus selection is a per-deployment override — a
different owner (the deployment, not the methodology author) and a
different lifecycle (changeable without editing the methodology tree).
Sovereignty places the choice with its owner; putting a deployment knob
in the shipped manifest crosses that boundary.

### Why not environment atoms

Forge addressing is now delivered as the runtime-owned
`RUNA_PROJECT_FORGE_ADDRESSES` payload, selected by configured resource
selectors, while the corpus is methodology content resolved once at setup,
not per-session identity. Env vars also offer no structural validation; the
repo's established
structural-impossibility tier (TOML + JSON Schema, the C-2/C-3 prior art)
is available to a file and not to an environment.

### Why TOML + JSON Schema

Consistency with every other configured surface in this repository
(`manifest.toml`, workflow contracts, mechanics): `tomllib` parsing,
Draft 2020-12 validation, named per-path errors. One convention, not two
(Single Home).

### Failure semantics

A *missing* config file is the ordinary path and selects the embedded
default. A *present but invalid* file (unreadable, invalid TOML, schema
violation, relative corpus path) fails loudly with named errors. The
distinction is deliberate: zero-config is first-class, but an expressed
configuration that cannot be honored must never silently degrade the
reasoning substrate.

## Consequences

### Good

- Reckon's corpus dependency becomes configurable without becoming
  optional: the embedded default preserves standalone, offline operation.
- `pentaxis93/principles` appears only as an example value in
  documentation — the canonical choice for Tesserine deployments, never a
  baked-in operational default.
- The source/resolved distinction gives the resolution layer (setup-time
  materialization) and reckon (read-only consultation of local content) a
  clean contract, and makes "no live fetch mid-reckon" structurally
  expressible.

### Neutral

- The config file is invisible to the conformance runner (it lives
  outside the tree); its schema is conformance-checked, and its parsing
  is test-covered. Setup-time validation is the resolution layer's
  responsibility.

### Bad

- One more deployment-owned file location to know about. Mitigated by the
  zero-config default and by `docs/principles-corpus.md` documenting both
  paths.
