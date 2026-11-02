---
status: accepted
date: 2026-10-13
---
# `--effort max` by default on `anthropic-cli`, with an `ADVISOR_EFFORT` override

## Context and Problem Statement
`claude -p` inherits the global `effortLevel` unless `--effort` is passed. A `doctor --live` consult ran the advisor at `effort=medium` from the author's own settings, the same shape as the model inheritance in gotcha 17 (CLAUDE.md gotcha 29). The advisor is meant to be the stronger model, so running it at the user's daily effort level defeats the point.

## Considered Options
* Inherit the global `effortLevel` (previous behavior)
* Send `--effort max` by default, with an `ADVISOR_EFFORT` option to override
* A file-based override like the model's (rejected; CLAUDE.md gotcha 29)

## Decision Outcome
Chosen option: "`--effort max` by default, `ADVISOR_EFFORT` override", because the advisor should not run as weak as the daily driver (`server/advisor_server.py:44-46`). `cli-default` sends no flag, which is also the escape hatch for a `claude` too old to know it. No file override is needed because the default needs no config, so the desktop-app identity bug cannot block it (CLAUDE.md gotcha 29).

### Consequences
* Good, because the advisor reasons at full strength without any setup.
* Bad, because max effort makes consults slow and costly; see [ADR-0014](0014-tool-less-single-turn-advisor.md).
* Neutral: `anthropic-cli` only. The log records `effort`/`effort_source` there and `None` for other providers, so it never claims an effort that was not sent (CLAUDE.md gotcha 29).

## More Information
Evidence: add2940 (`advisor_effort` option), fbdebb7 (passed to the server), 55cdad7 (max default); `server/advisor_server.py:44-46`; CLAUDE.md gotchas 17, 29.
