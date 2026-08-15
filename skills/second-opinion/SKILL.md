---
name: second-opinion
description: Get a second opinion from a specific advisor model the user
  names, run outside this session via a vendor CLI — Anthropic (claude -p),
  Google (gemini), or OpenAI (codex, if installed). Use for ad-hoc routing to
  a provider or model that is not in the configured .mcp.json, or that the
  consult_advisor MCP tool has no provider for. The user picks the provider,
  so there is no escalation bar - any question they route here qualifies.
---

# Second opinion from a named provider

## Prefer the MCP tool when it already covers the provider

If `consult_advisor` is registered and its configured provider is the one
being asked for, use it instead. It logs the consult and scrubs the
subprocess environment; this skill does neither. Come here when the user
names a provider or model the server is not configured for.

## Package the consult

Build ONE focused prompt. The advisor is stateless — it sees nothing but
what you send. Include:

1. The question (one decision or problem, not the whole task)
2. Minimal context: options on the table, constraints, what was already tried
3. This output contract, verbatim:
   "Reply with: Recommendation (one clear choice), Reasoning (2-4
   load-bearing points), Risks (what could make this wrong). Do not
   write code."

## Run it

Pick the CLI for the provider you want. Run via Bash, passing the packaged
prompt as one quoted argument:

- Anthropic (bills Claude subscription):
  `claude -p "<packaged prompt>" --model <model>`
- Google (gemini CLI, free personal tier or its own billing):
  `gemini -p "<packaged prompt>"`
- OpenAI (only if `codex` is installed; bills ChatGPT subscription):
  `codex exec "<packaged prompt>"`

Unlike the MCP path, this inherits the session's environment. `claude -p`
run this way sees the parent session's `CLAUDE*` variables and may behave
as a nested session; prefer `consult_advisor` for Anthropic consults.

If the chosen CLI is missing or errors on auth, report that and fall back
to the advisor subagent — do not silently skip the consult.

## Apply the advice

Weigh the recommendation against repo reality (the advisor can't read this
project). State in your reply that you consulted, which provider/model
answered, and that this consult is not in the log.
