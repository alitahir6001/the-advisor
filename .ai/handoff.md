# Handoff — live state snapshot

## Last updated
2026-10-19 (session 9; rebuilt 2026-11-01 from git log + CLAUDE.md, folding in the retired current-task.md)

## Current state
v0.5.2 is committed and on origin/main (`572d580`), working tree clean, 24 tests. 0.5.2 fixed the prompt cut-off found on the first real Windows + Claude Code run (the author's own machine): the prompt now goes over stdin for every CLI provider (gotcha 31). All code/doc work for v1.0 is done; the gate is proof-of-use on machines that are not the author's.

## Active task
**What:** get the plugin into two other people's hands, one mac and one Windows, working with nothing but install, set the model, use it. That is the project's own definition of v1.0-ready.
**Why:** the code is done (provider inference, Windows fixes, desktop-app config routed around, `doctor` pre-ship gate, max effort, tool-less advisor, stdin prompt). What is left is proof from someone else's machine.

1-20. [x] Foundation through v0.3.0 (userConfig, python_command, refuse unset model, `/consult` rename, `/advisor-model` override, README rebuilds, log-path fix) - detail in history.md.
21. [ ] Windows + Claude Code on someone else's machine. Both Windows runs so far (Gemini CLI, then Claude Code in 0.5.2) were on the author's own PCs and do not count toward the friend-cold-install bar; the Windows `.cmd` path after the stdin fix is unverified - user
22. [x] Re-confirm Fable 5.1 as advisor post-Homebrew-migration - agent
23. [x] Live check of proactive escalation: clean negative, it does not fire even for the primary case - agent
24. [ ] Friend #1 (mac) runs setup cold, unaided - user
25. [ ] Friend #2 (Windows) runs setup cold - user
26. [x] Provenance (`model_source`/`provider_source`) in the log, log-only - agent
27. [x] `server/doctor.py`, two-tier (free config check, `--live` real round-trip) - agent
28. [x] Retracted the escalation "MUST" in `agents/advisor.md`; hook trigger deferred to v1.5/2.0 - user decided, agent built
29. [x] `/doctor` skill, README reorganized, comments trimmed, 0.4.0 pushed - agent/user
30. [x] Advisor effort: default `--effort max`, `ADVISOR_EFFORT` override, logged - agent
31. [x] Advisor tool-less, single-turn, 1800s timeout, description warns - agent
32. [x] 0.5.1 committed, pushed, cache updated, app restarted - agent/user
33. [x] 0.5.2: Windows launcher fix + prompt over stdin, committed, pushed - agent/user

## Open threads
- **Gemini CLI path still runs with tools enabled** - same agent-wandering exposure the Claude path had (gotcha 30); no `--tools` equivalent checked.
- **Claude Code MCP call limit beyond ~7 min is unmeasured** - 414s held; consults run 3-9 min at max, 1800s is our own ceiling.
- **Desktop-app identity bug unfixed upstream** (reported) - routed around by gotcha 21 (model/log) and gotcha 25 (provider/base_url/api_key via `launchctl setenv`; Windows `setx` unverified).
- **Untested providers** - `*-api` hosts have mock coverage only (no API keys); Codex: user testing, report pending.
- Merged branch `fix/windows-launcher-args` (same commit as main) still exists locally and on origin.

## Next recommended step
Windows + Claude Code on someone else's machine, then the two friend cold installs; nothing for the agent to build until one surfaces a real bug (or Gemini tool lock-down, if Gemini users matter before v1.0).

## Out of scope
`codex-cli` provider until testable; live `*-api` calls (no keys); renaming the plugin id or marketplace (breaks installs); working around the identity bug inside the plugin's config resolution; competing with the native Advisor on its own ground; subagent-as-workhorse and hook-based escalation (post-v1.0, see backlog.md parked items).
