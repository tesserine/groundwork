# Source Strategy

Reference for research Phases 3–5: where to look, how to drive the search
tools, and how to weigh what they return.

## Source Priority

| Source Type | Strengths | Best For | Tavily Strategy |
|-------------|-----------|----------|-----------------|
| **Official Docs** | Authoritative, maintained | API signatures, core concepts | `include_domains` targeting official site |
| **GitHub Issues/PRs** | Real problems, maintainer input | Edge cases, bugs, workarounds | `include_domains: ["github.com"]` |
| **Stack Overflow** | Curated answers, voting signal | Common problems, quick fixes | `include_domains: ["stackoverflow.com"]` |
| **Source Code** | Ground truth | When docs are unclear | Read source directly |
| **Blog Posts** | Deep dives, tutorials | Learning workflows, context | General search, then `tavily-extract` |
| **Discord/Forums** | Cutting-edge, insider knowledge | Latest changes, community consensus | `include_domains` targeting community sites |

For each source, record: URL and access date; version/date of the
information; author credibility indicators; key claims with direct quotes
when significant.

## Tavily

### `tavily-search` — discovery

Sub-questions are independent: fire multiple searches simultaneously, each
with its own query and domain filter. Escalate depth only when needed:

1. First pass: `search_depth: "basic"`, `max_results: 10`
2. Thin or off-target: `search_depth: "advanced"`, `max_results: 15`
3. Still inadequate: narrow with `include_domains` or broaden the query

### `tavily-extract` — deep reading

- Snippet answers the question → don't extract, move on.
- Snippet promising but incomplete → extract that URL.
- Verifying a specific claim in context → extract the source.
- Comparing multiple in-depth sources → batch extract all candidates in
  one call: `tavily-extract(urls: [url1, url2, url3])`.

### Fallbacks

- `WebFetch`: a URL Tavily cannot parse, a user-provided URL, or when
  markdown output aids readability.
- `WebSearch`: a second engine perspective — independent corroboration for
  the three-source rule, or different ranking signals.

## Trust Hierarchy (highest to lowest)

1. Source code behavior (empirical test)
2. Official docs with version tags
3. Maintainer statements in issues/PRs
4. Highly upvoted + recently active Stack Overflow
5. Blog posts with working code examples
6. Unverified forum posts

**Red flags:** no version/date; code examples without imports; "this worked
for me" with no context; confident but detail-free; circular references
between sources.

## Capturing Practical Wisdom

Official docs miss the power-user moves. Target them:

| Pattern | Query Template | Filter |
|---------|---------------|--------|
| GitHub issue archaeology | `[tech] workaround OR hack OR trick` | `github.com` |
| Maintainer statements | `[tech] [problem] fix OR resolved` | `github.com`, advanced depth |
| Stack Overflow deep cuts | `[tech] [problem] note that OR also need to` | `stackoverflow.com` |
| Recent developments | `[tech] [feature] announcement OR release` | `time_range: "month"` |
| Breaking changes | `[tech] breaking change OR migration guide` | `topic: "news"` |
| Config wisdom | `[tool] dotfiles OR awesome-[tool] config` | `github.com` |

Emotional language signals hard-won knowledge: "Finally!", "After hours of
debugging...", "The trick is...", "What the docs don't tell you..."
Capture with context: `[Problem] / [Source + date] / [Version] / [Solution] / [Caveats]`.
