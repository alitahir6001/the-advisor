# History

Session logs and release history, moved out of backlog.md 2026-11-01. Never read at session start; read only when asked about past work.

## Last session: 2026-10-14 (session 8)
Made the advisor run at max effort, then found max effort was not the whole story.
`claude -p` inherited the user's global `effortLevel` (a doctor consult ran at medium), so
`--effort max` became the default with an `ADVISOR_EFFORT` override and a `cli-default`
escape (0.5.0). A live doctor run passed (11s, $0.13) and the advisor subprocess's own
transcript confirmed `effort: max`, against `medium` on the old run.

Then a real consult in the zune project timed out at 300s and silently fell back to a
same-model subagent. The killed run's transcript showed why: the advisor was running as a
full agent in the caller's repo, 19 Bash/Read calls and ~1.8M input tokens, each call
re-sending context and costing another max-effort think - contradicting the tool
description's "stateless, sees only what you send". Fix: `--tools "" --strict-mcp-config`
(single turn), timeout 300 -> 1800, description warns of multi-minute waits (0.5.1).
Replays of the same question: 530s and 309s, a headless MCP run 414s, a real pocket
professor consult through the restarted app 223.8s - thinking at max is the real cost, 3-9
min, which the user accepted over lowering effort (saved as a feedback memory).

Corrections made along the way: I first claimed the tool wandering was the whole slowness
and the fix would be faster - measured, thinking dominated (52K tokens, ~515s, answer text
12s). I also told the user nothing was left to build from a stale handoff; a NEXT TASK had
been added 2026-09-22 that I missed. 18 -> 23 tests, all mutation-verified.

## Last session: 2026-09-07 (session 7)
Closed the `consults.py` log-location gap (item 20): log now defaults to a fixed,
identity-independent `~/.the-advisor/consult-log.jsonl` via a new `THE_ADVISOR_DIR`
constant shared with `MODEL_OVERRIDE_PATH`, and `.mcp.json` no longer pins it to
`${CLAUDE_PLUGIN_DATA}`, which had been splitting one user's history across the
desktop-app/CLI identity bug. Then verified, live, that a real OS environment variable
(`launchctl setenv`) reaches the desktop app's plugin process even though `pluginConfigs`
can't (gotcha 25) — a working escape hatch for `advisor_provider`/`advisor_base_url`/
`advisor_api_key` from the desktop app, documented in the README; caught and fixed a stale
Troubleshooting line that had told desktop-app users to use `/plugin configure`, which
never reaches them either.

Then closed current-task item 23 for real: proactive escalation was tested cleanly for the
first time, not just theorized. A throwaway sibling stub project
(`../escalation-test-stub/`) with zero mention of "advisor"/"consult" anywhere confirmed a
fresh top-level `claude -p` session sees the full mandate and says it would act on it
unprompted - then, given a genuinely hard-to-reverse decision naturally, made zero tool
calls. Confirmed via the empty consult log, not the transcript. (Task-tool subagents were
separately confirmed to never see the mandate at all - different failure mode, see Parked
items.) Pulled the escalation promise from the README entirely on the user's call.

That surfaced the session's real subject: **this is the fourth time something looked like
it worked and didn't** (unset `ADVISOR_MODEL`, the desktop-app identity bug, the Windows
server, now this) - every time because a proxy signal one step upstream stood in for the
real, downstream effect. Wrote a prose rule into `.ai/rules.md` naming this. Tried to A/B
test whether the written rule actually changes behavior, twice, in throwaway stub projects
(`../rules-test-stub-control/`, `../rules-test-stub-withrule/`) - both times inconclusive,
because the test's own task framing ("did it work?") already forced careful checking
regardless of the rule, unlike the four real incidents, which happened as a side effect of
other work with no explicit verification ask. The user wanted this actually solved, not
re-tested: consulted the advisor directly via `claude -p --model claude-opus-5 --effort
max` (the `consult_advisor` tool has no effort parameter). Its answer, in short: prose has
a ceiling well under 100%, disqualifying by itself given a "cannot ship things that look
fixed" bar - mechanize it. Built the two unambiguous, high-priority pieces of that
recommendation: `model_source`/`provider_source` now travel with every resolved
model/provider (which real input won, not just the value - gotcha 26), and `server/
doctor.py`, a real uncached advisor call as a pre-ship gate, exit code 0/1, verified live in
both directions. Left open, on the user's call: the advisor's position on the mandate
itself hardened between the two consults, from "keep it, it's free" to "shipping a MUST
that empirically doesn't fire is the same defect class as the other four - hook it or
retract it" (current-task item 28).

