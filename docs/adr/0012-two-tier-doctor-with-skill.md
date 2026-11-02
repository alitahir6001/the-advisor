---
status: accepted
date: 2026-09-07
---
# Two-tier `doctor.py` (free default, `--live` opt-in ship gate) plus a `/doctor` skill

## Context and Problem Statement
Four separate failures in this project looked like they worked because a proxy signal (a run happened, config looked set, no error) stood in for the real effect (CLAUDE.md gotcha 26). The question was how to make "check the real effect" happen reliably, and how desktop-app users with no terminal could run the check.

## Considered Options
* A prose rule only (A/B tested twice, inconclusive; `.ai/history.md` session 7)
* `doctor.py` with `--live` as the default (the first cut, reversed; CLAUDE.md gotcha 26)
* `doctor.py` with a free default and opt-in `--live`
* The raw script only (unreachable from the desktop app; `.ai/history.md` session 7)

## Decision Outcome
Chosen option: "Free default, opt-in `--live`, plus a `/doctor` skill". The plain tier shows what is configured and whether the CLI resolves, with no advisor call; `--live` makes one real, uncached advisor call and is the only real ship gate (ce6c862; CLAUDE.md gotcha 26). Defaulting to `--live` was reversed because a free tool that spends money by default is its own trust problem (CLAUDE.md gotcha 26). The skill makes it reachable from the desktop app (f913b97).

### Consequences
* Good, because the pipeline can be proven end to end before shipping, and the quick check costs nothing.
* Bad, because the free tier cannot prove a consult works; only `--live` can.

## More Information
Evidence: ce6c862 (`server/doctor.py`), f913b97 (`skills/doctor/SKILL.md`); CLAUDE.md gotchas 26, 27 (how the skill finds its plugin root); README.md:121-123; `.ai/history.md` session 7. Related: [ADR-0009](0009-provenance-in-consult-log-not-reply-header.md).
