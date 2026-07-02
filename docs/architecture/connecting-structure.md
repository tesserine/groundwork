# Groundwork Connecting Structure

This document carries the design rationale for groundwork's connecting
structure — why the artifacts, manifest edges, and schemas that link
protocols and skills are shaped the way they are. The structure itself
lives in its enforced homes: [`manifest.toml`](../../manifest.toml)
holds the artifact types, protocol declarations, edges, and triggers;
[`schemas/`](../../schemas/) holds every artifact shape
([`schemas/README.md`](../../schemas/README.md) maps them);
[`workflow-contracts/`](../../workflow-contracts/) holds the C-2
workflow mechanics. `tooling/conformance.py` validates those homes, and
this document consults them by link for every structural fact
([ADR-0008](decisions/0008-prose-is-projection.md), consequence 3).

## Ground Constraints

These constraints are ground for the design.

1. **Runa's function.** Event-driven cognitive runtime. Monitors artifact
   state, validates against schemas, computes dependency graph, enforces
   protocol contracts, injects context when activating protocols.

2. **Artifacts are the sole state mechanism.** No second channel. Runa
   derives workflow state entirely from artifacts on disk.

3. **Artifacts are capstones.** The agent does the real work. The artifact
   produced at the end captures context for runa to orchestrate handoff
   to the next stage. Artifact creation is the last step, not the work
   itself.

4. **Work-unit identity.** Every artifact instance carries a reference to
   the work-unit it belongs to. Runa uses this to resolve which instances
   are related. Manifest edges stay type-level; instance-level linking
   lives in artifact content.

5. **Two populations.** Protocols are runa-managed (declared in the
   manifest, triggered by artifact state, enforced by runa). Skills are
   agent-managed (invoked by agent judgment, not declared in the
   manifest).

6. **The liberation insight.** Runa imposing one law — the methodology
   topology — liberates the agent from its own many-law cognitive chaos.

## The Topology: Two Phases, Two Specification Scales

The work-unit artifact bridges two phases, both declared in
[`manifest.toml`](../../manifest.toml):

- **Planning phase** (unscoped): intent → survey → requirements →
  decompose → work-unit. External input enters as an intent artifact —
  the one type nothing inside the system produces — survey turns intent
  into requirements, and decompose breaks requirements into work-unit
  artifacts.
- **Scoped pipeline**: take → plan → implement → verify → submit →
  review → land. Take picks up a work-unit whose dependencies are
  satisfied, authors the contract, and the forward flow produces
  artifacts that runa tracks and threads by work-unit identity. The
  pipeline-shape decision is
  [ADR-0007](decisions/0007-dimension-agnostic-contract-machine.md).

The two phases carry two specification scales. **requirements** declares
what needs doing at any scope — a new tool, a feature, a migration —
and is the project-level specification. The **contract** declares how a
single work-unit is validated, criterion by criterion, and is the
implementation-level specification. Decompose bridges the scales: it
consumes requirements and produces the work-units that take picks up.

The contract is the spine of the scoped pipeline: authored at entry,
required by every judgment station, and the surface every downstream
artifact traces to. Documentation review lives inside verify —
documentation ships with the change it explains, and the
completion-evidence artifact records both criterion coverage and
documentation impact.

**The topology is pure graph.** Because artifacts are the sole state
mechanism (constraint 2), every link between protocols is an artifact
and every trigger is `on_artifact`, `on_change`, `on_invalid`, or a
composition of these. External events enter the system as artifacts —
an intent landing in the workspace — never as signals, so the manifest
carries no signal primitive.

**Work-unit-scoped evaluation.** The manifest declares type-level edges;
runa evaluates triggers per work-unit at runtime, partitioning the
workspace by each scoped artifact's `work_unit` content (constraint 4).
When several work-units are active, a protocol's trigger fires for a
specific work-unit's artifact, not every instance in the workspace.
Planning-phase artifacts predate work-unit identity and are scoped
through trigger evaluation against specific instances instead — see
*Common envelope* below for the schema side of this split.

## The Entry: Contract-First Take

In work-unit-first entry, selection is not take's job: the work-unit is
already the entry, and runa activates take on it. What entry truly is —
once selection is gone — is the place where done gets defined. Take
prepares the workspace, frames the work, and authors the contract.

The contract is the root of the scoped artifact chain. No separate
threading artifact is needed: work-unit identity is runtime-enforced —
runa injects `work_unit` into every scoped artifact and validates
canonical ids — so the entry's capstone is the contract itself.

