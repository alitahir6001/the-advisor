<!-- Durable project knowledge, auto-loaded every session. Permanent facts only: live state -> .ai/handoff.md, history -> .ai/history.md. Gotchas are append-only (compress, never delete). Edit only when the user asks. -->

# The Advisor

## What this project is
A Claude Code plugin: a cheap workhorse model consults a stronger advisor model — Claude,
Gemini, or GPT — before hard-to-reverse decisions. The advisor provider is chosen by
config, not code. Live state: `.ai/handoff.md`.

Design decisions: docs/adr/ (index: docs/adr/README.md). Write new ones with the write-adr skill.

## Phase / status
Published at v0.5.3 via the GitHub marketplace `alitahir6001/the-advisor`. The direct
command is `/consult` — Claude Code's own built-in `/advisor` shadows any plugin skill of
that name. `advisor_model` can be changed live, with no restart and no terminal, via
`/advisor-model` (gotcha 21) — `--config`/`/plugin configure` still sets it at install and
remains the only path for the other options. Provider is auto-detected from the model name.
All code/doc work for v1.0 is done; the remaining gate is entirely proof-of-use: a real
Windows+Claude Code test on someone else's PC (Windows+Gemini CLI and Windows+Claude Code
have run, both on the author's own machines), and two friend cold installs. The vendor `*-api` hosts have test
coverage but no live call (no API keys). Desktop-app identity bug reported to Anthropic;
every setting now has a working route around it regardless (gotcha 21 for the model/log,
gotcha 25 for provider/base_url/api_key). See `.ai/handoff.md` for exact current state.

## Active gotchas
<!-- Numbered, append-only. Never delete an entry — compress it instead if this grows long. -->
1. **The repo is not what runs.** The live plugin is the installed copy at
   `~/.claude/plugins/cache/the-advisor/the-advisor/<version>/`. Editing the repo changes
   nothing until the next install. Settings themselves no longer live there — they are
   `userConfig` options, stored outside the cache and carried across version bumps.
2. **The local marketplace source is a directory, not GitHub** — it points at this working
   tree. Your own installs read uncommitted local files, so "the installed plugin" can
   differ from what other people get from GitHub. Push before assuming they match.
3. **`anthropic-api` requires `max_tokens`** — omitting it 400s. It is 4096 because 2048
   truncated advice mid-Risks.
4. **`openai-api` must NOT set `max_tokens`** — it is optional there (unset means no cap),
   and newer models reject the field outright in favour of `max_completion_tokens`.
   Adding it "for consistency" with the Anthropic path is a regression.
5. `claude plugin update` needs the full id (`the-advisor@the-advisor`) and a restart to
   take effect.
6. **`ADVISOR_BASE_URL` makes the API key optional on purpose** — local servers (ollama,
   LM Studio, vLLM) want no key, and sending an empty `Authorization` header breaks some
   of them. Don't "fix" this by demanding a key again.
7. **Gemini CLI silently disables MCP servers in untrusted folders.** `gemini mcp add`
   reports success and `gemini mcp list` shows the server as Disabled. Trust the folder
   before concluding the server is broken.
8. **An unset `userConfig` option substitutes as `""`, not as absent** (verified against
   Claude Code 2.1.222 with a throwaway probe plugin). It lands in the MCP server's `env`
   and shadows any inherited shell value — which is why the key option is named
   `ADVISOR_API_KEY` rather than `ANTHROPIC_API_KEY`, and why config reads use `or` rather
   than a `get()` default.
9. **`required: true` on a `userConfig` option does not block a non-interactive install** —
   `claude plugin install` warns and proceeds. Safe to mark options required.
10. Model IDs stay out of `advisor_server.py` and `.mcp.json`, but the `userConfig`
    descriptions in `plugin.json` do carry examples — they're help text, not defaults.
11. **An unset `ADVISOR_MODEL` used to inherit the workhorse's own model** — `claude -p`
    with no `--model` reads the user's `settings.json`, so the advisor silently became the
    same model as the caller and the log still looked fine (16 real consults, caught only
    via billing). It now refuses; `cli-default` is the explicit opt-in. Don't reintroduce
    a silent fallback.
12. **Claude Code's built-in `/advisor` shadows a plugin skill of the same name** — the
    skill becomes unreachable, silently. The built-in is a whole native feature (advisor
    threads, executor<->advisor pairing, its own billing), not just a command. Ours is
    `/consult`. Don't rename it back.
13. **Uninstalling a plugin clears its `pluginConfigs`** — re-pass `--config` on reinstall
    or it comes back unconfigured.
