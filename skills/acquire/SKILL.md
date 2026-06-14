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
  version: "1.0.0"
  updated: "2026-06-11"
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
work-unit delivery: today, a `decompose`-scoped session (the `work-unit`
MCP tool is served there); under the cold-start runtime entrypoint
([tesserine/runa#188](https://github.com/tesserine/runa/issues/188)), the
session that entrypoint opens.

## Steps

1. **Read the ticket.** Resolve the invariant `read-ticket` operation
   through `groundwork-mechanic` and run the active-forge mechanic it
   returns:

   ```
   groundwork-mechanic run read-ticket --tracker <selector> ticket_number=<N> [--secret-env token=<ENV>]
   ```

   Tracker coordinates come from runa's `RUNA_PROJECT_FORGE_ADDRESSES`
   payload and the selected configured tracker — do not pass owner, name,
   host, repository, endpoint URL, or tracker identity as bindings. The
   mechanic emits `{handle, title, body, state}` for either forge.

2. **Materialize the artifact body.** Pipe the read-ticket output through
   the materializer:

   ```
   ... | python3 skills/acquire/scripts/materialize.py
   ```

   (Script path from the groundwork methodology root.)

   It derives the work-unit body — `title`, `description`, and
   `acceptance_criteria` from the ticket content, `handle` carried through
   verbatim — and the `instance_id` (`work-unit-<N>-<short-slug>`). The
   derivation never invents content (see step 3).

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
     instance_id: "work-unit-<N>-<short-slug>",
     title: "<from the ticket>",
     description: "<from the ticket>",
     acceptance_criteria: ["<from the ticket>"],
     handle: { forge_tag: "<github|sourcehut>", "...": "<ticket identity>" }
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
- `read-ticket` (mechanic): the forge read acquisition resolves through
  `groundwork-mechanic`; emits `{handle, title, body, state}` for both forges.
