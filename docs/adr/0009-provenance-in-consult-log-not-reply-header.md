---
status: accepted
date: 2026-09-07
---
# Record `model_source`/`provider_source` in the consult log only

## Context and Problem Statement
Every reply already names the advisor model and provider (5747d22). The resolved values alone cannot show which input won, for example the override file versus `ADVISOR_MODEL`, or explicit `ADVISOR_PROVIDER` versus inference, so a stale override shadowing a fresh config change would look identical to a correct resolution (CLAUDE.md gotcha 26).

## Considered Options
* Show the provenance in the user-facing reply header (built, judged noise, pulled; `.ai/history.md` session 7)
* Record the provenance in the consult log only

## Decision Outcome
Chosen option: "Log only", because provenance is a post-mortem and `doctor.py` signal, not something to show the user on every reply (CLAUDE.md gotcha 26). `log_consult()` records `model_source` and `provider_source`; `attribution()` shows only model, provider, and workhorse (bfcb61a; `server/advisor_server.py:111-140`).

### Consequences
* Good, because a wrong-input resolution is diagnosable after the fact without cluttering replies.
* Bad, because the user has to read the log or run `/doctor` to see which input won.

## More Information
Evidence: 5747d22 (reply header), bfcb61a (provenance fields in `log_consult()`), 4d62666 (`TestProvenance` tests); CLAUDE.md gotcha 26; `.ai/history.md` session 7. Related: [ADR-0012](0012-two-tier-doctor-with-skill.md).
