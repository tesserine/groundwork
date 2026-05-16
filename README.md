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

## Using Groundwork Interactively

Interactive operators can install Groundwork for Claude Code and Codex with:

```sh
git clone https://github.com/tesserine/groundwork.git
cd groundwork
git checkout vX.Y.Z
./scripts/groundwork-sync install
```

`groundwork-sync install` requires a clean detached checkout at a tag or full
commit SHA. It refuses branch checkouts because branches move. The command
copies the pinned methodology into
`${XDG_STATE_HOME:-$HOME/.local/state}/groundwork-sync`, then creates
discoverable entries under both `$HOME/.claude/skills/` and
`$HOME/.agents/skills/` for every directory in `skills/` and `protocols/`.
Protocols are projected as skill-shaped entries whose `SKILL.md` is copied
from `PROTOCOL.md`.

Re-run `./scripts/groundwork-sync install` from a different clean detached
checkout to sync to that pinned source. Existing unmanaged entries with the
same names are reported as conflicts. To remove only entries created by the
command:

```sh
./scripts/groundwork-sync uninstall
```

The command uses Bash, coreutils-compatible filesystem tools, and Git. Fedora
CoreOS operators should ensure Git is installed before use.

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
| [`schemas/`](schemas/) | JSON Schema contracts for each artifact type |
| [`docs/architecture/`](docs/architecture/) | Topology design rationale and work-unit state model |
| [`docs/authoring/`](docs/authoring/) | Follow-direct guides for methodology authors |

For how these pieces compose into a methodology plugin, see runa's
[methodology authoring guide](https://github.com/tesserine/runa/blob/main/docs/methodology-authoring-guide.md).

## License

[MIT](LICENSE)
