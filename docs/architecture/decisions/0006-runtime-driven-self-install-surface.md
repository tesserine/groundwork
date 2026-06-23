# ADR-0006: Runtime-Driven Self-Install Surface

**Status:** Proposed — delivered for operator review \
**Date:** 2026-06-12 \
**Traces to:** [#416](https://github.com/tesserine/groundwork/issues/416)
(the self-install), [#415](https://github.com/tesserine/groundwork/issues/415)
(legacy retirement decision), first consumer
[pentaxis93/babbie-ops#65](https://github.com/pentaxis93/babbie-ops/issues/65).

## Context

In a runtime-driven deployment, a protocol runtime executes the
methodology through the methodology interface contract: each protocol's
instruction content and validated inputs arrive at execution time through
the runtime's session surface. The legacy installer
(`scripts/groundwork-install`) predates that channel — it projects
`protocols/*/PROTOCOL.md` documents as skills so a bare agent session can
run them. In a runtime-driven deployment that projection installs a
second, drifting copy of content the runtime already delivers
authoritatively.

What the contract channel does *not* deliver still needs installing:
skills (agent-invoked by judgment, never runtime-delivered), the
methodology runtime the forge steps execute through, and the resolved
principles corpus.

## Decision

One idempotent, groundwork-owned, host- and runtime-agnostic installer:
`scripts/install` (logic in `tooling/install.py`, stdlib-only). It owns
exactly three surfaces and carries no projection machinery:

1. **Skills, verbatim.** Every `skills/<name>/` carrying a `SKILL.md`
   installs unmodified into `~/.claude/skills/<name>` and
   `~/.agents/skills/<name>`, enumerated from the tree at the source
   commit. No transformation of any shipped file; the only added file is
   the ownership marker.
2. **The methodology runtime.** `~/.groundwork` with `manifest.toml` and
   `mechanics/`.
3. **The principles corpus.** The corpus source is an operator input
   (`--corpus-git URL [--corpus-ref REF]` | `--corpus-path PATH` |
   `--corpus-embedded` — ADR-0005's discriminated union as flags). The
   installer records the input into the deployment-owned
   `${XDG_CONFIG_HOME:-~/.config}/groundwork/principles.toml` and
   materializes the resolved corpus at `~/.groundwork/principles` through
   the existing resolution layer. Absent the input, an existing config is
   honored; absent both, the embedded default resolves.

### Naming

The tool is `scripts/install`, not a prefixed variant: it is invoked by
checkout path, never placed on `PATH`, so it cannot collide with
coreutils `install` or shadow the legacy `groundwork-install` during the
coexistence window — and once the legacy script retires (#415) it reads
as exactly what it is, the repo's installer.

### Ownership identity is disjoint from the legacy installer

Markers are `.groundwork-managed` with
`managed-by=groundwork scripts/install`; state lives at
`${XDG_STATE_HOME:-~/.local/state}/groundwork/install.tsv`. The legacy
installer's identity (`.groundwork-install`,
`groundwork-install/interactive-install.tsv`) is never read as our own.
Entries the legacy installer placed are **named conflicts directing the
operator to `scripts/groundwork-install uninstall`**, never adopted:
adoption would transfer ownership of content this installer did not
write — including protocol projections it must never manage.

### Convergence and failure semantics

- Re-running converges with exit 0 and leaves every managed inode
  untouched (compare-before-swap on all three surfaces, including the
  recorded config and the state file).
- An entry installed previously but no longer shipped is removed; removal
  is gated on this installer's own marker, and a missing marker at a
  deletion boundary fails loudly with state intact.
- Pre-existing unmanaged state fails loudly with a named path before any
  target is touched.
- The corpus is staged (including the remote fetch) before any target
  mutation, so an unreachable remote aborts a run with nothing changed,
  and resolution-layer errors surface unmodified.
- The source must be a clean checkout root; content derives from `HEAD`
  and the recorded `source-sha` is the trace. There is no pinned-ref
  gate: deployment recipes pin the ref they clone, and forcing detachment
  here adds ceremony without traceability gain.
- Uninstall removes only marker-verified managed entries and the runtime
  root; the deployment-owned `principles.toml` is recorded into, never
  deleted.

## Consequences

### Good

- Runtime-driven deployments compose one upstream installer with their
  own inputs (babbie-ops#65) instead of re-implementing install
  knowledge; no protocol content is ever installed for agent discovery,
  so nothing drifts against the contract channel.
- The legacy installer's retirement (#415) reduces to deleting the
  projection machinery — its legitimate jobs live here, in Python, with
  the corpus layer imported rather than subprocessed.

### Neutral

- Two installers coexist until #415 lands; disjoint marker and state
  namespaces plus the directed-conflict message make the boundary
  explicit at every collision point.

### Bad

- A deployment migrating from the legacy installer must run its
  uninstall first; the conflict message names that step, but it is a
  manual step.
