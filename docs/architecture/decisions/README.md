# Methodology Decision Records

Architecture decisions scoped to the groundwork methodology. Ecosystem-level
decisions live in the
[commons ADR register](https://github.com/tesserine/commons/blob/main/adr/README.md);
nothing here duplicates that scope.

## Status rubric

groundwork is pre-1.0 and its decisions are ratified by the operator, not by
shipping. Status names the **governance state**, not the implementation
state — a decision can be fully shipped and still await ratification:

- **Proposed** — authored and delivered for operator review. May already
  describe shipped behavior; the decision itself has not been reviewed.
- **Provisional** — operating decision: it is the methodology's current
  design and is binding on contributors and agents, but it is held open for
  revision while the methodology stabilizes. Revisions are recorded in-file
  (see ADR-0002's Revision section).
- **Accepted** — operator-ratified. Changing it requires a superseding ADR.
- **Superseded** — replaced; the Status line names the successor.

An agent executing the methodology treats Proposed and Provisional ADRs as
authoritative for *what the system currently is*; the open status signals
only that the operator may still revise the decision.

## Register

| # | Title | Status | Date |
| --- | --- | --- | --- |
| [0001](0001-internal-development-history-policy.md) | Internal Development History Policy | Provisional | 2026-03-10 |
| [0002](0002-methodology-sovereignty.md) | Methodology Sovereignty | Provisional (revised 2026-05-28) | 2026-05-02 |
| [0003](0003-disposition-as-artifact-type.md) | Disposition as Artifact Type | Provisional | 2026-05-31 |
| [0004](0004-contract-first-scoped-pipeline.md) | Contract-First Scoped Pipeline | Proposed — delivered for operator review | 2026-06-11 |
| [0005](0005-principles-corpus-configuration.md) | Principles Corpus Configuration | Provisional | 2026-06-12 |

New decisions add a row here in the same change.
