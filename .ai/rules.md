# Project rules & how to maintain .ai/

## Maintaining these files
At session start, read `handoff.md` ONLY. Everything else loads on demand.

- **handoff.md** - live state snapshot, and the only file read at startup. Rewrite in place, never append like a log. Cap 8 KB.
- **rules.md** - this file. Read when you're about to change code, or when handoff points at a rule. Edit only on an explicit "add a project rule: X".
- **backlog.md** - parked work. Read only when the user asks about it or asks you to add to it. Never read at startup.
- **history.md** - session logs and release history. Never read at startup; read only when asked about past work.
- Permanent gotchas / non-obvious behavior that stays true for the project's life -> root `CLAUDE.md`, not here.
- Subsystem depth (how the renderer works, what the pipeline costs) -> a project skill under `.claude/skills/`, not here. Skill descriptions sit in context for ~20 tokens each and the body loads only when relevant.

## What earns a place in this file
A rule belongs here only if ALL FOUR hold. Otherwise route it:
1. It applies to ANY change in this project - not one subsystem. (Subsystem -> a skill.)
2. It is not a general engineering or epistemic principle. (General -> `~/.claude/CLAUDE.md`, where it works across every project.)
3. It is not a standing user preference. (Preference -> `~/.claude/CLAUDE.md`.)
4. Breaking it costs real money, real data, or something the user cannot undo.

**Cap 8 KB, measured in bytes, not lines.** A line cap on paragraph-length entries is not a cap - one project's rules file reached 57 KB and 105 rules against a "200 line" limit, and ~70% of it had already been superseded by project skills. One sentence per rule plus a pointer; the long version lives in the skill.

## Status marks
Use these for any step or task that needs a status — in handoff's Active task section and elsewhere:
- `[ ]` todo
- `[~]` in progress
- `[x]` done
- `[!]` blocked

## Populating from empty
- **handoff.md** - Last updated (date + session N) / Current state (3 sentences) / Active task (what, why, remaining steps with status marks and owner) / Open threads (max 5) / Next recommended step / Out of scope. No "changed files" section - `git log` and `git diff` answer that for free and never go stale.
- **backlog.md** - parked items only. Not a session log.

## Quick reference: when to touch what
| Event | handoff.md | rules.md | backlog.md | CLAUDE.md |
|---|---|---|---|---|
| Made a code change | yes | - | - | - |
| Hit a blocker / found a bug | yes | - | - | - |
| Finished task, starting new one | yes | - | - | - |
| Task boundary / ~50% context | yes | - | - | - |
| User says "add a project rule" | - | yes | - | - |
| User says "park that" / "add to backlog" | - | - | yes | - |
| Discovered a permanent gotcha | yes | - | - | only if user agrees |

## Project-specific rules
<!-- Tech stack, code conventions, agent workflow constraints (e.g. "never run git"), security rules - append as discovered. Skip anything guessable from the code. -->

- **Check the real effect one level downstream, not a proxy signal** (see CLAUDE.md gotcha 26). Pre-ship gate: `python3 server/doctor.py --live`; unit-level: `TestProvenance`.
- Run tests: `python3 -m unittest discover -s server -p 'test_*.py'`
- **Clear `server/__pycache__` when mutation testing.** Python reuses stale bytecode when
  an edit lands in the same second with an unchanged file size, which silently produces
  wrong test results.
- The escalation rule lives on the **agent description** in `agents/advisor.md`, not on
  the MCP tool schema — tool schemas can be deferred out of context, and a rule the model
  never sees can't fire. Testing overturned the opposite design. Don't "tidy" it onto the
  tool.
- **ollama is installed on this machine** with `gemma3:latest` and `gemma3:12b-it-q4_K_M`,
  serving OpenAI-format requests at `http://localhost:11434/v1` with no API key. Use it to
  exercise the `openai-compatible` path for real instead of trusting mocks — doing so is
  what caught the base-URL/API-key ordering bug.
- **Resolve config in the order the user would fix it.** `api_base()` runs before
  `api_key()` so a provider missing its host says so, rather than complaining about a key
  that may not even be needed.
- Verify behaviour changes by **mutating the source and confirming the suite goes red**.
  Every guard in the suite has been checked this way; a test that never fails is worse
  than no test.
- **Test harness behaviour with a throwaway probe plugin**, not by reading docs and hoping.
  A scratch marketplace + one-file plugin whose "MCP server" just dumps `os.environ` and
  exits answers substitution questions in a minute. That is how the `""`-not-absent and
  `required`-doesn't-block facts were established. Uninstall and remove the marketplace
  afterwards.
- **`env()` in the test suite must clear every var the server reads.** It unsets the names
  in `ADVISOR_VARS`; a var missing from that tuple leaks in from the real environment and
  makes tests pass for the wrong reason. Add new vars there when adding them to the server.

- **Check whether Claude Code already owns a command name before shipping a skill** (gotcha 12). A deprecating stub at a shadowed name is useless too. Grep the CLI binary's strings when a name feels generic.
- **A version bump touches three things**: `.claude-plugin/plugin.json`, the `serverInfo`
  literal in `advisor_server.py` (the suite fails if they disagree — they drifted once),
  and the README wherever it names a cache path containing the version.
- Before blaming config for a model rejection, check `claude --version` (gotcha 16).
- **The advisor's subprocesses leave their own transcripts** in `~/.claude/projects/`,
  whose first user message is the advisor system prompt and whose assistant records carry
  the real model. That is the ground truth for "which model actually answered" - better
  than the consult log, which only records what was requested.
- **Sync repo -> cache with `cp`** (gotcha 23): copy changed files into `~/.claude/plugins/cache/the-advisor/the-advisor/<version>/`, and remember `skills/` alongside `server/` - they drifted once.
- **A free way to verify server behaviour without the Claude Code harness or real model
  spend**: spawn `advisor_server.py` directly and drive it by hand over stdin/stdout - real
  JSON-RPC, not a mocked test - with a deliberately bogus model name. `log_consult()`
  records what was attempted even on failure, so this proves resolution/precedence logic
  (e.g. "does a config change reach an already-running process with no restart") for free.
  Complements the throwaway-probe-plugin technique above, one level down: that one tests
  Claude Code's own harness behaviour, this one tests the server's.
