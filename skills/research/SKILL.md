---
name: research
description: >-
  Systematic multi-source research with citations and synthesis. Use when a
  decision depends on facts outside the codebase — library behavior, version
  compatibility, ecosystem practice, external evidence of any kind. Fires at
  any stage: framing, design, planning, and implementation can all require
  it.
metadata:
  version: "2.0.0"
  source: internal
  updated: "2026-06-11"
---

# Research

Structured, multi-source research that ends in a cited, decisive answer.

## Principles

1. **Start simple, escalate when needed.** Focused searches before broad
   sweeps; complexity only when simpler approaches fail.
2. **Three-source rule.** Never trust a single source. Cross-reference with
   at least two independent sources before treating information as
   reliable.
3. **Version everything.** Most source conflicts dissolve when versions and
   dates are explicit. Anchor findings to specific versions and timestamps.
4. **Empirical verification over authority.** When stakes are high, test
   claims directly. Code behavior beats documentation.
5. **Conclude decisively.** "It depends" helps no one. State the answer,
   the confidence, and the limitations.

## Steps

1. **Clarify.** Identify the core question, scope, output format, and
   constraints. If the query is vague, ask before searching — researching a
   vague question wastes cycles on wrong targets. Skip this when the
   question is already specific: if you can write the sub-questions without
   asking anything, move on.

2. **Decompose.** Break the question into 3–5 independently searchable
   sub-questions that together form a complete picture. Each maps to at
   least one source; independent sub-questions fire as parallel searches.

3. **Gather.** Consult sources in priority order — official docs, issue
   trackers, curated Q&A, source code, blogs, community — recording URL,
   date, version, and key claims for each. When the topic intersects the
   current codebase, read the relevant source first. Tool driving and
   query patterns:
   [references/source-strategy.md](references/source-strategy.md).

4. **Evaluate.** Weigh sources by the trust hierarchy (empirical behavior >
   versioned official docs > maintainer statements > curated answers >
   blogs > forums) and discard red-flag material — undated, unversioned,
   contextless, or circular.

5. **Resolve conflicts.** Check versions first (most "conflicts" are
   version skew); find the maintainer's statement; deep-read both sides;
   test empirically when possible; weight broader consensus; and if still
   unresolved, report both positions with evidence.

6. **Synthesize.** Every factual claim cited; quantitative over
   qualitative; a direct answer with an honest confidence assessment;
   conflicts surfaced, not hidden. Output structure:
   [references/synthesis-template.md](references/synthesis-template.md).

## Quality Checklist

Before concluding research, verify:

- [ ] Core question answered directly and specifically
- [ ] 3+ diverse sources consulted; all claims cited with URLs
- [ ] Version/date noted for time-sensitive information
- [ ] Conflicting sources investigated and explained, not hidden
- [ ] Conclusion concrete, confidence stated with reasoning
- [ ] Limitations and caveats acknowledged

## Persisting Findings

Research output stays in conversation by default. When findings should
persist, deliver a `research-record` artifact through the active protocol
session (protocols that accept research declare the tool), or follow the
project's knowledge conventions. Persistence is a decision, not a default.

## Cross-References

- `reckon` (skill): research supplies the verified evidence reckoning
  builds from; reckon decides what question is worth researching.
- `plan` (protocol): design decisions that depend on external facts cite
  research findings in their rationale.
