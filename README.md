# The Advisor

Your cheap workhorse model consults a stronger advisor before hard-to-reverse decisions.
Any model on either side — Claude, Gemini, GPT, or a local model. Nothing is hardcoded.
Works with Claude Code, any MCP client, or [standalone from the command line](#other-workhorses).

Claude Code has a built-in `/advisor` that pairs Claude models inside your session. This
plugin is the multi-provider version: any advisor, a greppable JSON log, and it works from
workhorses that aren't Claude Code. The command is `/consult`.

![How it works](docs/loop.svg)

- [Install](#install)
- [Use it](#use-it)
- [Settings](#settings)
- [Other workhorses](#other-workhorses)
- [How it works](#how-it-works)
- [Troubleshooting](#troubleshooting)

## Install

Requires Python 3 — standard library only, nothing to install.

```bash
claude plugin marketplace add alitahir6001/the-advisor && claude plugin install the-advisor@the-advisor --config advisor_model=claude-opus-5
```

The provider is detected from the model name — `claude-*` uses your Claude CLI, `gemini-*`
uses Gemini, `gpt-*` uses the OpenAI API. For a local model, set the base URL:

```bash
claude plugin install the-advisor@the-advisor \
  --config advisor_model=gemma3:latest \
  --config advisor_base_url=http://localhost:11434/v1
```

Pick a cheap workhorse with `/model` and start a new session — the plugin loads on startup.

On Windows, add `--config python_command=python`.

## Use it

```
/consult is a queue the right call here, or am I overbuilding?
```

Every reply names both models so you know who answered:

```
Advisor   = claude-opus-5 (anthropic-cli)
Workhorse = claude-haiku-4-5
```

The bundled agent also escalates on its own — before architectural calls, after the same
fix fails twice, and on tradeoffs it can't settle alone. It stays quiet on routine work.

Route a one-off question to a different provider (needs that vendor's CLI installed):

```
/second-opinion ask gemini what it thinks about this schema
```

## Settings

Set at install with `--config key=value`, or change later with
`/plugin configure the-advisor@the-advisor` (terminal only — in the desktop app, re-run
the install command). Uninstalling clears settings.

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

## Other workhorses

Not on Claude Code? Clone the repo and point your MCP client at the server:

```bash
git clone https://github.com/alitahir6001/the-advisor.git
```

**Gemini CLI** — manual installation:

1. **Clone the repo** to a permanent location.
2. **Add the MCP server** (global recommended):
   ```bash
   # Windows (use absolute path)
   gemini mcp add advisor python C:\path\to\the-advisor\server\advisor_server.py -e ADVISOR_MODEL=gemini-3.8-flash
   
   # macOS / Linux
   gemini mcp add advisor python3 ~/the-advisor/server/advisor_server.py -e ADVISOR_MODEL=gemini-3.8-flash
   ```
3. **Add the slash commands** (Skills):
   ```bash
   gemini skill link C:\path\to\the-advisor\skills\consult
   gemini skill link C:\path\to\the-advisor\skills\second-opinion
   ```

`-e` sets environment variables on the server — same settings as the table above. Adjust
the path to wherever you cloned the repo. On Windows, use `python` instead of `python3`.

**No client at all** — one shot, advice to stdout:

```bash
python3 the-advisor/server/advisor_server.py "Queue or direct call?" "10 req/min, user waits."
```

## How it works

![Request lifecycle](docs/lifecycle.svg)

| Component | Role |
|---|---|
| `agents/advisor.md` | Escalation rule. Always in context. |
| `server/advisor_server.py` | The `consult_advisor` MCP tool and standalone CLI. |
| `skills/` | `/consult` for direct questions, `/second-opinion` for one-off calls. |

The advisor is **stateless** — it sees only what the workhorse sends, never your session.

```bash
python3 -m unittest discover -s server -p 'test_*.py'
```

## Troubleshooting

**Settings don't apply** — restart Claude Code.

**"does not support this model; version X or newer is required"** — your Claude Code is
too old. Update it, or pick a model your version supports. Homebrew lags by a few days.

**"ADVISOR_MODEL is not set"** — re-run the install command with `--config advisor_model=...`.

**"Not logged in"** — run `claude setup-token`. The bundled agent fills in meanwhile.

**Desktop app can't see your env** — put API keys in `/plugin configure`, not `~/.zshrc`.

**Windows: plugin won't start** — set `python_command` to `python` via `/plugin configure`.

## Gemini CLI: Lessons Learned

If `gemini mcp list` shows no servers after an add, check these common pitfalls:

- **Configuration Scope:** `gemini mcp add` creates a project-specific config if run inside a 
  subdirectory. For global availability, run it from your home directory or manually move 
  the `mcpServers` block to `~/.gemini/settings.json`.
- **Windows Paths:** JSON configuration does not expand `~/`. Use absolute paths (e.g., 
  `C:\path\to\...`) and ensure you use `python` if `python3` is not in your PATH.
- **MCP vs Skills:** Adding an MCP server provides the tools, but slash commands 
  (like `/consult`) require linking the corresponding skill files via `gemini skill link`.

## Credits

Inspired by the [advisor/executor pattern](https://vanja.io/advisor-and-executor/) at
vanja.io. MIT licensed.
