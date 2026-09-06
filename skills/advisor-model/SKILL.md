---
name: advisor-model
description: Show or change which model answers as the advisor, without
  restarting Claude Code. Use when the user says "/advisor-model ...",
  "change/swap the advisor model", or "what model is the advisor right
  now". Works identically in the desktop app and the CLI - unlike
  /plugin configure, this needs no terminal.
---

# Show or set the advisor model

The advisor's model can come from two places: an override file this skill
manages (`~/.the-advisor/model`), or the `ADVISOR_MODEL` set at install
(`--config advisor_model=...` / `/plugin configure`). The override file
wins when present - that's what lets this work with no restart, identically
in the desktop app and a terminal, regardless of which one is running it.

## No argument: show the current model

Run via Bash:
```
cat ~/.the-advisor/model 2>/dev/null
```

If that's empty or the file doesn't exist, tell the user the override isn't
set and the advisor is using whatever `ADVISOR_MODEL` was set at install -
you cannot read that value directly, so say so rather than guessing it.

## An argument: set the model

Run via Bash:
```
mkdir -p ~/.the-advisor && printf '%s' "<model>" > ~/.the-advisor/model.tmp && mv ~/.the-advisor/model.tmp ~/.the-advisor/model
```
(Write-then-rename, not a direct write: a killed shell mid-write leaves the
old override intact instead of blanking it - advisor-reviewed, 2026-09-06.)

Confirm the new value back to the user. It takes effect on the very next
`/consult` - no restart needed, in either the desktop app or a terminal.
