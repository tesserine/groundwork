---
name: acquire
description: >-
  Entry from an existing forge ticket. Use to start scoped work from a ticket
  reference that is already on the tracker (e.g. "take runa#14") when no
  work-unit artifact exists yet — acquisition reads the ticket and
  materializes the work-unit artifact that take then proceeds on. The mirror
  of decompose's create path: decompose creates the ticket it delivers;
  acquire adopts the ticket it is given, and creates no ticket.
metadata:
  version: "1.1.0"
  updated: "2026-07-02"
---

# Acquire

The scoped pipeline activates on a `work-unit` artifact, but the live
planning surface is the forge tracker. Acquisition is the bridge for the
natural developer entry — "start on ticket #N" — when that ticket already
exists and no work-unit artifact does yet. It reads the ticket and
materializes the work-unit artifact; `take` then proceeds unchanged on that
artifact through its existing contract.

Acquisition is **one-way**: the ticket is the planning home, the artifact is
its execution-scoped snapshot, and `handle` is the back-link. Nothing here
writes artifact content back to the ticket, and nothing here creates a
ticket — acquisition *adopts* the ticket it is given. An acquired work-unit
is indistinguishable downstream from a decomposed one: same `handle`, same
`work-unit-<N>-<short-slug>` instance-id convention.

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
   credentials. Groundwork receives the whole ticket:
   `{handle, title, body, state}` plus, per forge-capability `1.2.0`, an
   optional ordered `comments` log — `handle` is the connector-issued
   `{ id, display }` identity. The body is the work-unit's spec; the
   comment log is its running record — review state, dispositions, and
   directives. Surface the log to the session as entry context so the
   session grounds on the whole ticket, not the spec alone.

2. **Materialize the artifact body.** Pipe the read-ticket output through
   the materializer:

   ```
   ... | python3 skills/acquire/scripts/materialize.py
   ```

   (Script path from the groundwork methodology root.)

   It derives the work-unit body — `title`, `description`, and
   `acceptance_criteria` from the ticket content, `handle` carried through
   verbatim — and the `instance_id` (`work-unit-<sha256(handle.id)>`). The
   derivation never invents content (see step 3). The artifact
   materializes from the ticket body alone: the comment log is read as
   entry context, never persisted into the artifact — the ticket remains
   the planning home, and the artifact carries the spec.

3. **Surface gaps; never invent.** When the ticket does not map cleanly onto
   the required schema fields — no extractable acceptance criteria, an empty
   body, or a ticket that is not open — `materialize.py` exits non-zero with
   a named work-unit-quality defect. That is not an acquisition failure to
   work around: it is a defect in the ticket at its planning home. Route it
   to `decompose`'s `refine-work-unit` discipline (improve the ticket), then
   re-acquire. Do not hand-fill the missing fields here — that would forge an
   execution snapshot the planning home never authorized.

4. **Deliver the `work-unit` artifact.** Invoke the `work-unit` MCP tool with
   the materializer's `instance_id` and `artifact` body — the same call shape
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
   records it. The cascade then computes `take` as the next station on the
   acquired artifact.

5. **Hand off to `take`.** Acquisition materializes; `take` claims. Tracker
   claiming (assigning the ticket, marking it in progress) is `take`'s
   workspace-preparation step, not acquisition's — keep the one-way boundary
   clean.

## Corruption Modes

- `log-blindness`: handing off to `take` with the ticket's comment log
  unread and unsurfaced. The snapshot carries the running record so the
  session grounds on the whole ticket; an entry that reads the spec alone
  executes blind to its own live corrections.
- `ticket-creation`: calling `create-ticket` during acquisition. Acquisition
  adopts an existing ticket; creating one is `decompose`'s path, and doing
  both makes a second ticket for the same work.
- `content-fabrication`: hand-filling acceptance criteria or a description
  the ticket does not contain, instead of routing the gap to refinement. The
  artifact must be a faithful snapshot of the planning home.
- `write-back`: editing the ticket from acquisition (beyond `take`'s later
  claim). Derivation is one-way.
- `handle-drift`: re-deriving or altering the `handle` instead of carrying
  the ticket's identity through verbatim — breaks the back-link and risks a
  downstream identity collision.

## Cross-References

- `decompose` (protocol): the create path acquisition mirrors, and the home
  of `refine-work-unit` — where a ticket-quality gap surfaced here is fixed.
- `take` (protocol): proceeds on the acquired artifact through its existing
  contract; owns tracker claiming.
- `read-ticket` (connector capability operation): emits
  `{handle, title, body, state}` and, per forge-capability `1.2.0`, the
  optional ordered `comments` log for the selected connector.
