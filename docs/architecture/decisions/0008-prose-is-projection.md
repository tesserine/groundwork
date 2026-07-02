# ADR-0008: Prose Is Projection

**Status:** Proposed — delivered for operator review with groundwork#504 \
**Date:** 2026-07-02

## Context

Groundwork's identity is enforced, not exhorted: every belief traces to its
enforcing file. Runa injects each `PROTOCOL.md` whole as the per-tick
instruction, so protocol prose is executed surface, not commentary — a prose
defect is delivered into every run.

The manifest, the artifact schemas, and the workflow contracts are the
enforced substrate, but prose surfaces had no stated relation to it, and
structural claims stood in prose with nothing binding them. At the pipeline's
front door, the survey protocol's §Requirements Structure documented nine
fields that `schemas/requirements.schema.json` — `additionalProperties:
false` — forbids on any valid instance: an impossible artifact described in
the very prompt that instructs its production, and no check could see it.
groundwork#503 catalogues the wider class this instance belongs to.

## Decision

**Prose is projection.** `manifest.toml`, `schemas/`, and
`workflow-contracts/` are the single home of every structural fact — artifact
shapes, protocol edges, triggers, mechanics, dispositions. Every prose
surface does exactly one of three things with a structural fact:

- **consults** the home, by link or path;
- is a **gate-bound rendering** of it — prose whose agreement with the home a
  committed check verifies by consulting the home itself; or
- carries only what the substrate cannot carry — judgment, discipline,
  corruption recognition, rationale.

A structural claim standing in prose with no binding gate is a defect of the
class this methodology exists to close: discipline held by memory instead of
enforced substrate.

Three consequences, each traced to its enforcing file:

1. **Protocol artifact prose is conformance-gated to the owning schema.**
   Every field a `PROTOCOL.md` attributes to an artifact — a key in a fenced
   delivery-call block, a backticked `###` field heading — exists in that
   artifact type's schema, modulo the documented tool-parameter/injection
   envelope (`instance_id`, runtime-injected `work_unit`). Enforced by
   `tooling/protocol_prose.py`, exercised over the live tree by
   `tests/test_protocol_prose_conformance.py` in the CI conformance job
   (`.github/workflows/conformance.yml`). The gate consults the live schemas:
   a schema change flips it without the gate being edited.
2. **Runtime and deployment wiring state lives outside methodology prose.** A
   protocol states the methodology's own seam — what it delivers, to which
   tool, under which envelope — and stops; which runtime commands are wired,
   installed, or pending belongs to the runtime's own repository and tracker.
   Enforced at the installed-surface boundary by
   `tests/test_protocol_artifact_delivery_docs.py` (the
   interactive-adapter-bypass and injection-contract pins).
3. **Architecture prose carries rationale; structural renderings live in
   their substrate homes.** `manifest.toml`, `schemas/`, and
   `workflow-contracts/` hold the structure, validated by
   `tooling/conformance.py`; an architecture document links to those homes
   and carries the why. A hand-maintained manifest copy, edge list, or schema
   rendering in prose is a second editable home.

## Consequences

- **A methodology author classifies a structural sentence before writing
  it.** Is the fact held by the manifest, a schema, or a workflow contract?
  State it in that home; prose consults it. Is it runtime wiring state? It
  belongs to the runtime's repository, not here. Is it judgment, discipline,
  or rationale? Prose owns it. Is it a rendering that must appear in prose —
  a delivery example, a field walk-through? Write it in a form a committed
  gate binds to the home (delivery-call blocks and backticked `###` field
  headings are bound per consequence 1); a rendering no gate binds does not
  enter prose.
- A schema evolution needs no coordinated prose sweep to stay honest: any
  protocol prose the change strands turns red in CI, at the file and line
  that must move.
- The `take`, `decompose`, and `connecting-structure` surfaces are brought
  under this decision by groundwork#503's remaining units; this ADR is the
  record they trace to.
