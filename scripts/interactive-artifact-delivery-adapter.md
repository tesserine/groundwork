<!-- groundwork-install:interactive-artifact-delivery-adapter begin -->
## Interactive Artifact Delivery Adapter

Interactive sessions have no runa runtime, MCP artifact tool, artifact store,
or automatic downstream threading. When this projected protocol reaches a
runa-served delivery step, substitute this adapter for the complete runa-served
artifact delivery transform.

Do not call the MCP tool in interactive mode. Assemble and present the produced
artifact body: the artifact object as this protocol and its schema define it
after runa would have consumed tool-only parameters and injected session
context. Present that artifact body to the human in the terminal. The object
presented to the human is not the MCP tool-input object shown in the protocol
body.

`instance_id` is tool-only identity metadata for runa-served delivery. In
interactive mode, consume it as optional human continuity metadata outside the
artifact body if it helps name the output, but `instance_id` must not appear
inside the artifact body.

`work_unit` exists only when the produced artifact is scoped to a work unit.
For scoped artifacts, fill `work_unit` from the active interactive work-unit or
session context when it is unambiguous. If no single active work unit is clear,
ask the human for the work-unit identity before presenting the artifact body.
For unscoped artifacts, do not add `work_unit`.

Interactive delivery is complete when the schema-shaped artifact body has been
presented to the human. Interactive mode does not persist artifacts, does not
create workspace JSON files, and does not thread artifacts automatically to
downstream protocols.
<!-- groundwork-install:interactive-artifact-delivery-adapter end -->
