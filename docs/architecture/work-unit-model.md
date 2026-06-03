# Work-Unit-Based Development

The work-unit graph is the persistence layer across sessions. Agent sessions end, context windows close, agents rotate — the work-unit graph survives. Work from the graph, not from memory.

## Definitions

- **Work-unit graph**: the set of open work-units and their dependency edges. It is the working memory of the project — not a backlog to be groomed, but the live map of what remains and what blocks what.
- **Unblocked**: a work-unit whose hard dependencies are all closed. Transitively unblocked means every ancestor in the dependency chain is closed.
- **Execution layer**: a set of work-units that share no mutual dependencies and can be worked in parallel once their shared ancestors are closed. Layer 0 has no dependencies; layer 1 depends only on layer 0; and so on.
- **Session-sized**: a work-unit that one agent can complete — from reading context through passing verification — in a single focused session.

## State Source Rule

State is determined by reading the forge tracker record content, not forge metadata (labels, columns). A work-unit's state is what its record body and comments say it is.

## Work-Unit Working States

| State       | Meaning                                      | Enters when                        | Exits when                          |
|-------------|----------------------------------------------|------------------------------------|-------------------------------------|
| draft       | Intent captured, not yet agent-executable     | Tracker record created without full criteria | Criteria, scope, and size filled in |
| ready       | Agent-executable and unblocked                | All fields complete, deps closed   | Session claims it                   |
| in-progress | Active session is working on it               | Session declares goal against it   | Session closes or blocks            |
| blocked     | Waiting on one or more open dependencies      | Dependency discovered or reopened  | All blocking work-units closed      |
| closed      | All acceptance criteria verified              | Verified and merged                | Reopened for regression             |
| stale       | No progress for 14+ days while still open     | Clock expires                      | Resumed, split, or closed as wont-fix |

## Dependency Graph Format

Epics with 4+ tasks include a dependency graph in two representations:

1. **Mermaid diagram** (arrows mean "must complete before"):
   ```mermaid
   graph TD
     A[#1 task-title] --> B[#2 task-title]
     A --> C[#3 task-title]
     B --> D[#4 task-title]
     C --> D
   ```

2. **Layered text summary** (for machine readability):
   ```
   Layer 0 (no deps):  #1
   Layer 1 (needs 0):  #2, #3
   Layer 2 (needs 1):  #4
   ```

## Graph Maintenance

- **Stale detection**: flag work-units with no progress comment for 14+ days. Resolution: resume, split into smaller work, or close as wont-fix with rationale.
- **Splitting**: when an in-progress work-unit exceeds session size, split remaining work into new work-units and close the original with a pointer.
- **Merging**: when two work-units converge on the same deliverable, merge into one and close the duplicate with a cross-reference.
- **Validation after mutation**: after adding, closing, splitting, or merging work-units, verify the graph has no orphaned dependencies or cycles.
- **Tracker identity agreement**: tracker-backed work-units carry a forge-tagged `handle` whose ticket number is the source of truth. The delivered artifact id must use the same ticket number (`work-unit-<N>-<short-slug>`), and a ticket must not have multiple delivered roots.
