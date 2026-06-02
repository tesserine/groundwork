---
name: forge-operation
description: Resolve and invoke Groundwork forge-invariant operation handles through the active forge mechanic.
---

# Forge Operation

Use this skill when a protocol names a forge-invariant operation such as
`deliver-change-proposal`, `apply-approved-change`, `reflect-disposition`, or
`close-out`.

Run `groundwork-forge-operation` from this skill directory in installed
sessions. It resolves the operation against `GROUNDWORK_FORGE`, defaulting to
`github` when the variable is absent. Pass `--forge` only for standalone tests
or explicit local override.

Use `render` to inspect the resolved command and `invoke` to run it:

```bash
python groundwork-forge-operation resolve close-out
python groundwork-forge-operation render close-out --param name=value
python groundwork-forge-operation invoke close-out --param name=value
```

Do not embed forge-specific commands in protocol bodies. Keep GitHub,
SourceHut, and other forge-specific procedures inside C-3 mechanics.
