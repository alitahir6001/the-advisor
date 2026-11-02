---
status: accepted
date: 2026-08-11
---
# Stateless advisor: it sees only `question` and `context`, never the session

## Context and Problem Statement
The advisor can be any provider, including non-Claude models that cannot read the workhorse's files or session (92de4a7, README.md:100-103 at that commit). The question was whether the advisor should get session history or other state, or only what the workhorse sends it.

## Considered Options
* Stateless: the tool takes two strings, `question` and `context`, and nothing else
* Server-side state shared across consults (raised later for parallel subagent consults)

## Decision Outcome
Chosen option: "Stateless", because it forces the workhorse to articulate the problem, and because `context` is all a non-Claude advisor can know (92de4a7, README.md:100-103 at that commit). Server-side state was later rejected for parallel subagent consults because it "undoes the stateless design" and still cannot reconcile conflicting answers (`.ai/backlog.md:42-44`).

### Consequences
* Good, because any provider works the same way, and every consult is reproducible from its logged `question` and `context`.
* Bad, because the workhorse must put the relevant code and constraints into `context` itself (CLAUDE.md gotcha 30).

## More Information
Evidence: 92de4a7 (README.md:100-103 at that commit); `server/advisor_server.py:30-39` (`TOOL_DESCRIPTION`, "stateless" at line 36); `.ai/backlog.md:42-44`. Enforced for `anthropic-cli` by [ADR-0014](0014-tool-less-single-turn-advisor.md).
