# Documentation Discipline

The always-on writing stance orient carries: what documentation exists, who
it serves, and how much detail it needs. The `verify` protocol audits the
result after a change; this discipline governs the writing as it happens.

## Artifact Types

| Artifact | Audience | When Produced |
|----------|----------|---------------|
| README.md | New users, contributors, agents on first encounter | Project init; major capability changes |
| README lead / project synopsis | People who do not yet know the project (discovery) | Project init; positioning changes |
| ARCHITECTURE.md | Contributors, agents understanding system structure | After grounding; significant structural changes |
| ADR | Future decision-makers (human and AI) | When a significant decision is made (MADR 4.0 format) |
| CHANGELOG.md | Users, operators, downstream consumers | Before landing user-visible changes (Keep a Changelog format) |
| work-unit-model.md | Contributors, agents working from the work-unit graph | When work-unit states, graph format, or maintenance rules change |
| API reference | API consumers, agents calling functions | During implementation, alongside code |
| Inline comments | Future maintainers, agents modifying code | At non-obvious decision points during implementation |
| Command help (invocation surface) | Operators and agents meeting a command cold — `--help`, subcommand help, usage | Any change shipping or altering a command's invocation |
| Error output (failure surface) | Recipients mid-failure, acting from the error alone | Any change shipping or altering a failure path a recipient meets |
| Machine self-description | Agents discovering a surface programmatically — MCP tool descriptions, schemas, manifest entries | Any change shipping or altering a machine-discoverable surface |

Interactive prompt flows are invocation-surface kin: the prompts are where
the recipient is met mid-act.

## Constraints

- `audience-first`: identify the reader before writing. No document exists
  without a stated audience.
- `minimum-viable-detail`: include enough to prevent mistakes, no more.
  Three clear sentences beat two verbose paragraphs.
- `source-of-truth-over-counts`: avoid hardcoded aggregate counts for
  dynamic sets. Reference the authoritative object or generate the value.
- `task-oriented`: organize docs around what the reader needs to
  accomplish, not around the file tree.
- `adr-for-decisions`: significant architectural decisions get an ADR.
  "Significant" means it affects contributor work, is hard to reverse, or
  is not obvious.

## Procedure: audience-identify

Before writing any documentation:

1. Name the audience: end user, contributor, API consumer, AI agent, or
   discovery reader.
2. State what they already know.
3. State what they need to accomplish after reading.
4. Apply the audience test throughout: "Would this reader know what to do
   after reading this?"

Audience profiles:

- **End user**: needs to install, configure, and use the system. Assumes no
  internals knowledge.
- **Contributor**: needs architecture understanding and dev setup. Assumes
  programming competence but no project-specific knowledge.
- **API consumer**: needs contracts and integration guidance.
  Assumes domain competence.
- **AI agent**: needs explicit file paths, concrete examples, and
  constraint-first organization. Assumes no persistent memory across
  sessions.
- **Discovery reader**: does not yet know the project exists. Needs, from
  the entry surface in a few sentences, what it is, who it is for, and why
  to choose it over the status quo. Assumes no prior awareness, and leaves
  if the first lines do not land.

## Procedure: write-artifact

1. Run audience-identify.
2. Use `reckon` when the artifact requires design decisions (ARCHITECTURE
   docs, ADRs).
3. Write for the identified audience at the appropriate depth.
4. Apply minimum-viable-detail; cut any section the reader does not need
   at the point of use.
5. Verify the audience test passes before committing.

## Corruption Modes

- `structure-not-understanding`: document headings mirror the directory
  tree instead of the reader's task.
- `verbose-not-useful`: the document is long but a reader still cannot act.
- `audience-blindness`: no stated audience, or the document would not
  change if the audience changed.
