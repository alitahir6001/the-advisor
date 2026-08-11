---
name: consult-advisor-cli
description: Get a second opinion from an advisor model OUTSIDE this session
  via a vendor CLI — Anthropic (claude -p), Google (gemini), or OpenAI
  (codex, if installed). Use for one-off consults to a specific provider or
  model the user names, when the configured consult_advisor MCP tool isn't
  registered or doesn't cover that provider. Same escalation bar as
  consult_advisor - architectural or hard-to-reverse decisions, twice-failed
  fixes, unresolvable tradeoffs. Never for routine work.
---

# Consult an advisor via vendor CLI

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

If the chosen CLI is missing or errors on auth, report that and fall back
to the advisor subagent — do not silently skip the consult.

## Apply the advice

Weigh the recommendation against repo reality (the advisor can't read this
project). State in your reply that you consulted, which provider/model
answered, and whether you followed the advice.
