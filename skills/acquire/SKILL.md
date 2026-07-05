---
name: acquire
description: >-
  Entry from an existing forge work-unit. Use to start scoped work from a work-unit
  reference that is already on the tracker (e.g. "define runa#14") when no
  work-unit artifact exists yet — acquisition reads the work-unit and
  materializes the work-unit artifact that define then proceeds on. The mirror
  of decompose's create path: decompose creates the work-unit it delivers;
  acquire adopts the work-unit it is given, and creates no work-unit.
metadata:
  version: "1.1.0"
  updated: "2026-07-02"
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

4. **Deliver the `work-unit` artifact.** Invoke the `work-unit` MCP tool with
   the materializer's `instance_id` and `artifact` body — the same call shape
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

5. **Hand off to `define`.** Acquisition materializes; `define` claims. Tracker
   claiming (assigning the work-unit, marking it in progress) is `define`'s
   workspace-preparation step, not acquisition's — keep the one-way boundary
   clean.

## Corruption Modes

- `log-blindness`: handing off to `define` with the work-unit's comment log
  unread and unsurfaced. The snapshot carries the running record so the
  session grounds on the whole work-unit; an entry that reads the spec alone
  executes blind to its own live corrections.
- `work-unit-creation`: calling `create-work-unit` during acquisition. Acquisition
  adopts an existing work-unit; creating one is `decompose`'s path, and doing
  both makes a second work-unit for the same work.
- `content-fabrication`: hand-filling acceptance criteria or a description
  the work-unit does not contain, instead of routing the gap to refinement. The
  artifact must be a faithful snapshot of the planning home.
- `write-back`: editing the work-unit from acquisition (beyond `define`'s later
  claim). Derivation is one-way.
- `handle-drift`: re-deriving or altering the `handle` instead of carrying
  the work-unit's identity through verbatim — breaks the back-link and risks a
  downstream identity collision.

## Cross-References

- `decompose` (protocol): the create path acquisition mirrors, and the home
  of `refine-work-unit` — where a work-unit-quality gap surfaced here is fixed.
- `define` (protocol): proceeds on the acquired artifact through its existing
  contract; owns tracker claiming.
- `read-work-unit` (connector capability operation): emits
  `{handle, title, body, state}` and, per forge-capability `2.0.0`, the
  optional ordered `comments` log for the selected connector.
