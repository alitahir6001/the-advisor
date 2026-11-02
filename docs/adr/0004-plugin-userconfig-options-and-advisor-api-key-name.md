---
status: accepted
date: 2026-08-15
---
# Plugin `userConfig` options for settings; the key option is named `ADVISOR_API_KEY`

## Context and Problem Statement
Settings originally meant hand-editing the installed copy's `.mcp.json` in the plugin cache, which is what actually runs and is replaced on every version bump (CLAUDE.md gotcha 1). Claude Code plugins support `userConfig` options, but an unset option substitutes as `""`, not as absent, and that empty value shadows any inherited shell variable (CLAUDE.md gotcha 8).

## Considered Options
* Hand-edit the cached `.mcp.json`
* `userConfig` options substituted into `.mcp.json`
* Name the key option after the vendor variable, `ANTHROPIC_API_KEY` (inferred from CLAUDE.md gotcha 8)

## Decision Outcome
Chosen option: "`userConfig` options, with the key option named `ADVISOR_API_KEY`", because options are discoverable and stored outside the cache, so they survive version bumps (082812c; CLAUDE.md gotcha 1). The distinct name means an unset option cannot blank out an existing `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` in the shell; the server reads `ADVISOR_API_KEY` first, then the vendor variable, and treats `""` as absent by using `or` instead of a `get()` default (2241df8; CLAUDE.md gotcha 8).

### Consequences
* Good, because setup happens at install with `--config`, and existing shell setups keep working.
* Good, because `${user_config.KEY}` also substitutes in `command`, which makes a `python_command` option possible (CLAUDE.md gotcha 14).
* Bad, because every config read must treat `""` as unset; a blank-config test guards this (853efc2).

## More Information
Evidence: 082812c, 2241df8, 853efc2; CLAUDE.md gotchas 1, 8, 14. Desktop-app limits of `userConfig`: [ADR-0010](0010-identity-independent-the-advisor-dir.md).
