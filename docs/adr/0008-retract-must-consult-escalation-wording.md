---
status: accepted
date: 2026-09-07
---
# Retract the "MUST consult" escalation wording

## Context and Problem Statement
`agents/advisor.md` told the workhorse it MUST get a second opinion before hard-to-reverse decisions ([ADR-0002](0002-escalation-rule-on-agent-description-not-tool-schema.md)). A clean test showed a fresh top-level session could see the mandate and said it would follow it, then made zero tool calls on a real qualifying decision; Task-tool subagents never see the mandate at all (CLAUDE.md gotcha 28). Shipping a promise that does not fire was judged the same defect class as earlier "looked like it worked" failures (`.ai/history.md`, session 7).

## Considered Options
* Keep the mandate wording
* Add a plan-mode-exit hook to trigger a consult (`.ai/backlog.md:19`)
* Add a session-end hook running a cheap classifier over the final response (`.ai/backlog.md:21`)
* Retract the mandate and describe consulting as on demand

## Decision Outcome
Chosen option: "Retract the mandate", because prose on an agent description is attended to as a routing hint, not a policy, and a real fix needs a deterministic harness hook, not stronger wording (CLAUDE.md gotcha 28). Both hook options were deferred to v1.5/2.0 (`.ai/handoff.md:21`). The description now says the agent will not reliably trigger on its own and should be called explicitly or via `/consult` (6a0f36e; `agents/advisor.md:3-8`).

### Consequences
* Good, because the plugin no longer claims a behavior it does not have.
* Bad, because consulting now depends on the user or the workhorse choosing to ask.

## More Information
Evidence: 6a0f36e; CLAUDE.md gotcha 28; `agents/advisor.md:3-8`; `.ai/history.md` session 7, `.ai/backlog.md:19-21`, `.ai/handoff.md:21`. Supersedes the mandate wording of [ADR-0002](0002-escalation-rule-on-agent-description-not-tool-schema.md); its placement decision still stands.
