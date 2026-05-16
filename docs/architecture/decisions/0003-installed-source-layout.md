# ADR-0003: Installed Source Layout

**Status:** Provisional \
**Date:** 2026-05-16

## Context

`scripts/groundwork-sync install` creates discovery entries for interactive
agents under Claude Code and Codex skill directories. Skills already have the
runtime filename those agents expect: `SKILL.md`. Protocols use
`PROTOCOL.md`, so install must expose them through a skill-shaped directory
without changing their source authoring format.

The first implementation snapshotted only `skills/` and `protocols/`, then
copied each protocol into a separate projection directory with
`PROTOCOL.md` renamed to `SKILL.md`. That made top-level discovery work, but
it changed the filesystem position of the protocol instructions. Relative
links from installed protocols could no longer resolve to repo-level docs,
schemas, skills, the manifest, or other committed source files.

## Decision

Installed state mirrors the committed source tree. The snapshot at
`snapshots/<commit>/source/` contains the tracked repo files from the pinned
commit. Protocol directories receive one generated file inside that source
shape: `SKILL.md`, copied from the adjacent `PROTOCOL.md`.

Discovery entries under `.claude/skills/` and `.agents/skills/` symlink to
directories inside that source-shaped snapshot:

- Skills target `snapshots/<commit>/source/skills/<name>/`.
- Protocols target `snapshots/<commit>/source/protocols/<name>/`.

There is no separate projection tree. Any relative path from an installed
protocol or skill instruction file must resolve to the same committed content
as it would from the source checkout.

This ADR continues the existing `docs/architecture/decisions/000N-*.md`
series and the status/date header shape used by ADR-0001 and ADR-0002. It
introduces no new ADR convention.

## Consequences

### Good

- Installed instructions share the source checkout's coordinate system.
- Future relative links to docs, schemas, skills, protocols, or top-level
  files do not require installer-specific inclusion rules.
- Discovery still satisfies agents that require a real `SKILL.md` inside a
  symlinked directory.
- The ownership state file remains a record of managed discovery symlinks
  rather than a schema for snapshot internals.

### Neutral

- Snapshots include tracked files beyond the currently discovered skills and
  protocols.
- Generated protocol `SKILL.md` files exist only in installed snapshots, not in
  the source checkout.

### Bad

- Snapshot size grows with the tracked repository instead of only the active
  methodology directories.