The `work-unit` artifact take activates on arrives one of two ways:
created by `decompose`, or materialized from an existing forge ticket by
the [`acquire`](../../skills/acquire/SKILL.md) skill. Acquisition is
skill-side intake — the mirror of decompose's create path — and reaches
runa's store through decompose's own `work-unit` output tool, the same
way the `research` skill's output reaches the store through a protocol's
`may_produce` tool (see *the `may_produce` bridge* below). It creates no
ticket, derives the artifact one-way from the ticket (ticket = planning
home, artifact = execution snapshot, `handle` = back-link), and uses
decompose's tracker-backed `instance_id` convention, so acquired and
decomposed work-units are indistinguishable downstream. The manifest
producer of `work-unit` remains `decompose` alone; the single-producer
rule below is unaffected.

## Edge Design: `requires` vs `accepts`

Runa's interface defines two input edge types — `requires` blocks a
protocol until the artifact exists and validates; `accepts` injects the
artifact when present and proceeds without it otherwise (see
[runa's interface contract](https://github.com/tesserine/runa/blob/main/docs/interface-contract.md)
for the enforcement semantics). The design rule for choosing between
them:

> An input is `requires` when the protocol cannot produce a structurally
> valid capstone without it, or when the work-unit thread would break
> without it. An input is `accepts` when the capstone can be valid but
> would be better informed by the context.

Requires edges form the structural backbone of the topology — the chain
that must be unbroken for a work-unit to flow. Accepts edges provide
contextual enrichment — cross-cutting artifacts that improve quality but
whose absence does not break the chain. The per-protocol assignments
live in [`manifest.toml`](../../manifest.toml); each protocol's
`PROTOCOL.md` carries the operational meaning of its own inputs.

`decompose` is the planning-phase application of the rule that keeps
the distinction visible: ordinary planning reaches decompose through the
`requirements` trigger, and `requirements` is accepted so the protocol
receives the content it is decomposing — not required, because
cold-start ticket entry substitutes the trigger with the ticket
reference, reaches the same `work-unit` output surface, and has no
planning-phase requirements artifact yet.

## Standing Design Rules

These rules govern the topology as a whole. The manifest instantiates
them; this document is their named home as design rationale.

- **Single producer.** Every artifact type has exactly one producer — a
  protocol's `produces` declaration, a required-choice output group, or
  a source outside the protocol graph. `intent` is the external entry
  (no protocol produces it); `research-record` is skill-produced,
  reaching the store through `may_produce`; review's two disposition
  types are the members of its required-choice group. One producer per
  type means unambiguous provenance for runa's trigger and injection
  resolution. Current assignments:
  [`manifest.toml`](../../manifest.toml).

- **Acyclic backbone.** The requires graph is a DAG from intent through
  completion-record. Every artifact type has a consumer except
  `completion-record`, the terminal archival artifact.

- **Typed dispositions.** Review produces exactly one of two outcome
  artifact types through a required-choice group; the artifact type is
  the disposition ([ADR-0003](decisions/0003-disposition-as-artifact-type.md)).
  Land gates on the typed approval; the revision loop routes
  `change-needs-revision` back through submit, and review re-runs on the
  changed proposal version.

- **Skill emissions cross through protocols.** `research-record` is the
  sole skill-produced artifact type in the graph: no protocol's
  completion depends on one existing, so no protocol `produces` it, and
  the protocols whose sessions may emit one declare it in `may_produce`.
  This is the two-population principle (constraint 5) in action: skills
  produce artifacts that runa validates but never triggers on.

## Runtime Layers

Groundwork is methodology content, not a runtime. A working agent
session runs across four distinct layers, each with a narrow
responsibility.

**agentd.** Session lifecycle: starting and supervising the agent
process, preparing the environment, injecting identity. Opaque to
methodology content — agentd knows only that a given profile uses
methodology X, not what that methodology contains.

**Harness** (claude code, codex, and similar). Runs the agent loop,
mediates tool calls, and — critically for this document — **loads and
invokes skills**. Skills live at the harness layer operationally: they
are markdown files the harness reads into the agent's context on
activation, and the harness decides, based on the agent's judgment and
the harness's own activation rules, when to invoke them. Runa does not
see skills; they are not part of runa's contract.

**Runa.** The cognitive runtime. Its interface to groundwork is three
primitives: artifact types, protocol declarations, and trigger
conditions (see
[runa's interface contract](https://github.com/tesserine/runa/blob/main/docs/interface-contract.md)).
Runa orchestrates protocols, validates artifacts against their schemas,
and injects context when a protocol activates. It derives all workflow
state from artifacts on disk. Runa does not know about skills, does not
know about the harness, and does not participate in agent cognition.

**Groundwork.** The methodology content itself: protocols (runa-managed,
declared in the manifest), skills (not declared in the manifest),
schemas (what runa validates against), and the manifest that wires the
topology. This repository.

The important boundary for the rest of this document: **skills and runa
are disjoint worlds** — runa never sees a skill, and a skill has no
direct channel to runa. Anything a skill produces that needs to enter
runa's validated artifact store must cross through an active protocol
session. *The `may_produce` bridge* below describes the mechanism.

### Authoring surfaces and authority

The four layers imply a single authoritative place for each kind of
declaration:

- [`manifest.toml`](../../manifest.toml) is the sole contract surface
  for runa-managed protocol declarations: `requires`, `accepts`,
  `produces`, `may_produce`, and `trigger`. Manifest-shaped fields
  appear there and nowhere else.
- Skill frontmatter is a harness-and-reader surface, not a runa surface.
  The harness uses identifying fields such as `name` and `description`;
  optional `metadata` remains for human-oriented context such as version
  or attribution.
- Protocol frontmatter is reader-facing only. Runa reads the
  `PROTOCOL.md` file as instructions text; it does not parse mirrored
  contract declarations from the markdown header.

A second editable rendering of a manifest-shaped field is a second
unsynchronized surface: nothing holds it true, so it drifts from the
authoritative one. Keeping the declaration in one home eliminates the
inconsistency class rather than asking authors to maintain two
declarations by hand.

For the skill-frontmatter convention in follow-direct form, see
[`docs/authoring/skills.md`](../authoring/skills.md).

## Skill-Produced Artifacts and the `may_produce` Bridge

A skill can be loaded by the harness only during an agent session, which
always runs under some active runa protocol. The harness invokes the
skill, the agent does the skill's cognitive work, and the skill may
cognitively produce an artifact-shaped output — a research-record in the
concrete case. For that output to enter runa's validated artifact store,
the active protocol must declare the artifact type in its `may_produce`
field. Runa's interface contract then guarantees that each declared
output artifact is exposed as an MCP tool during the protocol session.

This is the bridge:

- `produces`: the artifact a protocol's completion depends on. Runa
  requires it before the protocol ends; the session's MCP server exposes
  a tool for it.
- `may_produce`: an artifact a protocol may optionally emit during
  execution, typically by a skill invoked inside the session. Runa does
  not require it; the session's MCP server exposes a tool for it.

At the interface level, the two fields are symmetric: one tool per
declared output artifact, named after the type, with the artifact's
schema as the tool's input schema. The distinction is semantic:
`produces` is the protocol's capstone, `may_produce` is the protocol's
sanctioned side-emission surface. (See
[runa's interface contract](https://github.com/tesserine/runa/blob/main/docs/interface-contract.md)
for the derivation rules runa's MCP server applies to artifact schemas
when generating tool input schemas.)

This document is the named home of the bridge's design rationale; the
manifest holds each protocol's actual `may_produce` wiring.

### `accepts` and `may_produce` as independent declarations

`accepts` and `may_produce` are two independent declarations that answer
two different questions:

- `accepts` answers: "if a valid instance of this artifact exists when I
  activate, inject it into my context."
- `may_produce` answers: "during my session, the agent may need to
  produce a fresh instance of this — expose an MCP tool for it."

For any protocol/artifact pair, the two decisions are made separately.
All four combinations are legitimate:

- **Neither.** The protocol neither reads the artifact on activation nor
  writes a fresh instance during its session.
- **`accepts` only.** The protocol reads an existing instance as context
  but does not produce new instances — a read-only consumer.
- **`may_produce` only.** The protocol writes a fresh instance during
  its session but does not read prior instances into its activation
  context — a protocol-internal emission.
- **Both.** The protocol reads prior instances and may also emit fresh
  ones.

Each protocol/artifact pair is a separate judgment by the methodology
author. There is no mirroring rule between the two fields; a reader
verifies the wiring by checking each declaration in
[`manifest.toml`](../../manifest.toml) against the protocol's actual
needs, not against the other field.

### Authoring a new skill-produced artifact

For a methodology author wiring a new skill whose output should be
persisted through runa:

1. Declare the artifact type in the manifest's artifact-type table and
   define its schema in [`schemas/`](../../schemas/).
2. For each protocol, judge separately whether prior instances of the
   artifact should enrich its activation context. Add the artifact to
   that protocol's `accepts` if yes.
3. For each protocol, judge separately whether the agent could plausibly
   need to produce a fresh instance of the artifact during that
   protocol's session. Add the artifact to that protocol's `may_produce`
   if yes. This decision is independent of step 2.
4. Keep any skill frontmatter limited to harness/reader identification
   fields. The runa-facing declaration lives only in `manifest.toml`; do
   not mirror `accepts`, `produces`, `may_produce`, or `trigger` into
   the skill file.

## Agent Interface

Two interfaces connect the agent to the artifact system. Both are owned
by runa. The agent touches neither directly.

**Input: context injection as prompt.** Runa constructs a prompt with
all context pre-integrated. The agent reads natural language, not JSON.
The contract, implementation-plan, and research-records are already
woven into the context window. The agent does not parse artifacts or
know about schemas.

**Output: MCP tools for artifact production.** Runa's MCP server exposes
one MCP tool per declared output artifact for the active protocol — the
union of `produces` and `may_produce`, subject to runa's tool-generation
rules. Each tool is named after the artifact type, and its input schema
derives from the artifact's JSON Schema. The design intent of that
derivation: everything runa can supply from session context is
server-supplied — the agent never writes `work_unit` for a scoped
artifact — and the one thing only the agent can name, the instance, is
agent-supplied as `instance_id`. Everything else is cognitive output:
the agent supplies it and runa validates it.
[Runa's interface contract](https://github.com/tesserine/runa/blob/main/docs/interface-contract.md)
owns the derivation rules, the eligibility rules, and how unscoped
sessions interact with `work_unit`-bearing schemas. Each producing
protocol's `PROTOCOL.md` carries its own delivery-call form, gate-bound
to the owning schema (ADR-0008, consequence 1) — the take protocol's
contract delivery is the worked example.

The MCP server validates the payload, writes the artifact to the
workspace under the chosen `instance_id`, and records it in runa's
store. The agent never constructs filenames, writes to disk, or supplies
`work_unit` for scoped artifacts.

**The liberation insight at the interface level.** The agent never
touches the artifact system. Runa owns both input (context injection)
and output (MCP validation and placement). The agent is liberated from
infrastructure — free to do its cognitive work without fighting JSON
Schema internals, file placement conventions, or state management.

## The MCP Server as Methodology Interface

*The subsections below extend the interface pattern above. The inference
of `work_unit` from execution context is present behavior. The
simplifications it enables — `deliver(content)`, structured queries,
cross-reference validation, progressive authoring — are design
directions, not current behavior.*

The MCP server is not just an artifact I/O layer. It is the agent's
entire interface to the methodology. The agent doesn't know about runa,
manifests, schemas, work-units, artifact types, or the topology. It has
tools. The tools guide the work. The shape of the tools IS the
methodology.

### The agent knows nothing about infrastructure

The MCP server can infer from execution context:

- **work_unit** — which work-unit is being worked
- **protocol** — which protocol is executing
- **artifact type** — what this protocol produces
- **available context** — what requires/accepts artifacts exist

This means the agent's tool interface can be as simple as
`deliver(content)`. The server knows the rest.

### Structured queries replace context parsing

Instead of the agent parsing injected context, the MCP server exposes
query tools: what are my acceptance criteria, what behavior entries
exist, what checks passed. Structured queries against the artifact
store, returned in natural language or structured data.

### Cross-reference validation at write time

When the agent references an acceptance criterion in a scenario or gate,
the MCP server verifies it exists in the work-unit artifact. Not just
schema validation — semantic validation. The traceability thread is
enforced mechanically.

### Progressive authoring

Instead of one atomic `deliver()` call, the MCP server can support
incremental building: add a scenario or gate, get immediate feedback,
add another, finalize. The agent discovers errors as it works, not after
producing the full artifact.

### Pre-population and cognitive scaffolding

The MCP server can present pre-assembled data to reduce the agent's
mechanical work. Verify's agent receives a pre-filled coverage matrix
joining the contract's criteria to performed results by `criterion_id` —
the same matrix for every dimension — and does judgment work: confirm,
amend, flag gaps, not data assembly.

### Observability from the start

Every tool call is a structured event. The MCP server sits at the
chokepoint between agent and system. This enables:

- **Telemetry** — which agent, which protocol, which work-unit, what was
  produced, when, whether it validated. Without the agent doing anything
  extra.
- **Cost tracking** — tool calls correlated with LLM calls. Cost per
  contract, cost per work-unit implementation, cost per acceptance
  criterion. Measured, not estimated.
- **Anomaly detection** — the server sees patterns across many work
  units. An implement protocol completing in two minutes when the median
  is forty is a signal. A contract with one behavior entry for eight
  acceptance criteria is a signal.
- **Replay and audit** — the full sequence of tool calls for a work unit
  is a structured trace. Debugging agent behavior means reading
  structured logs, not sifting through conversations.
- **Resource governance** — token budgets, time limits, policy
  enforcement at the tool level.

### Architecture summary

The CLI and artifact store are the skeleton. The MCP server is the
nervous system — the live interface where agents meet methodology. The
topology, schemas, and edges whose rationale this document carries give
the MCP server its shape. The liberation insight taken to its
conclusion: the one law isn't visible to the agent as a law. It is the
shape of the available tools.

## Schema Design Principles

The artifact shapes live in [`schemas/`](../../schemas/), validated by
`tooling/conformance.py` and mapped by
[`schemas/README.md`](../../schemas/README.md). The principles that
shape them:

### Consumer-backward

Each schema is designed from the consuming protocol's need: what must be
in the injected context for the consumer to produce its own capstone?
Not from a guess about what the producer might write. The manifest's
edges name each type's consumers; each consuming protocol's
`PROTOCOL.md` carries what it does with the input.

### Common envelope

Scoped-pipeline artifacts carry a `work_unit` field — the work-unit
reference that threads them together. Runa uses it to scope context
injection: when plan activates, it receives the contract for this
work-unit, not every contract in the workspace. Planning-phase artifacts
predate work-unit identity and do not carry the field; runa scopes them
through trigger evaluation against specific artifact instances. Which
schemas carry the field is visible in the schemas themselves.

Everything else runa needs is available from outside artifact content:
artifact type from directory structure, producing protocol from manifest
declarations, modification timestamps from filesystem state, content
hashes from the store. The common envelope is minimal by design.

### Metadata elimination

Artifact content carries no field whose value runa can derive from its
own state. Producing protocol, timestamps, and content hashes are runa's
to know; a `produced_by` or `date` field in an artifact duplicates what
the runtime already tracks, and by sufficiency has no place in a schema.

### The traceability thread

Acceptance criteria on the work-unit are the high-level "done"
statements. Contract criteria are their precise refinement, dimension by
dimension. The thread runs the full length of the execution chain:
work-unit acceptance criteria → contract criteria that trace to them →
test-evidence results that trace to criteria → completion-evidence
coverage rolled up at the acceptance-criterion level. Two schema
consequences carry the design: each contract criterion names the
acceptance criterion it refines, and completion-evidence reports
coverage at the acceptance-criterion level — so verify can answer "are
all acceptance criteria covered?" The exact fields live in
[`schemas/`](../../schemas/).

### Context injection is not transitive

Runa injects a protocol's declared requires and accepts instances. It
does not inject transitive dependencies. If a protocol needs the
work-unit content (to read acceptance criteria), it declares the
work-unit artifact in its own edges — the `work_unit` reference carried
by every scoped artifact identifies the work-unit but does not carry its
content.

### The connector handle seam

The `work-unit.handle` field is the schema-as-contract seam between
groundwork and runa. Every work-unit is tracker-backed. The work-unit
schema requires the connector-issued `{ id, display }` handle, and
groundwork treats it as opaque: schema validity and conformance are
checked against the vendored Forge Capability handle definition, while
identity comparisons derive from `id` equality rather than provider
coordinates or display text. The vendored schema at
[`schemas/forge-capability/v1/forge-capability.schema.json`](../../schemas/forge-capability/v1/forge-capability.schema.json)
is the single home for the handle definition and the canonical
capability operations; groundwork artifact schemas carry self-contained
copies so runa can validate artifacts directly, and conformance fails
when those copies drift from the vendored `#/$defs/handle` definition.
The [decompose delivery rules](../../protocols/decompose/PROTOCOL.md)
create the tracker ticket before first work-unit delivery and carry the
returned connector handle exactly once.

## Where Documentation Discipline Lives

Documentation review is part of verification: verify's
documentation-impact step maps the change to affected documents,
classifies drift, updates in the same change, and records the outcome in
`completion-evidence.documentation`. The always-on documentation-writing
stance (audience, artifact choice, depth) is carried by the `orient`
skill
([`skills/orient/references/documentation.md`](../../skills/orient/references/documentation.md));
inline documentation is written alongside code during implement's GREEN
and REFACTOR phases.
