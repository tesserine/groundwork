---
name: acquire
description: >-
  Entry from an existing forge ticket. Use to start scoped work from a ticket
  reference that is already on the tracker (e.g. "define runa#14") when no
  work-unit artifact exists yet — acquisition reads the ticket and
  materializes the work-unit artifact that define then proceeds on. The mirror
  of decompose's create path: decompose creates the ticket it delivers;
  acquire adopts the ticket it is given, and creates no ticket.
metadata:
  version: "2.0.0"
  updated: "2026-07-05"
---

# Acquire

The scoped pipeline activates on a `work-unit` artifact, but the live
planning surface is the forge tracker. Acquisition is the bridge for the
natural developer entry — "start on ticket #N" — when that ticket already
exists and no work-unit artifact does yet. It reads the ticket and
materializes the work-unit artifact. Before the artifact is delivered,
acquisition freshens the inherited frame against current substrate and chooses
one typed disposition; only a `proceed-as-freshened` disposition lets `define`
proceed on the artifact through its existing contract.

Acquisition is **one-way**: the ticket is the planning home, the artifact is
its execution-scoped snapshot, and `handle` is the back-link. Freshening may
repair the ticket body at the planning home before delivery, then re-materialize
from that source; it never writes artifact content back into the ticket body,
and it never creates a ticket. Acquisition *adopts* the ticket it is given. An
acquired work-unit is indistinguishable downstream from a decomposed one: same
`handle`, same `work-unit-<N>-<short-slug>` instance-id convention.

This is a skill, not a protocol, because it runs when there is no artifact
state for a trigger to fire on. It belongs to whatever surface hosts a
work-unit delivery: a `decompose`-scoped session, where the `work-unit` MCP
tool is served, and the promised-entry session a targeted intent opens at
cold start.

## Steps

1. **Read the ticket.** Invoke the connector capability `read-ticket`
   operation exposed on runa's MCP surface:

   ```
   read-ticket({ reference: "<tracker reference>" })
   ```

   The deployment-selected connector owns provider coordinates and
   credentials.
   The `read-ticket` output includes an optional ordered `comments` log.
   It also includes the whole ticket: `{handle, title, body, state}` plus the
   connector-issued `{ id, display }` identity.
   The body is the work-unit's spec; the comment log is its running record — review state, dispositions, and directives.
   Surface the log to the session as entry context so the session grounds on the whole ticket, not the spec alone.

2. **Materialize the artifact body.** Pipe the read-ticket output through
   the materializer:

   ```
   ... | python3 skills/acquire/scripts/materialize.py
   ```

   (Script path from the groundwork methodology root.)

   It derives the work-unit body — `title`, `description`, and
   `acceptance_criteria` from the ticket content, `handle` carried through
   verbatim — and the `instance_id` (`work-unit-<sha256(handle.id)>`). The
   derivation never invents content (see step 3).
   The artifact materializes from the ticket body alone.
   The comment log is read as entry context, never persisted into the artifact.
   The ticket remains the planning home, and the artifact carries the spec.

3. **Surface gaps; never invent.** When the ticket does not map cleanly onto
   the required schema fields — no extractable acceptance criteria, an empty
   body, or a ticket that is not open — `materialize.py` exits non-zero with
   a named work-unit-quality defect. That is not an acquisition failure to
   work around: it is a defect in the ticket at its planning home. Route it
   to `decompose`'s `refine-work-unit` discipline (improve the ticket), then
   re-acquire. Do not hand-fill the missing fields here — that would forge an
   execution snapshot the planning home never authorized.