14. **`${user_config.KEY}` substitutes in `command`, not just `env`** — that is what makes
    `python_command` possible. A schema `default` is applied even when the user never sets
    the option, so defaults are real, unlike the `""` an option with no default yields.

15. **The desktop app and the CLI resolve this plugin under different identities** —
    `the-advisor@inline` vs `the-advisor@the-advisor`. `pluginConfigs` is keyed by identity,
    so the app's server gets every option blank. Diagnose with `ps eww` on the running
    server (`CLAUDE_PLUGIN_DATA` names the identity), not by guessing at staleness.
16. **The advisor shells out to `claude` on PATH**, which is the Homebrew CLI — not the
    desktop app's own harness. A model the app offers in `/model` may still be rejected by
    the CLI the advisor actually calls, with a "version X or newer is required" error.
17. **`claude -p` with no `--model` uses the global `model` in `settings.json`**, not the
    calling session's model. Proven with `CLAUDE_CONFIG_DIR` against a throwaway config.
18. **`shutil.which` resolves CLI wrapper paths on Windows** — without it,
    `subprocess.run(["gemini", ...])` raises `WinError 2` because `.cmd` wrappers aren't
    found. Tests mock `shutil.which` to `None` so assertions see bare command names.
19. **`gemini mcp add` is project-scoped by default** — the server config lives in the
    project directory and disappears when the user leaves it. Move the `mcpServers` block
    to `~/.gemini/settings.json` for global availability.
20. **Gemini CLI's `/permissions trust` must be run inside the CLI** — there is no
    `gemini trust` shell command. Attempting one treats the arguments as a prompt and can
    trigger a recursive agent loop that burns tokens.
21. **A file-based override (`~/.the-advisor/model`) sits ahead of `ADVISOR_MODEL` in
    `consult()`'s resolution, re-read fresh on every call, never cached.** It exists
    specifically to route around gotcha 15: `pluginConfigs` is keyed by plugin identity, so
    no `--config`/`/plugin configure` change can ever reach `the-advisor@inline` from any
    known command. The override file lives at a fixed, identity-independent path outside
    Claude Code's own config entirely, so both identities read the same value with zero
    restart. The `/advisor-model` skill is the only thing that writes it.
22. **`run_cli()`'s `shutil.which()` resolves fresh on every call, never cached** — added
    for the Windows `.cmd`-wrapper fix, but it has a second effect: the advisor
    transparently follows any change to the `claude`/`gemini` binary on PATH, with zero
    restart. Proven by swapping the Homebrew `claude` cask for the native installer
    mid-session and watching the already-running server pick up the new binary on its very
    next call.
23. **`claude plugin update` no-ops when the version string hasn't changed**, even for this
    project's `source: directory` marketplace — it does not resync files from the repo
    during iterative dev. Use `cp` (see `.ai/rules.md`) or an actual version bump instead.
24. **A subagent (spawned via the Agent tool) is not handed `consult_advisor` by default** —
    one general-purpose subagent had to run `ToolSearch` for it explicitly before it became
    callable, same deferred-tool pattern the top-level session uses. One data point, one
    harness version, not exhaustively verified — but relevant to any future work letting
    subagents act as their own advisor-consulting workhorses (see `.ai/backlog.md` parked
    items): it would need each spawned subagent's own prompt to know to go looking for it.
25. **A real OS environment variable reaches the desktop app's plugin process even though
    `pluginConfigs` can't (gotcha 15/16)** — proven with `launchctl setenv PROBE_VAR x`,
    a full app restart, and `ps eww` on the freshly-spawned server showing it in `env`.
    `ADVISOR_PROVIDER`/`ADVISOR_BASE_URL`/`ADVISOR_API_KEY` are read with plain
    `os.environ.get(...)`, never through Claude Code's config layer, so `launchctl setenv`
    (macOS) is a working, documented escape hatch for exactly the three settings the
    identity bug still blocks from the desktop app. Windows equivalent (`setx`) is the
    logical analogue but is unverified — don't present it as confirmed.
