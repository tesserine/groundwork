---
name: acquire
description: >-
  Entry from an existing forge work-unit. Use to start scoped work from a work-unit
  reference that is already on the tracker (e.g. "define runa#14") when no
  work-unit artifact exists yet — acquisition reads the work-unit, freshens it
  against current substrate, and materializes the work-unit artifact that define
  then proceeds on. The mirror of decompose's create path: decompose creates the
  work-unit it delivers; acquire adopts the work-unit it is given, and creates no
  work-unit.
metadata:
  version: "2.0.0"
  updated: "2026-07-05"
---

# Acquire

The scoped pipeline activates on a `work-unit` artifact, but the live
planning surface is the forge tracker. Acquisition is the bridge for the
natural developer entry — "start on work-unit #N" — when that work-unit already
exists and no work-unit artifact does yet. It reads the work-unit and
materializes the work-unit artifact; `define` then proceeds unchanged on that
artifact through its existing contract.

Acquisition is **one-way**: the work-unit is the planning home, the artifact is
its execution-scoped snapshot, and `handle` is the back-link. Nothing here
writes artifact content back to the work-unit, and nothing here creates a
work-unit — acquisition *adopts* the work-unit it is given. An acquired work-unit
is indistinguishable downstream from a decomposed one: same `handle`, same
`work-unit-<N>-<short-slug>` instance-id convention.

This is a skill, not a protocol, because it runs when there is no artifact
state for a trigger to fire on. It belongs to whatever surface hosts a
work-unit delivery: a `decompose`-scoped session, where the `work-unit` MCP
tool is served, and the promised-entry session a targeted intent opens at
cold start.

## Steps

1. **Read the work-unit.** Invoke the connector capability `read-work-unit`
   operation exposed on runa's MCP surface:

   ```
   read-work-unit({ reference: "<tracker reference>" })
   ```

   The deployment-selected connector owns provider coordinates and
   credentials.
   The `read-work-unit` output includes an optional ordered `comments` log.
   It also includes the whole work-unit: `{handle, title, body, state}` plus the
   connector-issued `{ id, display }` identity.
   The body is the work-unit's spec; the comment log is its running record — review state, dispositions, and directives.
   Surface the log to the session as entry context so the session grounds on the whole work-unit, not the spec alone.

2. **Materialize the artifact body.** Pipe the read-work-unit output through
   the materializer:

   ```
   ... | python3 skills/acquire/scripts/materialize.py
   ```

   (Script path from the groundwork methodology root.)

   It derives the work-unit body — `title`, `description`, and
   `acceptance_criteria` from the work-unit content, `handle` carried through
   verbatim — and the `instance_id` (`work-unit-<sha256(handle.id)>`). The
   derivation never invents content (see step 3).
   The artifact materializes from the work-unit body alone.
   The comment log is read as entry context, never persisted into the artifact.
   The work-unit remains the planning home, and the artifact carries the spec.

3. **Surface gaps; never invent.** When the work-unit does not map cleanly onto
   the required schema fields — no extractable acceptance criteria, an empty
   body, or a work-unit that is not open — `materialize.py` exits non-zero with
   a named work-unit-quality defect. That is not an acquisition failure to
   work around: it is a defect in the work-unit at its planning home. Route it
   to `decompose`'s `refine-work-unit` discipline (improve the work-unit), then
   re-acquire. Do not hand-fill the missing fields here — that would forge an
   execution snapshot the planning home never authorized.

