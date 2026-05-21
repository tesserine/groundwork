## Interactive IO Adapter

This installed protocol entry is running in an interactive Claude Code or Codex
session, not in a runa-served protocol session. The protocol body below remains
the runa-served source of truth. This adapter supplies the interactive delivery
substitution for the one contract that differs.

When the protocol says to deliver a produced artifact by invoking its runa MCP
tool, produce the same artifact payload and render the same tool-input object in
the terminal for the human. The human reads that output and carries continuity
to any later protocol. Interactive sessions have no artifact store and no
autonomous downstream protocol.

Do not require runa or MCP tools in interactive mode. Do not write workspace
JSON files directly. Do not claim that the artifact was validated, persisted,
or recorded in runa's artifact store.

Interactive delivery is complete when the produced artifact is visible in the
terminal for the human as the protocol's executable outcome.

