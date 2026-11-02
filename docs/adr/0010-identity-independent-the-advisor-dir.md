---
status: accepted
date: 2026-09-06
---
# Fixed, identity-independent `~/.the-advisor/` for the model override and consult log

## Context and Problem Statement
The desktop app and the CLI resolve this plugin under different identities (`the-advisor@inline` and `the-advisor@the-advisor`). `pluginConfigs` is keyed by identity, so the app's server gets every option blank, and no known `--config` or `/plugin configure` command reaches the inline identity (CLAUDE.md gotchas 15, 21). The consult log under `${CLAUDE_PLUGIN_DATA}` was likewise split across the two identities (`.ai/history.md` session 7).

## Considered Options
* Set the model via `--config` / `/plugin configure` (cannot reach the inline identity)
* Keep the log under `${CLAUDE_PLUGIN_DATA}` (splits one user's history)
* A fixed directory outside Claude Code's config, `~/.the-advisor/`

## Decision Outcome
Chosen option: "Fixed `~/.the-advisor/` directory", because both identities read the same path. The model override file `~/.the-advisor/model` sits ahead of `ADVISOR_MODEL`, is re-read on every call with no restart, and is written only by the `/advisor-model` skill (ee07859; CLAUDE.md gotcha 21). The consult log moved to `~/.the-advisor/consult-log.jsonl` (8331b4d, 466f42b). The other options (provider, base URL, API key) are read with plain `os.environ.get`, so desktop users set them as OS environment variables, which do reach the app's plugin process (CLAUDE.md gotcha 25).

### Consequences
* Good, because the model can be changed live and identically from the desktop app and the CLI, and the log is one file.
* Bad, because it is a workaround for an upstream identity bug, and the macOS `launchctl setenv` route is verified while the Windows `setx` equivalent is not (CLAUDE.md gotcha 25).

## More Information
Evidence: ee07859, 8331b4d, 466f42b; `server/advisor_server.py:83-108`; CLAUDE.md gotchas 15, 21, 25; `.ai/history.md` session 7. The identity bug is reported upstream (CLAUDE.md, Phase / status).
