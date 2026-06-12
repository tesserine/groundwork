# Releasing Groundwork

Audience: the release operator cutting a Groundwork release or release
candidate. This document assumes access to the repository, GitHub, and Python
3.11 or newer.

## Release Identity

Groundwork uses one repository tag for one methodology version. Tags are
`vX.Y.Z` for stable releases and `vX.Y.Z-rc.N` for release candidates. The
top-level `version = "X.Y.Z"` or `version = "X.Y.Z-rc.N"` field in
`manifest.toml` is the version-of-record established by commons ADR-0011.

Tag grammar follows commons ADR-0012 exactly: numeric identifiers do not allow
leading zeroes, release candidates start at `rc.1`, and alpha, beta, and build
metadata forms are outside this repo's release surface.

## Tooling Provenance

`scripts/release-check`, `scripts/release-cut`, and the `release_lib.py`
library behind them are groundwork-owned implementations of the shared
release ceremony — convention canonical in
[commons RELEASE.md](https://github.com/tesserine/commons/blob/main/RELEASE.md)
and ADR-0006/0011/0012. groundwork's implementation is a distinct Python
lineage; the bash siblings in agentd, base, commons, and runa share ancestry
([commons#21](https://github.com/tesserine/commons/issues/21)) but every
implementation is independently owned: no repo is the tooling upstream, and
fixes do not propagate automatically. Ownership details:
[base RELEASING.md § Release Tooling Ownership](https://github.com/tesserine/base/blob/main/RELEASING.md#release-tooling-ownership).

## Pre-Release Gate

A releasable commit is on `main`, up to date with `origin/main`, and has a
clean working tree. Before cutting a tag:

```sh
git checkout main
git fetch origin main
git merge --ff-only origin/main
git status --short
./scripts/release-check metadata
```

For a final tag-time identity check against source already rolled to a version:

```sh
./scripts/release-check release "vX.Y.Z"
```

Use `vX.Y.Z-rc.N` for release candidates.

## Atomic Release Operation

Command shape: `scripts/release-cut vX.Y.Z[-rc.N]`.

Stable releases use the repo-owned helper:

```sh
scripts/release-cut vX.Y.Z
```

Release candidates use the same helper:

```sh
scripts/release-cut vX.Y.Z-rc.N
```

The documented command updates `manifest.toml`, rolls `CHANGELOG.md`, commits
the release, creates an annotated tag, verifies the tag identity, and pushes
`main` plus the tag with one atomic git push.

## Post-Release Gate

The tag push runs `.github/workflows/release.yml`. That workflow verifies the
annotated tag, requires the tag target to be reachable from `main`, runs
`release-check release`, extracts release notes from `CHANGELOG.md`, and
publishes the GitHub Release.

Only `vX.Y.Z-rc.N` tags are published as GitHub prereleases.

Manual stable GitHub Release recovery, when needed after a workflow failure:

```sh
./scripts/release-check notes "vX.Y.Z" > /tmp/groundwork-release-notes.md
gh release create "vX.Y.Z" \
  --title "groundwork vX.Y.Z" \
  --notes-file /tmp/groundwork-release-notes.md \
  --verify-tag
```

Manual release-candidate recovery includes the prerelease flag:

```sh
./scripts/release-check notes "vX.Y.Z-rc.N" > /tmp/groundwork-release-notes.md
gh release create "vX.Y.Z-rc.N" \
  --title "groundwork vX.Y.Z-rc.N" \
  --notes-file /tmp/groundwork-release-notes.md \
  --verify-tag \
  --prerelease
```

## Failure Modes

If `release-cut` reports that the local tag already exists, it has not changed
source state; inspect or remove the local tag before rerunning. If
`release-cut` fails before the atomic push, fix the source issue and rerun the
command. If the atomic push fails, the helper removes the local tag it created
and resets the release commit so the remote branch and tag remain unchanged.

If a published tag points at source that violates the release identity checks
and no external consumers have used it, delete the tag locally and remotely and
rerun the release operation. If external consumers may have used it, leave the
bad tag in the public record and cut the next version.

If the GitHub Release workflow fails after the tag is valid, repair the
workflow or environment and create the GitHub Release from
`scripts/release-check notes`. Do not edit release notes by hand unless the
changelog section is also corrected in source.