Closing the session: retracted (not hooked) the mandate's "MUST" language in
`agents/advisor.md`. User feedback on the provenance feature - the `[model: ...,
provider: ...]` bracket on every reply was noise - pulled it back out of `attribution()`;
the data still flows to the log, just not the user-facing header. Built `/doctor` as a
proper skill (not just a raw script) after realizing a desktop-app user had no way to run
it at all; verified end to end after an app restart, which also confirmed
`${CLAUDE_PLUGIN_ROOT}` is NOT a real env var available to a skill's own Bash calls (only
an `.mcp.json` spawn-time substitution) - skills must derive their own root from the "Base
directory for this skill" text shown at load time, same trick `/advisor-model` already
used. README reorganized end to end (Quickstart -> How it works -> Using other models ->
Changing settings later -> collapsed Troubleshooting) with the full command table finally
including `/doctor`. Did a repo-wide comment-reduction pass - advisor_server.py had
accumulated multi-line comments with embedded dates/history; trimmed to 1-2 lines each,
pointing at CLAUDE.md gotchas instead of restating them. Version bumped to 0.4.0
(`plugin.json` + `advisor_server.py`'s `serverInfo`, kept in sync by `TestVersion`),
committed, pushed. 18 tests, all passing.

## Last session: 2026-09-06 (session 6)
Fixed the desktop-app config problem session 5 only diagnosed and reported: a new
`/advisor-model <model>` skill writes `~/.the-advisor/model`, which `consult()` now checks
ahead of `ADVISOR_MODEL` on every call (never cached) - a fixed path outside Claude Code's
identity-keyed `pluginConfigs` entirely, so it works the same in the desktop app and CLI
with zero restart. Verified live and repeatedly through the real tool, not just unit tests:
Opus 5, a mid-session switch to Sonnet 5 (same server PID, proving no restart), and the
actual production case - Fable 5.1 (hit the known Homebrew version block exactly as
predicted) and plain `claude-fable-5` (worked). 14 -> 17 tests, mutation-verified. Also
migrated this machine's CLI off the stuck Homebrew cask (2.1.236) onto Anthropic's native
installer (2.1.263) - confirmed clean, and confirmed the advisor kept working through the
swap with no restart, because `run_cli()` re-resolves `claude` via `shutil.which` fresh on
every call rather than caching the path. README rewritten twice: once for the new Settings
shape, once top-to-bottom for onboarding (Quickstart, collapsible reference tables,
consolidated Troubleshooting). Hunted for a stray `DISABLE_AUTOUPDATER=1` in the
environment (source never found); lesson: grep for the specific key rather than dumping
a full `env` block.
Open: the desktop-app identity bug itself is still unfixed upstream (reported to Anthropic,
practical impact now limited to `advisor_provider`/`base_url`/`api_key`), and the sharpened
gap list for v1.0 is Windows+Claude Code untested (only Windows+Gemini CLI ever was, and
only on the author's own PC - doesn't count toward the friend-cold-install bar), proactive
escalation never cleanly verified end to end, and zero outside cold installs yet.

Closed out at end of session: confirmed Fable 5.1 works clean post-migration (no
version-gate error). Also ran a first real test of the user's subagent-workhorse idea (see
Parked items) - a general-purpose subagent could reach `consult_advisor`, but only via an
explicit `ToolSearch` call; it wasn't in its default tool list.

## Last session: 2026-09-06 (session 5)
Provider inference so users only set the model (no more `advisor_provider` required).
Windows tested for the first time — on Win10 with Gemini CLI, not Claude Code. Two bugs
found and fixed: `subprocess.run` can't resolve `.cmd` wrappers on Windows (fixed with
`shutil.which`), and the system prompt was too rigid for non-architectural questions.
Gemini CLI setup was painful — project-scoped MCP config, silent trust failures, skills
needing separate linking — all documented in the README now. The desktop-app identity bug
(`the-advisor@inline` vs `the-advisor@the-advisor`) was reported to Anthropic. Also
learned the hard way not to fabricate CLI commands for tools I haven't used (hallucinated
`gemini trust add`, which caused a recursive agent loop that burned tokens). 14 tests.

