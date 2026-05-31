# Groundwork

Groundwork is a methodology plugin for [runa](https://github.com/tesserine/runa),
a cognitive runtime for AI coding agents.
It encodes opinions about how software should be built into protocols, skills,
and artifact schemas that a runa instance orchestrates. It is not a runtime, a
CLI, or a framework — it is a methodology definition.

Groundwork serves teams that use AI coding agents for software delivery. It
connects the stages from problem framing through shipped change so that agent
work traces from requirement to merged code, completion claims require evidence,
and progress survives session boundaries.

For what methodology plugins are and how runa executes them, see runa's
[core concepts](https://github.com/tesserine/runa#core-concepts).

## The Shape of the Methodology

Work moves through two phases connected by the work-unit artifact.

**Planning** takes an external request and produces work-units.
Survey examines what actually needs doing; decompose breaks that into work
units with acceptance criteria and dependency edges.

**Execution** takes one work-unit and carries it through to a merged increment:
take claims the work-unit and opens the session → specify writes the behavior
contract as Given/When/Then scenarios → plan converges on a decision-complete
design → implement executes through RED-GREEN-REFACTOR → verify gates
completion with evidence → document ensures accuracy → submit packages the
change → land merges and closes the loop.

Each protocol produces an artifact that the next protocol requires.
→ [`docs/architecture/connecting-structure.md`](docs/architecture/connecting-structure.md)

Six skills operate across the topology:

- **orient** — the methodology map that connects protocols and skills
- **reckon** — first-principles reasoning when creating or analyzing
- **debug** — root cause investigation when failures appear
- **resolve** — structural friction resolution when obstacles impede
- **research** — external evidence gathering when facts are missing
- **contract** — behavior traceability through execution

Not every piece of work needs every stage. A bug with an existing work-unit enters
at execution. A new capability enters at planning. The constraint is sequence,
not completeness.
→ [`skills/orient/SKILL.md`](skills/orient/SKILL.md)

For how runa orchestrates this topology at runtime, see the
[interface contract](https://github.com/tesserine/runa/blob/main/docs/interface-contract.md).

## Interactive Installation

Runa-served agents consume Groundwork through the methodology mount. Interactive
Claude Code and Codex sessions can install the same skills and protocols into
their local discovery directories from a pinned Groundwork checkout:

```bash
git checkout --detach v0.2.0
scripts/groundwork-install install
```

The first release containing `scripts/groundwork-install` is v0.2.0.

The installer writes user-owned entries only, with no root or sudo requirement:

- `~/.claude/skills/{name}/`
- `~/.agents/skills/{name}/`

Every directory under `skills/` is copied as a skill entry. Every directory
under `protocols/` is copied as a skill-shaped entry with `PROTOCOL.md`
projected to `SKILL.md` and an interactive artifact delivery adapter inserted
near the top of the installed protocol. The adapter tells an interactive agent
how to present the produced artifact body to the human instead of calling the
runa MCP artifact tool. Installed entries are copies, not source-checkout
symlinks, so later changes to the checkout do not drift into the active
discovery surface.

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
→ [`protocols/decompose/PROTOCOL.md`](protocols/decompose/PROTOCOL.md)

### How work is executed

**Behavior is the thread.** The behavior contract written during specify traces
through every subsequent stage. Plans link design decisions to behavior
scenarios. Tests verify named scenarios. Verification cites behavior-level
evidence. Landing records what coverage shipped.
→ [`protocols/specify/PROTOCOL.md`](protocols/specify/PROTOCOL.md),
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
→ [`protocols/document/PROTOCOL.md`](protocols/document/PROTOCOL.md)

**Documentation obligation.** User-facing changes carry documentation
requirements. Documentation ships in the same PR as the code that caused it.
Drifted documentation compounds.
→ [`protocols/document/PROTOCOL.md`](protocols/document/PROTOCOL.md),
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
| [`protocols/`](protocols/) | 10 protocol definitions — one per stage |
| [`skills/`](skills/) | 6 skills — orientation and cross-cutting disciplines |
| [`schemas/`](schemas/) | JSON Schema contracts for artifacts and authoring substrates |
| [`tooling/`](tooling/) | Authoring-time parsers and validators |
| [`docs/architecture/`](docs/architecture/) | Topology design rationale and work-unit state model |
| [`docs/authoring/`](docs/authoring/) | Follow-direct guides for methodology authors |

For how these pieces compose into a methodology plugin, see runa's
[methodology authoring guide](https://github.com/tesserine/runa/blob/main/docs/methodology-authoring-guide.md).

## License

[MIT](LICENSE)
