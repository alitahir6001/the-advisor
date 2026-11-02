---
status: accepted
date: 2026-08-11
---
# No default model IDs in the server, `.mcp.json`, or agent frontmatter

## Context and Problem Statement
The advisor model is per-user config. A model ID baked into the code or shipped config goes stale and overrides what the user chose. The first commit already kept model IDs out of the server (92de4a7, `server/advisor_server.py:46` at that commit), but the agent frontmatter shipped with a pinned `model:` line.

## Considered Options
* Pin a `model:` in `agents/advisor.md` frontmatter (shipped in 92de4a7)
* No model IDs anywhere in code or shipped config

## Decision Outcome
Chosen option: "No model IDs anywhere", because they go stale and undercut per-user config (`server/advisor_server.py:52`). The pinned `model:` was removed from the agent frontmatter on 2026-08-12 (1dd998f).

### Consequences
* Good, because the advisor is always the model the user configured.
* Bad, because an unconfigured install has no model; see [ADR-0006](0006-refuse-unset-advisor-model-cli-default-opt-in.md) for how that case is handled.

## More Information
Evidence: 92de4a7; 1dd998f; `server/advisor_server.py:52`; CLAUDE.md gotcha 10 (the `userConfig` descriptions in `plugin.json` carry example IDs as help text, not defaults).
