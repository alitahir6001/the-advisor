---
name: consult-advisor-cli
description: Deprecated alias for the second-opinion skill, kept so existing
  /consult-advisor-cli invocations still resolve. Removed at 0.2.0. Do not
  select this on your own - invoke the second-opinion skill instead.
---

# Deprecated — use `second-opinion`

This skill was renamed: it and the MCP server's `anthropic-cli` /
`gemini-cli` providers both said "CLI", which read as duplication. The real
distinction is configured (MCP) versus ad-hoc (this skill).

Invoke the `second-opinion` skill and follow it instead. Tell the user the
command is now `/second-opinion`, once, then carry on with their question —
do not make them retype it.