4. **Freshen the acquired work-unit.** A well-formed work-unit can still be
   *stale*: it was authored in another context at another time, and its body
   and its stated dependency edges are a claim about a past moment, not current
   ground — reality wins over the work-unit record, the need wins over the
   record. This is groundwork's one inherited-frame entry, so re-grounding is
   owed here, before `define` builds on the frame. Run the freshen pass over
   the acquired work-unit and choose exactly one disposition; the pass, the
   disposition set, and the freshen record it produces are detailed under
   [Freshening](#freshening) below. The pass has three moves in order: ground
   the body against current substrate, ground the dependency graph against live
   tracker state, then re-craft or dispose. Where grounding finds staleness or
   thinness, the body is re-crafted through `refine-work-unit` at its planning
   home rather than reimplemented here — freshening adds the staleness trigger
   and the dependency-graph re-verification, not a second re-craft engine. When
   grounding shows the substrate the unit rests on is itself defective, the
   finding escalates to `resolve` as a side quest rather than being absorbed
   into the unit — freshen repairs the unit, resolve repairs the substrate.
   Freshening fires at this single acquisition boundary in both session modes —
   mode is a property of the session (commons ADR-0015), not a fork in the
   pass.

5. **Deliver the `work-unit` artifact.** Only a `proceed-as-freshened`
   disposition may deliver the work-unit artifact; every other disposition ends
   acquisition without delivery, so `define` — whose sole trigger is the
   `work-unit` artifact — never fires on an unfreshened or withheld frame.
   Under `proceed-as-freshened`, invoke the `work-unit` MCP tool with the
   materializer's `instance_id` and `artifact` body — the same call shape
   `decompose` uses for a tracker-backed work-unit, with the work-unit's
   `handle` carried unchanged. `work-unit` is a planning-phase artifact: the
   agent supplies the schema fields and runa does not inject `work_unit`. Do
   not write the workspace JSON file directly; do not call `create-work-unit`.

   ```
   work-unit({
     instance_id: "work-unit-<sha256-handle-id>",
     title: "<from the work-unit>",
     description: "<from the work-unit>",
     acceptance_criteria: ["<from the work-unit>"],
     handle: { id: "<connector-issued work-unit identity>", display: "<human-readable work-unit identity>" }
   })
   ```

   Runa validates the body against the `work-unit` schema, persists it, and
   records it. The cascade then computes `define` as the next station on the
   acquired artifact.

6. **Hand off to `define`.** Acquisition materializes; `define` claims. Tracker
   claiming (assigning the work-unit, marking it in progress) is `define`'s
   workspace-preparation step, not acquisition's — keep the one-way boundary
   clean.

## Freshening

Freshening re-grounds an acquired work-unit against current substrate at the
acquisition boundary and yields exactly one typed disposition. The discipline
is groundwork's native re-derivation of the `freshen-work-unit` station skill:
the transferable invariants are the pass shape, the typed disposition, and the
freshen record. It composes existing assets at their homes — `reckon` supplies
the re-grounding reasoning, `refine-work-unit` the body re-craft, the `spike`
work-unit the reframe home, `resolve` the defective-substrate escalation — and
builds on the comment log this skill already surfaces, adding no second
log-surfacing.

**The pass.** Ground the body against the current substrate the work-unit's
acceptance criteria cite; ground the dependency graph against live tracker
state; then choose one disposition and record it. The disposition is chosen
*before* any re-craft.

**The disposition set and where each unit goes.** The `disposition` value is
one member of the set declared in `schemas/freshen-record.schema.json` — the
single home of the set. Only `proceed-as-freshened` admits the unit to
`define`; every other disposition withholds it, the way the
committed-but-unspecced gate withholds an unspecced unit.

| Disposition | Admits to `define`? | Onward route |
| --- | --- | --- |
| `proceed-as-freshened` | yes | delivered to `define` through step 5 |
| `close` | no | closed at the tracker; the need is gone or already met |
| `split` | no | routed to `decompose`'s `refine-work-unit`, then re-acquired |
| `relink` | no | re-linked or merged at the tracker, then re-acquired or closed |
| `reblock` | no | blocking edges recorded at the tracker; the unit waits, unmaterialized |
| `reframe-as-spike` | no | filed as a `spike` work-unit per `work-unit-craft` |

**The freshen record.** Every acquisition from an existing work-unit attaches a
freshen record — validated against `schemas/freshen-record.schema.json` and
posted as a comment on the work-unit, a log entry in the running record, not
written into the work-unit body. It carries four required elements: the
`grounded_against` substrate state (commit, when, and the tracker state the
graph was verified against), the `staleness_finding` (what was stale or thin
and what changed, or that grounding found the body current), the `graph_finding`
(below), and the `disposition`.

**The graph finding covers the whole graph, not only the body.** The
`graph_finding` re-verifies each stated edge against current tracker state, one
finding per facet: `blockers`, `blocked`, `epic_membership`, `siblings`,
`milestone`, `labels`. A finding that addresses only body staleness does not
satisfy the record — the schema's `graph_finding` object requires all six
facets.

**Proceed re-craft.** Under `proceed-as-freshened`, where grounding found
staleness or thinness the body is re-crafted through `refine-work-unit` at the
planning home — which re-applies `work-unit-craft`'s contract-input pass — and
re-materialized, so the body `define` receives is a standalone spec verifiable
against current substrate, not a stale body wearing a freshened annotation.

## Corruption Modes

- `log-blindness`: handing off to `define` with the work-unit's comment log
  unread and unsurfaced. The snapshot carries the running record so the
  session grounds on the whole work-unit; an entry that reads the spec alone
  executes blind to its own live corrections.
- `freshen-skipped`: handing off to `define` without running the freshen pass
  and recording a disposition. An acquired frame is inherited, not reckoned;
  skipping the pass carries a stale body and stale edges into the pipeline with
  perfect fidelity.
- `work-unit-creation`: calling `create-work-unit` during acquisition. Acquisition
  adopts an existing work-unit; creating one is `decompose`'s path, and doing
  both makes a second work-unit for the same work.
- `content-fabrication`: hand-filling acceptance criteria or a description
  the work-unit does not contain, instead of routing the gap to refinement. The
  artifact must be a faithful snapshot of the planning home.
- `write-back`: editing the work-unit artifact from acquisition (beyond a freshen
  re-craft at the planning home and `define`'s later claim). Derivation is
  one-way: freshening repairs the work-unit at its planning home through
  `refine-work-unit`, never the materialized artifact.
- `handle-drift`: re-deriving or altering the `handle` instead of carrying
  the work-unit's identity through verbatim — breaks the back-link and risks a
  downstream identity collision.

## Cross-References

- `decompose` (protocol): the create path acquisition mirrors, and the home
  of `refine-work-unit` — where a work-unit-quality gap surfaced here is fixed,
  and where a freshen `proceed-as-freshened` re-craft is performed.
- `define` (protocol): proceeds on the acquired artifact through its existing
  contract; owns tracker claiming. Its sole trigger is the `work-unit` artifact,
  so withholding delivery under a non-proceed disposition structurally withholds
  the unit from the scoped pipeline.
- `resolve` (skill): the defective-substrate escalation when freshening finds
  the substrate the unit rests on is itself defective.
- `read-work-unit` (connector capability operation): emits
  `{handle, title, body, state}` and, per forge-capability `2.0.0`, the
  optional ordered `comments` log for the selected connector.
- `schemas/freshen-record.schema.json`: the single home of the freshen
  disposition set, the record's required elements, and the graph-facet list.
