---
name: forge-resolution
description: >-
  Resolve forge-invariant operation handles to exactly one active-forge C-3
  mechanic using GROUNDWORK_FORGE, with shell-safe parameter rendering for
  existing default_invocation pipelines.
metadata:
  version: "1.0.0"
  updated: "2026-06-02"
---

# Forge Resolution

Use this skill when a protocol names a forge-invariant operation such as
`deliver-change-proposal`, `apply-approved-change`, `reflect-disposition`, or
`close-out`.

Run the installed resolver from this skill directory:

```bash
python3 -m tooling.forge_resolution close-out
```

The resolver reads `GROUNDWORK_FORGE`, defaulting to `github` when the variable
is absent. It resolves the operation against the pinned installed
`manifest.toml` and `mechanics/` snapshot copied with this skill.

To invoke a mechanic through the existing C-3 shell-string format, pass
`--invoke` with `--param name=value` arguments. Parameter values are rendered as
shell-safe literals before the mechanic's `default_invocation` pipeline runs.
