---
status: accepted
date: 2026-10-14
---
# Tool-less, single-turn advisor with a 1800s timeout

## Context and Problem Statement
`claude -p` ran the advisor as a full agent in the caller's working directory. A real consult made 19 Bash/Read calls and was killed at the 300s timeout, because each tool call re-sent the context and cost another max-effort think. That also contradicted the tool description's promise that the advisor is stateless and sees only what it is sent (CLAUDE.md gotcha 30; [ADR-0001](0001-stateless-advisor-sees-only-question-and-context.md)).

## Considered Options
* Agentic advisor with tools (previous behavior)
* Lower the effort to make consults faster (rejected by the user; `.ai/history.md` session 8)
* Tool-less, single turn, with a longer timeout and a warning to callers

## Decision Outcome
Chosen option: "Tool-less, single turn", using `--strict-mcp-config --tools ""` with the variadic `--tools` kept last (7045b5e; `server/advisor_server.py:48-50`). The timeout went from 300s to 1800s, and the tool description warns that a hard question can take several minutes at max effort (3667ede; `server/advisor_server.py:37-38`). Max-effort thinking is the real cost: replays of the same question took 309s to 530s, so consults of 3-9 minutes are accepted over lowering effort (CLAUDE.md gotcha 30; `.ai/history.md` session 8).

### Consequences
* Good, because the advisor is actually stateless and a consult is one bounded call.
* Bad, because the workhorse must send the relevant code in `context`, and consults take minutes.
* Bad, because Claude Code's MCP call limit is measured only to about 414s; beyond that it is unmeasured (CLAUDE.md gotcha 30).

## More Information
Evidence: 7045b5e, 3667ede; `server/advisor_server.py:37-38, 48-50`; CLAUDE.md gotcha 30; `.ai/history.md` session 8. Scope: `anthropic-cli` only. The Gemini CLI path has the same exposure and still runs with tools (CLAUDE.md gotcha 30). Related: [ADR-0013](0013-max-effort-default-for-anthropic-cli.md).
