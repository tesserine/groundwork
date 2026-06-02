# Forge Deployment Identity

## Audience and Purpose

This note is for interactive agents, runa-served agents, and operators binding
Groundwork forge mechanics. It defines the `GROUNDWORK_*` deployment identity
contract: the environment variables that identify the active forge deployment
and the repository/tracker targets used by forge-tagged mechanics.

The contract is an atom set, not a bundle of ready-made endpoint strings. Each
variable stores one fact. Consumers derive composed values from those facts at
the point of use so there is no second stored copy to keep synchronized.

## Contract

| Variable | Holds | Example | Forge-assigned? |
|---|---|---|---|
| `GROUNDWORK_FORGE_TYPE` | Forge selector used to choose the active forge-tagged mechanic. | `github` | No; this is configuration. |
| `GROUNDWORK_FORGE_ENDPOINT` | Deployment host; service subdomains derive from it where the forge topology uses them. | `weforge.build` | No; this is configuration. |
| `GROUNDWORK_FORGE_OWNER` | Tracker and repository owner handle. | `operator` | No; this is configuration. |
| `GROUNDWORK_FORGE_NAME` | Tracker and repository name. | `weforge` | No; this is configuration. |
| `GROUNDWORK_FORGE_TRACKER_ID` | Tracker integer ID for mechanics whose forge API requires an integer tracker identifier. | `4` | Yes; non-derivable and assigned by the forge. |
| `GROUNDWORK_FORGE_REPO_ID` | Git repository integer ID for mechanics whose forge API requires an integer repository identifier. | `<repo Int>` | Yes; non-derivable and assigned by the forge. |

`GROUNDWORK_FORGE_TYPE` already has runtime behavior in the forge-operation
resolver: when no explicit override or environment value is present, the active
forge type defaults to `github`. The other variables are deployment identity
atoms supplied by the session environment or by runa session construction.

The two integer IDs are explicit because they are forge-assigned and
non-derivable. Do not infer them from owner, name, endpoint, or URL shape.

## Derivation Boundary

Issue #362 owns this atom contract only. It does not change mechanics and does
not define the resolver logic that composes mechanic parameters.

Issue #363 owns composition from atoms to mechanic parameters. For SourceHut,
that follow-on work inherits these formulas:

```text
todo_query_url = https://todo.${GROUNDWORK_FORGE_ENDPOINT}/query
git_query_url = https://git.${GROUNDWORK_FORGE_ENDPOINT}/query
ssh_remote = git@git.${GROUNDWORK_FORGE_ENDPOINT}:~${GROUNDWORK_FORGE_OWNER}/${GROUNDWORK_FORGE_NAME}
```

GitHub composition differs because GitHub does not use the same per-service
subdomain topology; that is #363 scope, not this contract.

## Binding Modes

Interactive sessions set these variables in the repo or session environment.
Autonomous sessions receive them from runa at session construction. In both
modes, consumers read the same atom names and derive composed values from those
atoms instead of re-deriving forge access from memory or hardcoding deployment
endpoints.
