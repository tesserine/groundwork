# Groundwork Skill Ontology Row 1 Audit

## Purpose

This note is the row-1 audit for
[#468](https://github.com/tesserine/groundwork/issues/468). It applies the
method fixed in
[`skill-ontology-and-core-protocol-seam.md`](skill-ontology-and-core-protocol-seam.md)
to Groundwork's own `skills/` and `protocols/` assets at source head.

The result is provisional architecture evidence for epic
[#466](https://github.com/tesserine/groundwork/issues/466), not ADR-0007.
Row 1 classifies Groundwork only. Row 2, the gazette pass, extends this table
before the ADR distills the seam.

## Method

The audit reads the 18 live row-1 assets: 9 skills under `skills/` and 9
protocols under `protocols/`. Each asset is placed on the two axes from the
foundation note:

- domain coupling: `universal` or `domain:software`
- form: `skill` or `protocol`

The membership test is projection to another methodology domain. The concrete
target is gazette as it exists now: a non-code runa methodology with a
`manifest.toml` and schemas, a `survey` protocol name in common, and editorial
artifact types such as `brief`, `beat`, `dispatch`, `draft`, `grounding`,
`issue`, and `ledger`, but no `skills/` tree to carry a duplicated cognitive
core. A row-1 asset is universal when that non-code methodology can reuse the
discipline without inheriting software-delivery artifacts. It is
`domain:software` when the asset's meaning depends on work-units, change
proposals, code review, implementation tests, forge mechanics, or the
Groundwork scoped pipeline.

## Groundwork Row

| Asset | Kind | Domain Coupling | Form | Membership-Test Ground |
|---|---|---|---|---|
| acquire | skill | domain:software | skill | Gazette or another non-code methodology may need entry from an existing planning record, but this skill materializes a forge ticket as a `work-unit` snapshot with a `handle` for `take`. |
| code-review | skill | domain:software | skill | Gazette needs independent quality judgment, but code-review's criteria are software-specific: behavior regressions, schemas, interfaces, tests, and documentation impact for code changes. |
| contract | skill | universal | skill | Gazette or another domain still needs an executable definition of done across behavior, documentation, and quality dimensions; only the evidence form changes. |
| debug | skill | universal | skill | Root-cause-before-fix applies to non-code failures as well as software failures; gazette grounding or publication failures still need evidence before correction. |
| orient | skill | universal | skill | Another domain needs the methodology map, graph-first orientation, and documentation audience discipline without adopting Groundwork's delivery pipeline. |
| reckon | skill | universal | skill | First-principles grounding and traceable reasoning are domain-neutral; gazette's editorial choices also need constraints before inherited frames. |
| research | skill | universal | skill | Systematic external-evidence gathering projects directly to non-code work, including gazette's source and historical evidence questions. |
| resolve | skill | universal | skill | Structural friction resolution applies whenever tooling, configuration, convention, or process blocks work in another domain. |
| work-unit-craft | skill | universal | skill | Another domain still needs delegation-record craft: outcome-first records, body-as-spec authority, and criteria that transfer intent across contexts. The artifact name may change. |
| decompose | protocol | domain:software | protocol | The cognitive craft projects, but this shell produces `work-unit` artifacts and tracker-backed handles, not gazette's non-code artifact crossings. |
| implement | protocol | domain:software | protocol | Another domain can reuse test-first construction, but this shell consumes implementation plans and emits `test-evidence` for software work-unit behavior. |
| land | protocol | domain:software | protocol | Another domain can reuse governance closure, but this shell applies approved software change proposals, reflects forge disposition, and emits a `completion-record`. |
| plan | protocol | domain:software | protocol | Another domain can reuse decision-complete planning, but this shell maps Groundwork contracts to implementation plans for the scoped software pipeline. |
| review | protocol | domain:software | protocol | Another domain can reuse independent judgment, but this shell routes Groundwork `change-proposal` artifacts through `change-approved` or `change-needs-revision`. |
| submit | protocol | domain:software | protocol | Another domain can reuse proposal packaging, but this shell delivers verified software changes through forge mechanics into a `change-proposal`. |
| survey | protocol | domain:software | protocol | The inquiry discipline projects and gazette also has a `survey` protocol, but this shell transforms `intent` into Groundwork `requirements`. |
| take | protocol | domain:software | protocol | Another domain can reuse contract-first entry, but this shell claims a work-unit issue, prepares a feature branch, and authors a `contract` for a software work-unit. |
| verify | protocol | domain:software | protocol | Another domain can reuse evidence-before-claim, but this shell gates software completion with `completion-evidence` tied to work-unit criteria, tests, and documentation review. |

## Protocol Reduction Test

Row-1 answer to "holds for 100% of cases?": No. Each protocol exposes a
cognitive band through a Groundwork-specific typed shell, but none reduces
fully to the universal candidate because each row keeps domain wrapper
obligations in the protocol boundary.

| Protocol | Universal Candidate | Reduction | Reason |
|---|---|---|---|
| decompose | work-unit-craft | no | The protocol body uses the work-unit-craft discipline, but delivery of `work-unit` artifacts and tracker identity remains in the protocol shell. |
| implement | test-driven-implementation | no | The cognitive band is RED-GREEN-REFACTOR, but the shell binds it to implementation-plan input and `test-evidence` output. |
| land | governance-closure | no | The cognitive band is approved-version closure, but forge apply, disposition reflection, and `completion-record` delivery remain the domain wrapper. |
| plan | decision-complete-planning | no | The cognitive band is convergence before mutation, but the wrapper maps Groundwork gates or scenarios to an `implementation-plan`. |
| review | quality-review | no | The protocol depends on `code-review`, a software projection. The universal quality-review parent is predicted but not yet extracted. |
| submit | proposal-submission | no | The cognitive band is packaging verified work for review, but forge delivery and `change-proposal` shape are wrapper concerns. |
| survey | disciplined-inquiry | no | The cognitive band is separating descriptive state from normative need, but the wrapper turns `intent` into `requirements`. |
| take | contract-first-entry | no | The core band is contract-first entry, but the current body also owns workspace preparation, tracker claiming, and temporary carry-through to later stations. |
| verify | evidence-gate | no | The cognitive band is evidence before completion claims, but the wrapper records Groundwork gate or scenario coverage in `completion-evidence`. |

## Projection Seams

The current row has two domain-specific skills. Both point at universal
parents that row 1 predicts but has not yet extracted as standalone source
skills.

| Domain Skill | Domain Scope | Projects From | Inherited Discipline | Domain Delta |
|---|---|---|---|---|
| acquire | domain:software | acquisition | Materialize an execution artifact from an authorized planning record without fabricating content. | Reads a forge ticket, preserves `handle`, derives a `work-unit` body, and hands execution to `take`. |
| code-review | domain:software | quality-review | Judge proposed work against scope, contract, evidence, and recipient impact before approval. | Adds software-specific correctness checks: code semantics, schemas, interfaces, tests, regressions, and current documentation accuracy. |

## Lateral Harmonics

| Atomic Bead | Kin Assets | Shared Invariant | Extraction Value |
|---|---|---|---|
| Ground before design | reckon, survey, decompose, plan, work-unit-craft | The current substrate is evidence, not the need; the next artifact must derive from verified constraints. | High: shared by the planning front and record-craft surfaces. |
| Contract carries forward | contract, take, plan, implement, verify, review, land | Validation defined at entry remains the measure through planning, execution, evidence, judgment, and close. | High: this is the pipeline's spine and the clearest single-home pressure. |
| Evidence before claim | debug, implement, verify, review, land | A claim is accepted only after fresh evidence or an independent finding decides it. | High: repeated across failure handling, build, completion, review, and governance. |
| Artifact delivery boundary | decompose, take, plan, implement, verify, submit, land | Tool parameters are not artifact body, `work_unit` injection is scoped, and runa validates the remaining body fields. | Medium: repeated protocol-shell text points at an extractable delivery wrapper discipline. |
| Forge containment | acquire, decompose, submit, land | Provider-specific operations stay in mechanics and handles, while protocol and skill language stays forge-invariant. | Medium: strongest where tracker or proposal mechanics touch the outside world. |

## Mendeleev Gaps

| Predicted Position | Properties Implied | Missing Asset |
|---|---|---|
| Universal parent of `code-review` and gazette `factcheck` | Independent quality judgment over a proposal or artifact, using scope, evidence, recipient impact, and domain-specific correctness as projections. | `quality-review` skill |
| Universal parent of `acquire` | Faithfully materialize an execution-scoped artifact from an existing authoritative planning record, surfacing gaps instead of inventing content. | `acquisition` skill |
| Universal shell authoring discipline | Explain how a typed protocol wraps one cognitive skill, owns only the artifact crossing, and leaves composition below the shell. | `protocol-shell-craft` skill |
| Shared artifact-delivery wrapper | State the MCP tool input boundary, `instance_id` extraction, scoped `work_unit` injection, and artifact-body validation once for producer protocols. | `artifact-delivery` reference or skill |
| Universal governance close | Close a unit only from an approved disposition, bind the approved version, record performed validation, and surface any gaps. | `governance-closure` skill |

## Distilled-Table Crossings

| Pairing | Behavioral Invariant | Convergence |
|---|---|---|
| Typed artifact crossings and periodic-table position | A position determines properties: protocol behavior follows from the required and produced artifact boundary. | Converges structurally; row 1 does not claim chemical period counts. |
| Lateral harmonics and chromatic intervals | The same sub-move recurs at the same relative position across different parents. | Converges: grounding, evidence, contract carry, and delivery-boundary moves recur across siblings. |
| Universal-to-projection seams and the principles graph | A projection inherits the universal and adds only a marked domain delta. | Converges: `code-review` and `acquire` reveal the relation most clearly by needing missing universal parents. |
| Distilled tables and row-1 asset counts | Useful cuts should predict missing positions from structure, not fit assets into prechosen numbers. | Diverges as evidence for exact numbers; the open numbers question remains unresolved by row 1. |

## Substrate Fine-Tuning Findings

| Finding | Witness Marks | Disposition |
|---|---|---|
| `review` is graded by the domain-skill graduation, not the wrapped-universal graduation. | `protocols/review` names `skills/code-review` as its evaluation discipline, while the foundation note predicts domain review skills project from a universal quality-review parent. | Surface for row 2 and ADR-0007; do not extract in this unit. |
| `take` carries temporary station-bridging content in addition to contract-first entry. | `protocols/take` owns workspace preparation and says it must carry through later stations until runtime sequencing is wired. | Record as a substrate fine-tuning candidate; no protocol rewrite in this unit. |
| `decompose` and `work-unit-craft` still duplicate substantial record-craft teaching. | `protocols/decompose` contains the same outcome-first record discipline that `skills/work-unit-craft` owns. | Candidate for the factoring work after the seam ADR. |
| Producer protocols repeat artifact-delivery shell language. | The producer protocols share the same `instance_id`, MCP-input, scoped `work_unit`, and validation boundary paragraphs. | Candidate extraction to a protocol-shell or delivery-wrapper reference. |

## Row 2 Extension Shape

Row 2 extends this artifact by appending gazette assets without rewriting row
1. The extension should keep the same columns for the asset row:

- `Asset`
- `Kind`
- `Domain Coupling`
- `Form`
- `Membership-Test Ground`

It should then add gazette protocol reductions, gazette domain projections,
new harmonics, and any changed Mendeleev gaps. Row 2 decides whether the
row-1 predicted parents hold across a second domain. ADR-0007 should consume
the combined row evidence, not this row alone.
