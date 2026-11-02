---
status: accepted
date: 2026-09-05
---
# Rename `/advisor` to `/consult` and position as a complement to the native Advisor

## Context and Problem Statement
Claude Code shipped a built-in `/advisor`, a whole native feature with advisor threads, executor/advisor pairing, and its own billing. It silently shadows any plugin skill of the same name, so the plugin's `/advisor` skill became unreachable (CLAUDE.md gotcha 12).

## Considered Options
* Keep `/advisor` (unreachable while the built-in exists)
* Leave a deprecating stub at the old name (useless: a stub at a shadowed name is unreachable too; `.ai/rules.md:75`)
* Rename the plugin id and marketplace as well (rejected: breaks existing installs; `.ai/handoff.md:39`)
* Rename only the command to `/consult`

## Decision Outcome
Chosen option: "Rename only the command to `/consult`", because it is the only reachable name, and keeping the plugin id and marketplace (`the-advisor@the-advisor`) leaves existing installs working. The README now positions the plugin as the multi-provider complement to the built-in (README.md:6-8).

### Consequences
* Good, because the direct command works again and the overlap with the native feature is stated up front.
* Bad, because users who learned `/advisor` now reach the built-in, not this plugin.

## More Information
Evidence: d683dd5 (old `skills/advisor` removed), 9fe328d (`skills/consult` added); CLAUDE.md gotcha 12; README.md:6-8; `.ai/rules.md:75`, `.ai/handoff.md:39`.
