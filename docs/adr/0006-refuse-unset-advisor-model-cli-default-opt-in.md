---
status: accepted
date: 2026-09-05
---
# Refuse an unset `ADVISOR_MODEL`; `cli-default` is the explicit opt-in

## Context and Problem Statement
With no model set, CLI providers fell back to the CLI's own default (92de4a7, `server/advisor_server.py:145` at that commit). `claude -p` with no `--model` reads the user's global `settings.json`, so the advisor silently became the same model as the workhorse; the log still looked fine, and 16 real consults ran this way before billing caught it (CLAUDE.md gotchas 11, 17).

## Considered Options
* Silent fallback to the CLI default (shipped)
* Refuse to consult when the model is unset, with `cli-default` as an explicit opt-in to the fallback

## Decision Outcome
Chosen option: "Refuse, with `cli-default` as the opt-in", because an unset `ADVISOR_MODEL` is more often an accident than intent (`server/advisor_server.py:41-42`). Every provider refuses, the error names the fix, and the refusal is logged (fc2e0f0, 41fa789).

### Consequences
* Good, because a misconfigured install fails loudly instead of quietly giving the workhorse a second opinion from itself.
* Bad, because an install with no model set does nothing until the user configures one.

## More Information
Evidence: fc2e0f0, 41fa789; `server/advisor_server.py:41-42`; CLAUDE.md gotchas 11, 17. Related: [ADR-0003](0003-no-default-model-ids.md).
