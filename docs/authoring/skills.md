# Authoring a Skill: Frontmatter Convention

## Audience and purpose

This document is for a **methodology author writing a new skill**. After
reading it, you will know exactly what fields to put in your skill's
`SKILL.md` frontmatter, what to leave out, and why each decision is the
way it is. You can produce valid frontmatter from this document alone,
without reading existing skills or the canonical architecture reference.

For the underlying architectural reasoning — why skills sit where they
do in the runtime layering, and why skill frontmatter does not mirror
runa's contract surface — see
[`docs/architecture/connecting-structure.md`](../architecture/connecting-structure.md#authoring-surfaces-and-authority).

## Convention summary

A `SKILL.md` file begins with a YAML frontmatter block delimited by
`---` lines. The block carries three layers of fields:

| Layer | Fields | Required? | Consumer |
|-------|--------|-----------|----------|
| Identification | `name`, `description` | required | the harness — reads them to identify and activate the skill |
| Metadata | `metadata` | optional | human readers (contributors, maintainers) — no machine reads it |
| Forbidden | `requires`, `accepts`, `produces`, `may_produce`, `trigger` | must not appear | these are runa's contract surface and live only in `manifest.toml`; skills are not in runa's contract |

Only the identification layer is required. Metadata is optional. The
forbidden layer must be omitted entirely.
This keeps skill authoring focused on agent activation, while protocol
contract routing remains centralized in the manifest.

## Field reference

### `name` — required

A kebab-case string identifier. Must match the skill's directory name
under `skills/`. The harness uses this to identify the skill.

```yaml
name: debug
```

### `description` — required

A prose string describing when to use the skill. The harness reads this
on every session and uses it to decide when to surface the skill to the
agent. Convention: lead with the trigger condition ("Use when …" or a
direct statement of the failure mode the skill addresses) so harness
activation matches against terms a reader would naturally use.

When the description spans multiple lines, prefer YAML's folded scalar
syntax (`>-`) so the rendered string is one paragraph with single-space
joins:

```yaml
description: >-
  Root-cause investigation discipline. Use when a test fails, behavior is
  unexpected, or any failure occurs — before proposing fixes.
```

Single-line descriptions may be written as a plain string.

### `metadata` — optional

An open object for human-oriented context. No machine reads it; runa
does not see skills, and the harness does not parse this block. Include
fields here when a contributor or maintainer would benefit from the
information; omit the block entirely when there is nothing to say.

Conventional sub-fields observed in the codebase:

| Field | Purpose |
|-------|---------|
| `version` | Skill version, when the author tracks one |
| `updated` | ISO date of last substantive revision |
| `origin` | Attribution when the skill is adapted from an upstream source — required when `LICENSE-UPSTREAM` applies |
| `source` | Free-form provenance note (e.g., `internal`) when origin is not external |

None of these are individually required. The convention is "include
what helps a future reader; omit the rest."

## Worked examples

### With metadata (lifted from `skills/debug/SKILL.md`)

```yaml
---
name: debug
description: >-
  Root-cause investigation discipline. Use when a test fails, behavior is
  unexpected, or any failure occurs — before proposing fixes. Enforces
  structured investigation before fix attempts. Fires at any stage
  when failures appear. If you are about to fix something without understanding
  why it broke, this skill applies.
metadata:
  version: "1.0.0"
  updated: "2026-03-09"
  origin: "Adapted from obra/superpowers (MIT). See LICENSE-UPSTREAM."
---
```

### Without metadata (constructed example — normative, not descriptive)

The convention permits omitting the `metadata` block entirely. No
existing skill currently does this, so the example below is **prescriptive**:
it shows a valid shape the convention permits, not a pattern observed in
the codebase. A new skill with no provenance, version, or attribution to
record may be authored as:

```yaml
---
name: example
description: >-
  Use when … (trigger condition for this skill).
---
```

## What not to include

Do not put any of the following in skill frontmatter:

- `requires`
- `accepts`
- `produces`
- `may_produce`
- `trigger`

These are runa's contract surface for runa-managed protocols. They live
in `manifest.toml` and nowhere else. Skills are not in runa's contract
at all — runa never sees a skill — so mirroring contract-shaped fields
into skill frontmatter creates a second surface that drifts from the
authoritative one. (See
[`docs/architecture/connecting-structure.md`](../architecture/connecting-structure.md#authoring-surfaces-and-authority)
for the full reasoning, including the historical drift case that
motivated removing these fields.)

## Cross-references

- [`docs/architecture/connecting-structure.md` — Authoring surfaces and authority](../architecture/connecting-structure.md#authoring-surfaces-and-authority): the architectural reasoning behind this convention.
- [`manifest.toml`](../../manifest.toml): the sole authoritative surface for runa contract declarations.