4. **Freshen the acquired work-unit.**
   The materialized artifact is held until the freshen pass completes. This is
   the single acquisition boundary shared by autonomous and interactive
   sessions; session mode is a property of the session, not a second acquisition path
   ([commons ADR-0015](https://github.com/tesserine/commons/blob/main/adr/0015-mode-is-a-property-of-the-session.md)).

   Run the pass before `define` claims the ticket:

   1. Ground the ticket body against the current tree at the current base commit:
      verify identifiers, paths, behaviors, and acceptance criteria against
      current substrate, using the already-surfaced comment log for staleness
      and directive context.
   2. Ground the dependency graph against live tracker state: verify blockers,
      blocked units, epic membership, siblings, milestone, and labels.
   3. Re-reckon the frame by consulting [reckon](../reckon/SKILL.md): trace the
      inherited frame to the current need it must serve.
   4. Choose exactly one typed disposition from the routing table below before
      any re-craft.
   5. When proceeding after staleness or thinness, re-craft the ticket body at
      the planning home by consulting [work-unit-craft](../work-unit-craft/SKILL.md),
      then re-run `skills/acquire/scripts/materialize.py` on the freshened body
      so the delivered artifact is a faithful snapshot of a standalone,
      currently-verifiable spec. When grounding finds the body current, proceed
      without re-craft.
   6. Validate the freshen record against the
      [freshen-record schema](../../schemas/freshen-record.schema.json). The
      record is posted to the ticket as a comment before the disposition takes
      effect.

   A defective substrate finding escalates to [resolve](../resolve/SKILL.md) as
   a side quest: freshen repairs the unit, resolve repairs the substrate.

### Freshen routing table

| Disposition | Consequence | Onward route |
|-------------|-------------|--------------|
| proceed-as-freshened | Artifact delivery admits the unit to define. | Deliver the re-materialized work-unit artifact. |
| close | Acquisition ends without artifact delivery. | Close the tracker ticket with the freshen record as the rationale. |
| split | Acquisition ends without artifact delivery. | Route to `decompose`'s `refine-work-unit` discipline to split the ticket, then acquire the resulting ready unit. |
| relink | Acquisition ends without artifact delivery. | Repair tracker links or merge the duplicate, then re-acquire or close. |
| reblock | Acquisition ends without artifact delivery. | Record the blocking edges in the tracker and leave the unit waiting unmaterialized. |
| reframe-as-spike | Acquisition ends without artifact delivery. | File a spike work-unit using [work-unit-craft](../work-unit-craft/SKILL.md)'s spike form. |

### Graph facets

| Facet | Finding required |
|-------|------------------|
| blockers | State of work-units blocking this unit. |
| blocked | State of work-units this unit blocks. |
| epic_membership | Current parent epic membership or confirmed absence. |
| siblings | Current sibling, duplicate, or absorbed-scope state. |
| milestone | Current milestone assignment and currency, or confirmed absence. |
| labels | Current label accuracy. |

### Freshen record contract

| Element | Meaning |
|---------|---------|
| work_unit | The acquired work-unit identity the record threads to. |
| grounded_against | The commit, grounding timestamp, and tracker state consulted. |
| staleness_finding | What was stale or thin and what changed, or that the body is current. |
| graph_finding | Present finding for every dependency-graph facet above. |
| disposition | The single typed disposition selected by the pass. |

   The freshen record is a positive log entry in the running record acquire
   already reads. It is never written into the work-unit body; the freshened
   unit's body carries only the re-crafted spec.

5. **Deliver the `work-unit` artifact.**
   Deliver the work-unit artifact only under a recorded `proceed-as-freshened` disposition.
   Invoke the `work-unit` MCP tool with the materializer's `instance_id` and
   `artifact` body — the same call shape
   `decompose` uses for a tracker-backed work-unit, with the ticket's
   `handle` carried unchanged. `work-unit` is a planning-phase artifact: the
   agent supplies the schema fields and runa does not inject `work_unit`. Do
   not write the workspace JSON file directly; do not call `create-ticket`.

   ```
   work-unit({
     instance_id: "work-unit-<sha256-handle-id>",
     title: "<from the ticket>",
     description: "<from the ticket>",
     acceptance_criteria: ["<from the ticket>"],
     handle: { id: "<connector-issued ticket identity>", display: "<human-readable ticket identity>" }
   })
   ```

   Runa validates the body against the `work-unit` schema, persists it, and
   records it. The cascade then computes `define` as the next station on the
   acquired artifact.

6. **Hand off to `define`.** Acquisition freshens and materializes only when the
   disposition proceeds; `define` claims. Tracker claiming (assigning the
   ticket, marking it in progress) is `define`'s workspace-preparation step,
   not acquisition's — keep the one-way boundary clean.

## Corruption Modes

- `log-blindness`: handing off to `define` with the ticket's comment log
  unread and unsurfaced. The snapshot carries the running record so the
  session grounds on the whole ticket; an entry that reads the spec alone
  executes blind to its own live corrections.
- `ticket-creation`: calling `create-ticket` during acquisition. Acquisition
  adopts an existing ticket; creating one is `decompose`'s path, and doing
  both makes a second ticket for the same work.
- `content-fabrication`: hand-filling acceptance criteria or a description
  the ticket does not contain, instead of routing the gap to refinement. The
  artifact must be a faithful snapshot of the planning home.
- `stale-acquisition`: delivering an acquired work-unit after materialization
  without grounding its body and dependency graph against current substrate.
- `write-back`: editing the ticket from artifact content, or editing anything
  beyond planning-home repair authorized by freshening or `refine-work-unit`.
  Derivation is one-way: ticket body to artifact body.
- `handle-drift`: re-deriving or altering the `handle` instead of carrying
  the ticket's identity through verbatim — breaks the back-link and risks a
  downstream identity collision.

## Cross-References

- `decompose` (protocol): the create path acquisition mirrors, and the home
  of `refine-work-unit` — where a ticket-quality gap surfaced here is fixed.
- `define` (protocol): proceeds on the acquired artifact through its existing
  contract; owns tracker claiming.
- `schemas/freshen-record.schema.json`: the single home for the freshen record
  fields, dependency-graph facets, and typed disposition set.
- `read-ticket` (connector capability operation): emits
  `{handle, title, body, state}` and, per forge-capability `1.2.0`, the
  optional ordered `comments` log for the selected connector.
