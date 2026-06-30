# Groundwork

**Software delivery as an executable methodology — completion requires
evidence, and the discipline is enforced, not exhorted.**

Groundwork is a methodology plugin for [runa](https://github.com/tesserine/runa),
a cognitive runtime for AI coding agents.
It encodes opinions about how software should be built into protocols, skills,
and artifact schemas that a runa instance orchestrates. It is not a runtime, a
CLI, or a framework — it is a methodology definition: an entire engineering
discipline expressed as data that a runtime can enforce.

That expression has teeth. Agent work traces from requirement to merged code
through typed artifacts; completion claims are gated on evidence, not
assertion; progress survives session boundaries because state lives in the
work-unit graph, not in any one agent's memory. The methodology practices
what it enforces: every belief below traces to its enforcing file, the
dependency-graph notation and every script path in its instructions are
CI-gated against drift, and forge work is carried through connector-owned
capability operations so the methodology owns no provider implementation.

For what methodology plugins are and how runa executes them, see runa's
[core concepts](https://github.com/tesserine/runa#core-concepts). Groundwork
is the first methodology of the [Tesserine](https://github.com/tesserine)
stack's **Declare** tier — [gazette](https://github.com/tesserine/gazette)
is the proof the tier generalizes beyond code (ecosystem map:
[commons SOURCE-OF-TRUTH.md](https://github.com/tesserine/commons/blob/main/SOURCE-OF-TRUTH.md)).

## The Shape of the Methodology

Work moves through two phases connected by the work-unit artifact.

**Planning** takes external intent and produces work-units.
Survey examines what actually needs doing; decompose breaks that into work
units with acceptance criteria and dependency edges.

**Entry** into the scoped pipeline happens one of two ways: a work-unit newly
created by decompose, or one the acquire skill materializes from an existing
forge ticket (the "start on ticket #N" path). Either way take activates on a
work-unit artifact.

**The scoped pipeline** takes one work-unit and carries it through to a merged
increment: take prepares the workspace and writes the behavior contract as
Given/When/Then scenarios — the spine threaded through every later stage →
plan converges on a decision-complete design → implement executes through
RED-GREEN-REFACTOR → verify gates completion with evidence and documentation
review → submit delivers an immutable change-proposal version → review emits
exactly one typed disposition → land applies the approved version and closes
the loop.

Each protocol produces an artifact that the next protocol requires.
→ [`docs/architecture/connecting-structure.md`](docs/architecture/connecting-structure.md)

Skills operate across the topology as cross-cutting disciplines and
stage-specific judgment:

- **orient** — the methodology map that connects protocols and skills
- **reckon** — first-principles reasoning when creating or analyzing
- **debug** — root cause investigation when failures appear
- **resolve** — structural friction resolution when obstacles impede
- **research** — external evidence gathering when facts are missing
- **contract** — the BDD home: contract authoring at entry, traceability through execution
- **work-unit-craft** — the discipline for authoring work-unit tracker records
- **code-review** — review judgment for submitted change proposals
- **acquire** — entry from an existing forge ticket: materializes the work-unit artifact take activates on

Not every piece of work needs every stage. A bug with an existing work-unit enters
at execution. A new capability enters at planning. The constraint is sequence,
not completeness.
→ [`skills/orient/SKILL.md`](skills/orient/SKILL.md)

For how runa orchestrates this topology at runtime, see the
[interface contract](https://github.com/tesserine/runa/blob/main/docs/interface-contract.md).

## The Principles Corpus

Reckon reasons from navigational principles selected during Orient. The
corpus they are selected from is not hard-coded: it resolves through
methodology configuration and is materialized locally at setup, so reckon
reads local content during reasoning. With zero configuration the corpus
is the minimal embedded default at [`principles/`](principles/) — a bare
checkout reasons offline, out of the box. Deployments that want a richer
corpus configure one (any git repository or local directory).
→ [`docs/principles-corpus.md`](docs/principles-corpus.md)

## Install for Runtime-Driven Deployments

In a runtime-driven deployment, a protocol runtime executes the methodology
through the methodology interface contract and delivers protocol instruction
content at execution time — so protocols are never installed for agent
discovery. What that channel does not deliver, `scripts/install` installs from
a clean checkout, idempotently and with no root or sudo requirement:

```bash
scripts/install install --corpus-git https://example.org/owner/corpus
```

- **Skills, verbatim** — every `skills/<name>/` carrying a `SKILL.md` lands
  unmodified in `~/.claude/skills/<name>` and `~/.agents/skills/<name>`.
  Skills are agent-invoked by judgment and are not runtime-delivered, so they
  install natively; no projection or rewriting of any kind.
- **The methodology runtime** — `~/.groundwork` with `manifest.toml`,
  `schemas/{artifact_type}.schema.json` for each declared artifact type, and
  `protocols/{name}/PROTOCOL.md` for each declared protocol. Forge operations
  are connector capability tools contributed through runa's MCP surface, not
  local provider mechanics.
- **The principles corpus** — the `--corpus-git URL [--corpus-ref REF]`,
  `--corpus-path PATH`, or `--corpus-embedded` operator input is recorded in
  the deployment-owned `${XDG_CONFIG_HOME:-~/.config}/groundwork/principles.toml`
  and materialized at `~/.groundwork/principles` through the resolution layer.
  Without an input an existing configuration is honored; without either, the
  embedded default resolves — zero-config stays the ordinary path.

Re-running converges to the same state with exit 0; skills no longer shipped
are removed; pre-existing content the installer does not own is reported as a
named conflict, never overwritten or adopted (entries placed by the legacy
`groundwork-install` are directed to its own uninstall). Content derives from
the checkout's `HEAD` commit, recorded in each entry's ownership marker.
`scripts/install uninstall` removes only marker-verified managed entries and
leaves the deployment-owned config in place. State lives at
`${XDG_STATE_HOME:-~/.local/state}/groundwork/install.tsv`. No shell startup
file is created or modified by any run. Prerequisites: `git` and `python3`.

The decision record is
[ADR-0006](docs/architecture/decisions/0006-runtime-driven-self-install-surface.md).

## Interactive Installation

Runa-served agents consume Groundwork through the methodology mount. Interactive
Claude Code and Codex sessions can install the same skills and protocols into
their local discovery directories from a pinned Groundwork checkout. This
protocols-as-skills projection serves deployments with no protocol runtime; it
is deprecated in favor of the runtime-driven path above, and its retirement is
tracked in [#415](https://github.com/tesserine/groundwork/issues/415):

```bash
git checkout --detach v0.2.0
scripts/groundwork-install install
```

The first release containing `scripts/groundwork-install` is v0.2.0.

The installer writes user-owned entries only, with no root or sudo requirement:

- `~/.claude/skills/{name}/`
- `~/.agents/skills/{name}/`
- `~/.groundwork/`

Every directory under `skills/` is copied as a skill entry. Every directory
under `protocols/` is copied as a skill-shaped entry with `PROTOCOL.md`
projected to `SKILL.md` and an interactive session surface handoff inserted
near the top of the installed protocol. The handoff directs interactive
sessions through `runa go --work-unit <id>`: the operator issues only `go`,
while the configured agent reaches `next-protocol-context`, the current output
tool, and `advance` inside runa's validated cascade. Installed entries are
copies, not source-checkout symlinks, so later changes to the checkout do not
drift into the active discovery surface.

When `manifest.toml` is present, the installer projects a managed runtime
bundle under `~/.groundwork/`. The bundle contains the manifest and ownership
marker. It deliberately contains no provider mechanics, resolver module, or
forge-operation binary; upgrading removes stale copies of those retired runtime
children.

Forge work uses the vendored Forge Capability v1.1.0 contract at
`schemas/forge-capability/v1/forge-capability.schema.json`. The eight canonical
operations are connector MCP tools: `read-ticket`, `create-ticket`,
`claim-work-unit`, `record-progress`, `deliver-change-proposal`,
`reflect-disposition`, `apply-approved-change`, and `close-out`. Work units and
change proposals carry the connector-issued `{ id, display }` handle. The
handle is opaque to Groundwork: internal identity derives from `id` equality,
not from provider coordinates or a human-readable display string.

The source checkout must be clean and pinned at a tag or full commit SHA. The
command refuses branch checkouts because a branch is a moving source. To update
to a different pinned Groundwork version, check out that ref and run:

```bash
scripts/groundwork-install sync
```

`sync` converges the discovery directories to the new pinned source, including
removing entries that no longer exist upstream. `scripts/groundwork-install
status` reports the recorded install state, and `scripts/groundwork-install
uninstall` removes only entries the command created.

Methodology authors who develop Groundwork itself and want their working branch
reflected in the live discovery surface can pass `--from-branch` to install or
sync the current branch HEAD instead of a detached pinned ref:

```bash
scripts/groundwork-install sync --from-branch
```

The checkout must still be clean — `--from-branch` relaxes only the pinned-ref
requirement, not the clean-checkout requirement, so the recorded `source-sha`
always identifies a real commit. Because a branch is a moving source, this is an
opt-in for development; the default still requires a pinned tag or commit SHA.

Ownership is tracked in both a per-entry marker file and an XDG state file at
`${XDG_STATE_HOME:-~/.local/state}/groundwork-install/interactive-install.tsv`.
Pre-existing entries, including unofficial symlinks with the same names, are
reported as unmanaged conflicts rather than overwritten or adopted. When the
state file records ownership but the marker is missing at a deletion boundary,
the command fails and leaves state intact so the operator can inspect the
disagreement before anything irreversible happens.

Prerequisites are the stock command-line tools expected on Fedora CoreOS for
this workflow: `bash`, `git`, and POSIX file utilities such as `cp`, `find`,
`mkdir`, `mv`, and `rm`.

## Conformance Checks

Run the narrowed Step 1 methodology conformance runner with:

```bash
python -m tooling.conformance
```

By default it checks `manifest.toml`, source-tree workflow contracts and
mechanics when those directories exist, and all JSON Schema definitions under
`schemas/`. Pass files or directories as arguments to check explicit
C-2/C-3/C-4/C-5 units and aggregate all failures before returning a non-zero
exit status. Directory arguments use the same discovery rules as the default
runner: `manifest.toml`, `workflow-contracts/` and `mechanics/` TOML units,
plus `schemas/*.schema.json`. Explicit file arguments that do not classify as
conformance units still fail loudly.

The C-5 manifest check validates the outcome-routing substrate used by
required-choice protocol outputs: top-level `[[outcome_types]]` entries must
resolve to declared artifact types, `[[protocols.required_output_choices]]`
members must be registered outcome types, and successor triggers that route on
an outcome must use `on_artifact`, while successor triggers must not target a
disposition-agnostic output of an outcome-bearing protocol through any trigger
form or composite trigger.

It also validates connector capability conformance. Forge operation names,
operation input/output references, and the handle definition are read from the
vendored Forge Capability schema; absence checks for retired provider runtime
files are guards on top of that positive contract.

## What Groundwork Believes

These are the methodology choices embedded in groundwork's protocols and skills.
Each traces to the file where it lives.

### How work is understood

**The work-unit graph is working memory.** Agent sessions end, context windows
close, agents rotate. The work-unit graph is the persistence layer that survives
those boundaries. Multi-session progress depends on the graph, not on agent
memory.
→ [`docs/architecture/work-unit-model.md`](docs/architecture/work-unit-model.md)

**Sovereignty.** Every handoff passes outcomes — what must be true — never
implementation steps. Work-units define acceptance criteria, not procedure. Plans
define interfaces and decisions, not scripts to follow.
→ [`protocols/decompose/PROTOCOL.md`](protocols/decompose/PROTOCOL.md),
[`skills/work-unit-craft/SKILL.md`](skills/work-unit-craft/SKILL.md)

### How work is executed

**Behavior is the thread.** The behavior contract written at take — the entry —
traces through every subsequent stage. Plans link design decisions to behavior
scenarios. Tests verify named scenarios. Verification cites behavior-level
evidence. Review judges against the contract. Landing records what coverage
shipped.
→ [`protocols/take/PROTOCOL.md`](protocols/take/PROTOCOL.md),
[`skills/contract/SKILL.md`](skills/contract/SKILL.md)

**Evidence before assertion.** No completion claims without fresh verification
evidence. No fixes without root cause investigation. No implementation plans
without grounded constraints.
→ [`protocols/verify/PROTOCOL.md`](protocols/verify/PROTOCOL.md),
[`skills/debug/SKILL.md`](skills/debug/SKILL.md)

**Test-driven execution.** No production code without a failing test first.
Each test fails first, and for the right reason. Only the minimum code to pass
gets written. Code written before its test gets deleted and restarted.
→ [`protocols/implement/PROTOCOL.md`](protocols/implement/PROTOCOL.md)

**Code is ground truth.** When documentation and code disagree, code behavior
is descriptive truth. Documentation is a claim that must be verified against
the code.
→ [`protocols/verify/references/documentation-review.md`](protocols/verify/references/documentation-review.md)

**Documentation obligation.** User-facing changes carry documentation
requirements. Documentation ships with the code change that caused it.
Drifted documentation compounds.
→ [`protocols/verify/PROTOCOL.md`](protocols/verify/PROTOCOL.md),
[`skills/orient/SKILL.md`](skills/orient/SKILL.md)

### How obstacles are handled

**Root cause before fixes.** No fix without an established root cause. After
three failed fix attempts, the architecture is under question, not the
symptoms.
→ [`skills/debug/SKILL.md`](skills/debug/SKILL.md)

**Friction is structural.** Workarounds compound debt. Operational friction — a
missing tool, broken configuration, stale convention — gets resolved
structurally before work continues. Friction that exceeds side-quest scope
becomes a work-unit.
→ [`skills/resolve/SKILL.md`](skills/resolve/SKILL.md)

## What the Repo Contains

| Path | Contains |
|------|----------|
| [`manifest.toml`](manifest.toml) | Manifest: artifact types, protocol topology, trigger conditions |
| [`protocols/`](protocols/) | Protocol definitions for methodology stages |
| [`skills/`](skills/) | Skills for orientation, cross-cutting disciplines, and stage-specific judgment |
| [`schemas/`](schemas/) | JSON Schema contracts for artifacts and authoring substrates |
| [`principles/`](principles/) | Embedded default principles corpus (standalone fallback; see [`docs/principles-corpus.md`](docs/principles-corpus.md)) |
| [`tooling/`](tooling/) | Authoring-time parsers and validators |
| [`docs/architecture/`](docs/architecture/) | Topology design rationale and work-unit state model |
| [`docs/authoring/`](docs/authoring/) | Follow-direct guides for methodology authors |

For how these pieces compose into a methodology plugin, see runa's
[methodology authoring guide](https://github.com/tesserine/runa/blob/main/docs/methodology-authoring-guide.md).

## License

[MIT](LICENSE)
