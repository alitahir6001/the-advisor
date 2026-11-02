# Architecture Decision Records

This folder records the design decisions that shape The Advisor and why they were made, one file per decision (MADR 4.0).

- [0001](0001-stateless-advisor-sees-only-question-and-context.md) - Stateless advisor: it sees only `question` and `context`, never the session - accepted - 2026-08-11
- [0002](0002-escalation-rule-on-agent-description-not-tool-schema.md) - Escalation rule lives on the agent description, not the MCP tool schema - accepted (mandate wording superseded by ADR-0008) - 2026-08-11
- [0003](0003-no-default-model-ids.md) - No default model IDs in the server, `.mcp.json`, or agent frontmatter - accepted - 2026-08-11
- [0004](0004-plugin-userconfig-options-and-advisor-api-key-name.md) - Plugin `userConfig` options for settings; the key option is named `ADVISOR_API_KEY` - accepted - 2026-08-15
- [0005](0005-base-url-makes-api-key-optional.md) - `openai-compatible` provider: `ADVISOR_BASE_URL` makes the API key optional - accepted - 2026-08-15
- [0006](0006-refuse-unset-advisor-model-cli-default-opt-in.md) - Refuse an unset `ADVISOR_MODEL`; `cli-default` is the explicit opt-in - accepted - 2026-09-05
- [0007](0007-rename-advisor-command-to-consult.md) - Rename `/advisor` to `/consult` and position as a complement to the native Advisor - accepted - 2026-09-05
- [0008](0008-retract-must-consult-escalation-wording.md) - Retract the "MUST consult" escalation wording - accepted - 2026-09-07
- [0009](0009-provenance-in-consult-log-not-reply-header.md) - Record `model_source`/`provider_source` in the consult log only - accepted - 2026-09-07
- [0010](0010-identity-independent-the-advisor-dir.md) - Fixed, identity-independent `~/.the-advisor/` for the model override and consult log - accepted - 2026-09-06
- [0011](0011-infer-provider-from-model-name.md) - Detect the provider from the model name or base URL; explicit `ADVISOR_PROVIDER` wins - accepted - 2026-09-05
- [0012](0012-two-tier-doctor-with-skill.md) - Two-tier `doctor.py` (free default, `--live` opt-in ship gate) plus a `/doctor` skill - accepted - 2026-09-07
- [0013](0013-max-effort-default-for-anthropic-cli.md) - `--effort max` by default on `anthropic-cli`, with an `ADVISOR_EFFORT` override - accepted - 2026-10-13
- [0014](0014-tool-less-single-turn-advisor.md) - Tool-less, single-turn advisor with a 1800s timeout - accepted - 2026-10-14

Citations to `.ai/` files point at maintainer notes in the repo's `.ai/` directory.
