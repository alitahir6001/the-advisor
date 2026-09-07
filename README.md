# The Advisor

Your cheap workhorse model consults a stronger advisor before hard-to-reverse decisions.
Any model on either side — Claude, Gemini, GPT, or a local model. Nothing is hardcoded.

Claude Code has a built-in `/advisor` that pairs Claude models inside your session. This
plugin is the multi-provider version: any advisor, a greppable JSON log, and it works from
workhorses that aren't Claude Code. The command is `/consult`.

![How it works](docs/loop.svg)

- [Quickstart](#quickstart)
- [Changing settings later](#changing-settings-later)
- [Troubleshooting](#troubleshooting)
- [Not using Claude Code?](#not-using-claude-code)
- [How it works](#how-it-works)

## Quickstart

Requires Python 3 — standard library only, nothing else to install.

**macOS / Linux:**
```bash
claude plugin marketplace add alitahir6001/the-advisor && claude plugin install the-advisor@the-advisor --config advisor_model=claude-opus-5
```

**Windows** — same, plus one flag (`python3` doesn't exist on Windows):
```bash
claude plugin marketplace add alitahir6001/the-advisor && claude plugin install the-advisor@the-advisor --config advisor_model=claude-opus-5 --config python_command=python
```

Pick a cheap workhorse with `/model`, then start a new session — the plugin loads on
startup — and try it:

```
/consult is a queue the right call here, or am I overbuilding?
```

You're done when the reply names both models:

```
Advisor   = claude-opus-5 (anthropic-cli)
Workhorse = claude-haiku-4-5
```

The bundled agent also escalates on its own — before architectural calls, after the same
fix fails twice, and on tradeoffs it can't settle alone. It stays quiet on routine work.

Want Gemini or GPT as the advisor instead of Claude? Just change `advisor_model` above —
the provider is auto-detected from the name (`claude-*`, `gemini-*`, `gpt-*`). For a local
model, also add `--config advisor_base_url=http://localhost:11434/v1`.

Route a one-off question to a different provider ad hoc (needs that vendor's CLI installed):
```
/second-opinion ask gemini what it thinks about this schema
```

## Changing settings later

**The model** — the common case, no terminal needed, works the same in the desktop app
and CLI:
```
/advisor-model claude-opus-5
```
Takes effect on the very next `/consult`. No restart. Run it with no argument to see the
current value.

**Provider, base URL, or API key** (also `python_command`) — no skill for those yet, and
how you set them depends on where you're running:

| Where you are | How |
|---|---|
| Terminal | `/plugin configure the-advisor@the-advisor`, then restart Claude Code |
| Desktop app | set a real system environment variable, then fully quit and reopen the app — see below |

The desktop app resolves this plugin under a different internal name than the terminal
does, so anything saved via `--config`/`/plugin configure` lands somewhere the desktop app
never looks (see [Troubleshooting](#troubleshooting)). A plain OS environment variable
skips that entirely — the server just reads it directly, no matter which app asked.
Verified on macOS:

```bash
launchctl setenv ADVISOR_PROVIDER openai-compatible
launchctl setenv ADVISOR_BASE_URL http://localhost:11434/v1
launchctl setenv ADVISOR_API_KEY sk-...
```

then fully quit (Cmd+Q) and reopen the desktop app — it only picks up the new value on
launch. This lasts for your current login session; it won't survive a reboot unless you
also add it to a login item or shell profile. **Windows:** the equivalent should be `setx
ADVISOR_PROVIDER openai-compatible` (or System Properties → Environment Variables) — not
yet verified for this plugin.

Uninstalling clears every `--config` setting — pass `--config` again on reinstall. (The
`/advisor-model` override and the environment-variable method above both live outside
Claude Code entirely, so they survive.)

<details>
<summary>All settings, and every provider's <code>advisor_provider</code> value</summary>

| Option | Env variable | Notes |
|---|---|---|
| `advisor_model` | `ADVISOR_MODEL` | Required. Any name your provider accepts, or `cli-default`. |
| `advisor_provider` | `ADVISOR_PROVIDER` | Auto-detected; override for edge cases. |
| `advisor_base_url` | `ADVISOR_BASE_URL` | For local/gateway endpoints. Makes the key optional. |
| `advisor_api_key` | `ADVISOR_API_KEY` | For `*-api` providers. Falls back to `ANTHROPIC_API_KEY` / `OPENAI_API_KEY`. |
| `python_command` | — | Default `python3`. Set to `python` or `py` on Windows. |

`*-cli` providers shell out to a CLI you're signed into, billing your subscription.
`*-api` providers bill API credits.

| Provider | `advisor_provider` | Model name docs |
|---|---|---|
| Claude (subscription) | `anthropic-cli` | [docs](https://platform.claude.com/docs/en/about-claude/models/overview) |
| Gemini (subscription) | `gemini-cli` | [docs](https://ai.google.dev/gemini-api/docs/models) |
| Claude (API) | `anthropic-api` | same as above |
| OpenAI (API) | `openai-api` | [docs](https://developers.openai.com/api/docs/models) |
| Local / gateway | `openai-compatible` | `ollama list`, or your gateway's list |

</details>

## Troubleshooting

**Changed a `--config`/`/plugin configure` setting, nothing happened** — restart Claude
Code; it only reaches the MCP server on its next start. This doesn't apply to
`/advisor-model`, which needs no restart.

**Model keeps showing a value you didn't just set** — check `~/.the-advisor/model`. Once
it exists it wins over `--config advisor_model=...`/`ADVISOR_MODEL`, so a stale value there
shadows anything set at install. Run `/advisor-model <model>` to update it, or delete the
file to go back to the installed default.

**"does not support this model; version X or newer is required"** — your Claude Code is
too old for that model. Run `claude update` (or upgrade however you installed it — Homebrew
and WinGet don't auto-update by default), or pick a model your current version supports.

**"ADVISOR_MODEL is not set"** — run `/advisor-model <model>`, or re-run the install
command with `--config advisor_model=...`.

**"Not logged in"** — run `claude setup-token`. The bundled agent fills in meanwhile.

**Desktop app can't see a key from `~/.zshrc`, `/plugin configure`, or `--config`** — none
of those reach the desktop app's copy of this plugin. Set it as a real system environment
variable instead (`launchctl setenv` on macOS) and fully restart the app — see
[Changing settings later](#changing-settings-later).

**Windows: plugin won't start** — set `python_command` to `python` via `/plugin configure`
(or pass it at install, see [Quickstart](#quickstart)).

**Windows: `WinError 2` (file not found) during `/consult`** — the advisor couldn't find
your `gemini`/`claude` CLI. The server already resolves absolute paths automatically; make
sure your Node/nvm paths are on your system PATH too.

**Gemini CLI: `gemini mcp list` shows nothing after adding the server** — see
[Not using Claude Code?](#not-using-claude-code) below; this is almost always the
project-scoping gotcha.

## Not using Claude Code?

Clone the repo and point your MCP client at the server directly:

```bash
git clone https://github.com/alitahir6001/the-advisor.git
```

**Gemini CLI:**

1. **Clone the repo** to a permanent location.
2. **Add the MCP server**, from your home directory — not a subdirectory, see the note
   below:
   ```bash
   # macOS / Linux
   gemini mcp add advisor python3 ~/the-advisor/server/advisor_server.py -e ADVISOR_MODEL=gemini-3.8-flash

   # Windows — absolute paths, and 'python' not 'python3'
   gemini mcp add advisor python C:\path\to\the-advisor\server\advisor_server.py -e ADVISOR_MODEL=gemini-3.8-flash
   ```
3. **Link the skills.** The MCP server provides the tool, but `/consult` needs its skill
   linked separately:
   ```bash
   gemini skill link ~/the-advisor/skills/consult
   gemini skill link ~/the-advisor/skills/second-opinion
   gemini skill link ~/the-advisor/skills/advisor-model
   ```

`-e` sets environment variables — same options as the [settings table](#changing-settings-later).

If `gemini mcp list` shows nothing afterward: `gemini mcp add` scopes the config to
whatever directory you ran it in, so running it from inside a project silently confines it
there — either run it from your home directory as shown above, or move the `mcpServers`
block it wrote into `~/.gemini/settings.json` by hand for global availability. JSON config
doesn't expand `~/`, so Windows paths must be absolute.

**No client at all** — one-shot, advice straight to stdout:

```bash
python3 the-advisor/server/advisor_server.py "Queue or direct call?" "10 req/min, user waits."
```

## How it works

![Request lifecycle](docs/lifecycle.svg)

| Component | Role |
|---|---|
| `agents/advisor.md` | Escalation rule. Always in context. |
| `server/advisor_server.py` | The `consult_advisor` MCP tool and standalone CLI. |
| `skills/` | `/consult` for direct questions, `/second-opinion` for one-off calls, `/advisor-model` to change the model. |

The advisor is **stateless** — it sees only what the workhorse sends, never your session.

```bash
python3 -m unittest discover -s server -p 'test_*.py'
```

## Credits

Inspired by the [advisor/executor pattern](https://vanja.io/advisor-and-executor/) at
vanja.io. MIT licensed.
