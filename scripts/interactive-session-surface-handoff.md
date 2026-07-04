<!-- groundwork-install:interactive-session-surface-handoff begin -->
## Interactive Session Surface Handoff

Interactive Groundwork protocol sessions are driven through runa's validated
session surface. The operator issues only `go`, invoked as `runa go --work-unit
<canonical-work-unit-id>` from the repository workspace. `go` launches the
configured agent command, and that agent performs the session cascade through
the runa MCP tools.

Inside that cascade, the configured agent calls `next-protocol-context`, follows
the rendered protocol prompt, records the protocol output through the current
output tool, calls `advance`, and stops. For example, a ready `define` step
records `contract` through the current output tool; the operator does not call
`contract` or `advance` beside `go`.

Artifacts produced in interactive mode are validated by runa, persisted in the
runa workspace, and threaded downstream by the same graph rules used in
autonomous mode. Do not assemble artifact bodies manually.
Do not write workspace JSON files directly.
Do not add a separate human approval gate; typed disposition artifacts remain
the lifecycle authority.
<!-- groundwork-install:interactive-session-surface-handoff end -->
