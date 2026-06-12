# The Principles Corpus

Reckon reasons from navigational principles — first principles selected
during Orient and reasoned FROM during Reconstruct. The corpus those
principles are selected from is not hard-coded into any skill: it resolves
through methodology configuration. This document specifies the
configuration surface.

## Two concepts, kept distinct

- **The configured source** — where the corpus comes from. Declared in a
  deployment-owned config file (below). One of: the embedded default
  shipped in this repository, a local directory, or a remote git
  repository.
- **The resolved local corpus** — the local content reckon actually reads
  during reasoning. The resolution layer materializes the configured
  source into this location at setup time; reckon never live-fetches a
  remote mid-reckon. In an installed deployment the resolved corpus lives
  at `~/.groundwork/principles/`; in a standalone checkout the embedded
  default at `principles/` is already local.

## The ordinary path: zero configuration

With no configuration present, the corpus is the minimal embedded default
shipped in-tree at `principles/`. No config file, no network, no setup
beyond the checkout itself. An empty config file, or one without a
`[corpus]` table, selects the same default — absence of configuration is
the first-class ordinary path, not an error path.

The embedded default is a short, standalone, near-universal corpus. It is
the fallback/default for standalone use — not the canonical authority for
the Tesserine ecosystem, and not a digest of any external corpus.

## The power-user path: configuring a corpus

The config file is deployment-owned and lives outside the methodology
tree at:

```
${XDG_CONFIG_HOME:-~/.config}/groundwork/principles.toml
```

It declares a single `[corpus]` table discriminated by `source`:

```toml
# The embedded default, stated explicitly (same as no file at all):
[corpus]
source = "embedded"
```

```toml
# A corpus already on the local filesystem (absolute path required):
[corpus]
source = "path"
path = "/srv/corpora/our-principles"
```

```toml
# A remote git repository, fetched once at setup — for example, the
# canonical corpus Tesserine's own deployments configure:
[corpus]
source = "git"
url = "https://github.com/pentaxis93/principles"
ref = "main"   # optional; the repository's default branch when absent
```

The shape is schema-validated
([`schemas/principles-config.schema.json`](../schemas/principles-config.schema.json));
parsing and validation live in
[`tooling/principles_config.py`](../tooling/principles_config.py). A
present-but-invalid configuration fails loudly with named errors — it
never silently degrades to the default. (The operational validator is
stdlib-only so resolution runs in deployments without third-party
packages; the JSON Schema is the documentation and conformance contract,
and CI holds the two in agreement.)

## Materialization: when, where, how to refresh

Resolution is performed by
[`tooling/corpus_resolution.py`](../tooling/corpus_resolution.py), wired
into [`scripts/groundwork-install`](../scripts/groundwork-install):

- **When:** at install/setup — every `groundwork-install install` or
  `sync` run. Never during reasoning: no code path fetches the corpus
  inside a reckon step, and a remote source is fetched exactly once per
  resolution.
- **Where:** into `~/.groundwork/principles/` (the resolved local corpus,
  under the managed runtime root). Materialization stages into a
  temporary sibling directory and swaps atomically, so a failed
  resolution never corrupts or removes an existing resolved corpus.
- **Checks:** the install preflights the configuration before touching
  any target (an invalid config halts the install before anything is
  projected), and a resolved corpus must carry a readable index
  (`PRINCIPLES.md` or `README.md`) at its root.
- **Refresh:** rerun `groundwork-install sync` from the checkout. There
  is no in-session synchronization — a stale resolved corpus is refreshed
  at the next setup run, by design.

Failure modes are loud and named, with nonzero exit: a
present-but-invalid config, a missing local source directory, an
unreachable remote, a corpus without an index, or a missing `python3`
where resolution is required.

## What this surface deliberately does not do

- It names no privileged external corpus in code. `pentaxis93/principles`
  above is an example value — the right one for Tesserine deployments,
  but a configuration choice, not a baked-in default.
- It does not pre-select which principles matter. The corpus speaks for
  itself; reckon's Orient selects the relevant principles per domain from
  the resolved corpus.
- It does not synchronize during a session. Materialization happens at
  setup; refreshing the resolved corpus is a setup-time action.

Design rationale for the surface choice is recorded in
[ADR-0005](architecture/decisions/0005-principles-corpus-configuration.md).
