---
status: accepted
date: 2026-08-11
---
# Escalation rule lives on the agent description, not the MCP tool schema

## Context and Problem Statement
The plugin tells the workhorse when to consult the advisor. That rule could sit on the `consult_advisor` MCP tool's schema or on the `agents/advisor.md` agent description. Tool schemas can be deferred out of context until something searches for them, and a rule the model never sees cannot fire (92de4a7, README.md:107-110 at that commit).

## Considered Options
* Put the rule on the MCP tool schema
* Put the rule on the agent description in `agents/advisor.md`

## Decision Outcome
Chosen option: "Agent description", because it is always loaded, while the tool schema may not be. Testing overturned the opposite design (92de4a7, README.md:107-110 at that commit; `.ai/rules.md:52-55`).

### Consequences
* Good, because the guidance is in context whenever the agent list is.
* Bad, because agent-description text is treated as a routing hint, not a standing policy; proactive escalation was later measured not to fire (CLAUDE.md gotcha 28).

## More Information
Evidence: 92de4a7 (README.md:107-110 at that commit); `.ai/rules.md:52-55`. The placement still stands. The original "MUST consult" mandate wording is superseded by [ADR-0008](0008-retract-must-consult-escalation-wording.md).