26. **`log_consult()` carries `model_source`/`provider_source`, not just the resolved
    value** — added after four separate "looked like it worked" incidents in this project
    (gotchas 11, 15, the Windows server bug, and proactive escalation) all had the same
    shape: a proxy signal (a run happened, config looked set, no error) stood in for the
    real effect. The resolved model and provider alone can't tell you *which real input
    won* (override file vs `ADVISOR_MODEL`, explicit `ADVISOR_PROVIDER` vs inference) - a
    stale override silently shadowing a fresh `--config` change would look identical to a
    correct resolution without it. **Log-only, deliberately** - `attribution()` (the
    user-facing reply header) does NOT show this; it's a post-mortem/`doctor.py` signal, not
    something to put in front of a user on every single reply. Don't drop these fields from
    the log when refactoring; `TestProvenance`
    is mutation-verified to catch it if you do. `server/doctor.py` is the mechanized version
    of the same principle, in two tiers: plain (free - what's configured, does the CLI
    resolve, no advisor call) and `--live` (one real, uncached advisor call - real cost -
    proving the pipeline actually works end to end, not just that it looks configured).
    Only `--live` is a real ship gate; the free tier is a `brew doctor`-style quick check.
    Don't default it to `--live` - that was the first cut, and shipping a free tool that
    silently spends money by default is its own trust problem.
27. **`${CLAUDE_PLUGIN_ROOT}` is NOT a real env var in a skill's own Bash calls** - checked
    directly (`echo $CLAUDE_PLUGIN_ROOT` was empty in a live session). It only exists as an
    `.mcp.json` spawn-time substitution for the MCP server process. A skill needing its own
    plugin's install path (e.g. `skills/doctor`) must derive it from the "Base directory for
    this skill" text the harness shows when the skill loads - strip the trailing
    `/skills/<name>` to get the plugin root. Same trick `/advisor-model` already relied on.
28. **Proactive escalation does not fire, tested not assumed** - a fresh top-level session
    confirmed it can see the "MUST get a second opinion" mandate and said it would act on
    it, then made zero tool calls on a real qualifying decision. Task-tool subagents fare
    worse: they never see the mandate at all (only the bare, undescribed `consult_advisor`
    tool name). Agent-description text is attended to as a routing hint, not a standing
    behavioral policy - don't assume prose instructions fire just because the model claims
    it would follow them. `agents/advisor.md`'s language was retracted accordingly (session
    0.4.0); a real fix would need a deterministic harness hook, not stronger wording.
29. **`claude -p` inherits the global `effortLevel` unless `--effort` is passed** - a
    `doctor --live` consult ran `claude-opus-5-5` at `effort=medium` from the author's own
    settings, same shape as gotcha 17 for the model. `_dispatch()` now sends `--effort`,
    default `max` (`DEFAULT_EFFORT`), override `ADVISOR_EFFORT`, `cli-default` sends no
    flag (also the escape hatch for a `claude` too old to know it). `anthropic-cli` only;
    the log records `effort`/`effort_source` there and `None` for other providers on
    purpose, so it can't claim an effort that was never sent. No file override: the
    default needs no config, so the desktop-app identity bug (gotcha 15) can't block it.
30. **The advisor runs tool-less, one turn, with a 1800s timeout.** `claude -p` ran as a
    full agent in the caller's cwd: a real consult made 19 Bash/Read calls and was killed
    at 300s, ~1.8M input tokens, because each call re-sent the context and cost another
    max-effort think. `NO_TOOLS` (`--strict-mcp-config --tools ""`, `--tools` is variadic
    so it stays last) makes it stateless, as the tool description promises; the workhorse
    must send the code in `context`. Max-effort thinking is the real cost: the same
    question took 309s and 530s on two replays and 414s through MCP, so expect 5-9 min.
    Claude Code's own MCP call limit held for at least 414s; beyond that it is unmeasured.
    Gemini CLI has the same exposure and was left untouched.
31. **The prompt goes over stdin, never argv.** On Windows, `.cmd` wrappers (npm-installed
    `claude`/`gemini`) still need `shell=True`, and `cmd.exe` cuts a multi-line argument at
    the first newline, silently dropping the rest of the prompt and every flag after it.
    `run_cli()` sends it as `input=`, which also replaces the old `stdin=DEVNULL` guard
    against inheriting the JSON-RPC pipe. Gemini needs `-p ""` to stay headless; it appends
    that value to stdin. Live-checked on macOS for both CLIs; the Windows `.cmd` path itself
    is unverified.

## Conventions / what NOT to do
- Don't commit or push unless asked. Version bumps are a release action — confirm first.
- Don't add dependencies. Stdlib only, tests included — the plugin promises "requires
  python3, nothing to install".
- Don't put model IDs in `advisor_server.py` or the repo's `.mcp.json`.
- Don't re-explain a decision already made, or re-justify work already accepted.
- Design rules and test commands live in `.ai/rules.md`; live state in `.ai/handoff.md`.