Session 2 (2026-08-15, v0.1.5 model-agnostic work) rolled out - see "Release history" below.

## Release history (moved from CLAUDE.md 2026-11-01)
- **0.1.0** (2026-08-11) — first release. Inspired by the advisor/executor pattern at
  vanja.io. Diagrams added to the README.
- **0.1.1–0.1.2** (2026-08-12) — three bug fixes, all found in use, none caught by tests
  because there were none: a `json.loads` crash that killed the server loop, a pinned
  model removed from the agent frontmatter, `max_tokens` raised after advice truncated
  mid-reply, and auth failures that were invisible because the CLI prints them to stdout.
- **0.1.3–0.1.4** (2026-08-15) — the first test suite (5 tests, mutation-verified), the
  `/consult-advisor-cli` -> `/second-opinion` rename with a deprecating stub, and a
  README cut roughly in half.
- **0.1.5** (2026-08-15) — model-agnostic for real: `openai-compatible` provider,
  `ADVISOR_BASE_URL` (which also makes the API key optional), and a standalone entry point
  so a workhorse that speaks no MCP can still consult. Then setup itself: `userConfig`
  options replaced the hand-edited cache `.mcp.json`, so settings are discoverable and
  survive version bumps. 9 tests.
- **0.2.0** (2026-09-05) — Claude Code shipped its own native Advisor, whose `/advisor`
  shadows any plugin skill of that name, so `/advisor` became `/consult` and the README
  now positions against the built-in. Two silent failures fixed: the advisor had been
  running as the workhorse's own model for a month, and Windows couldn't start the server
  at all. `/consult-advisor-cli` deleted as promised. 10 tests.
- **0.3.0** (2026-09-06) — provider inference: users set the model, the provider is
  detected from the name (`claude-*` → `anthropic-cli`, `gemini-*` → `gemini-cli`,
  `gpt-*` → `openai-api`, base URL → `openai-compatible`). Windows tested for the first
  time (Win10 + Gemini CLI): `shutil.which` fixes subprocess resolution, `shell=True` on
  NT. System prompt relaxed for non-architectural questions. README rewritten with
  per-platform install sections (Claude Code, Gemini CLI, standalone). Desktop-app
  identity bug reported to Anthropic. 14 tests. Same day, a second pass fixed the identity
  bug's actual impact rather than just documenting around it: `/advisor-model` writes a
  file outside Claude Code's own config entirely, so the model can change live, with no
  restart, identically in the desktop app and CLI (gotcha 21). CLI migrated off a stuck
  Homebrew cask onto the native installer mid-session with zero disruption, which is what
  surfaced gotcha 22. README rewritten again, this time for onboarding (Quickstart,
  collapsible reference tables, consolidated Troubleshooting). 17 tests.
- **0.4.0** (2026-09-11) — a real, tested negative on proactive escalation: it does not
  fire, not even in the primary top-level-session case (gotcha 27 territory; agent
  description text isn't a behavioral policy the model reliably acts on). Escalation's
  "MUST" language retracted rather than left overclaiming. Named a repeating pattern
  (fourth "looked like it worked, didn't" incident) and mitigated it with `log_consult()`
  provenance (gotcha 26) and `server/doctor.py`, a real two-tier pre-ship check. New
  `/doctor` skill so desktop-app users (no terminal) can actually run it. README
  reorganized top to bottom. 18 tests.

- **0.5.0–0.5.1** (2026-10-14) — advisor effort: `claude -p` had been inheriting the
  user's own `effortLevel` (medium); now `--effort max` by default (gotcha 29). A real
  consult then timed out at 300s because the advisor ran as an agent in the caller's repo
  (19 tool calls); it now runs tool-less, one turn, 1800s timeout (gotcha 30). Consults
  take 3-9 min at max, accepted over lowering effort. 23 tests.
- **0.5.2** (2026-10-19) — first real Windows + Claude Code run (the author's own machine)
  found the advisor answering a cut-off question with no `--model`: `cmd.exe` truncates
  multi-line arguments at the first newline (gotcha 31). Native `.exe` CLIs now skip the
  shell, and the prompt goes over stdin for every CLI provider. 24 tests.
