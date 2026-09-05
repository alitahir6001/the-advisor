# The Advisor

Your cheap workhorse model consults a stronger advisor before hard-to-reverse decisions.
Fast and cheap by default, strong where it counts.

**Any model on either side.** The advisor can be Claude, Gemini, GPT, or a model on your
own machine. The workhorse can be Claude Code, any MCP client, or a shell script. Nothing
is hardcoded — you pick both.

Claude Code has its own built-in Advisor (`/advisor`), which pairs Claude models inside
your session. This is the other shape of the same idea: any provider including local
models, a greppable JSON log of every consult, and it works from workhorses that aren't
Claude Code. The skill here is `/consult`, because the built-in owns `/advisor`.

![How it works](docs/loop.svg)

- [Install](#install)
- [Use it](#use-it)
- [Choose your advisor](#choose-your-advisor)
- [Settings](#settings)
- [Other workhorses](#other-workhorses)
- [How it works](#how-it-works)
- [Troubleshooting](#troubleshooting)

## Install

Requires Python — standard library only, nothing to install.

**1. Install and name your advisor**, in a terminal. Set `advisor_model` to the strongest
model you have access to:

```bash
claude plugin marketplace add alitahir6001/the-advisor
```

```bash
claude plugin install the-advisor@the-advisor --config advisor_model=claude-opus-5
```

Don't skip the model — left blank, the advisor refuses to run and tells you so. That is
deliberate: it used to fall back to your CLI's default, which meant the advisor quietly
became whatever your workhorse already was.

On Windows, add `--config python_command=python`.

**2. Pick a cheap workhorse.** In Claude Code, run `/model` and choose something fast.

**3. Restart Claude Code.** Consults now go to the strong model, everything else stays
cheap.

To change a setting later, `/plugin configure the-advisor@the-advisor` opens a menu — but
**only in the terminal**, not the desktop app. From the desktop app, re-run the install
command above with the new value. Note that uninstalling clears your settings.

## Use it

Three ways in, all typed into Claude Code:

```
/consult is a queue the right call here, or am I overbuilding?
```

**Or let it escalate on its own.** Just work — the bundled agent consults before
architectural calls, after the same fix fails twice, and on tradeoffs it can't settle
alone. It stays quiet on routine work.

**Or route one question elsewhere**, to a provider you haven't configured — needs that
vendor's CLI installed and signed in:

```
/second-opinion ask gemini what it thinks about this schema
```

### Check it worked

A consult on the wrong model looks exactly like one on the right model. The log tells them
apart. Ask the advisor anything, then:

```bash
cd ~/.claude/plugins/cache/the-advisor/the-advisor/0.1.5/server
export ADVISOR_LOG=~/.claude/plugins/data/the-advisor-the-advisor/consult-log.jsonl
python3 consults.py       # list consults
python3 consults.py 0     # open one: the header names the model that answered
```

The advisor won't run without a model, so that header always names the model you chose.
Older entries logged `model: None` — those ran on the CLI's default, from when an unset
model was allowed to fall through silently. (`0.1.5` is the installed version — change it if yours differs.)

## Choose your advisor

Set `advisor_provider` the same way you set the model — `--config advisor_provider=...` at
install, or `/plugin configure` in a terminal.

Model names aren't checked here; they're passed straight through. A bad one fails on the
first consult with the vendor's own error, which names the model, so read it carefully — a
correct name can also be rejected because your Claude Code is too old for that model.

| Advisor | `advisor_provider` | Also set | Model names |
|---|---|---|---|
| Claude, via subscription | `anthropic-cli` (default) | — | [docs](https://platform.claude.com/docs/en/about-claude/models/overview) · `claude-opus-5` |
| Gemini, via subscription | `gemini-cli` | — | [docs](https://ai.google.dev/gemini-api/docs/models) · `gemini-3.1-pro-preview` |
| Claude, via API credits | `anthropic-api` | `advisor_api_key` | same as above |
| GPT, via API credits | `openai-api` | `advisor_api_key` | [docs](https://developers.openai.com/api/docs/models) · `gpt-5.6` |
| Local (ollama, LM Studio, vLLM) | `openai-compatible` | `advisor_base_url` | `ollama list` · `gemma3:latest` |
| Gateway (OpenRouter, Groq) | `openai-compatible` | `advisor_base_url`, `advisor_api_key` | your gateway's list |

Examples current as of August 2026. `*-cli` providers also take that CLI's short aliases,
like `opus`, and `cli-default` to deliberately use whatever your CLI defaults to. A local
advisor needs no API key.

## Settings

Everything is set through `/plugin configure`. The server reads the same values from the
environment, which is how the standalone paths below work.

| Option | Environment variable | Notes |
|---|---|---|
| `advisor_model` | `ADVISOR_MODEL` | required; any name your provider accepts, or `cli-default` |
| `advisor_provider` | `ADVISOR_PROVIDER` | one of the five values above |
| `advisor_base_url` | `ADVISOR_BASE_URL` | API root override; makes the key optional |
| `advisor_api_key` | `ADVISOR_API_KEY` | falls back to `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` |
| `python_command` | — | how python3 is invoked; `python` or `py` on Windows |
| — | `ADVISOR_LOG` | consult log path |

`*-cli` providers shell out to a CLI you're signed into, billing your subscription.
`*-api` providers bill credits.

## Other workhorses

Not on Claude Code? Clone the repo — the server runs on its own.

**Any MCP client.** Plain MCP over stdio. Gemini CLI, for example:

```bash
gemini mcp add advisor python3 /path/to/the-advisor/server/advisor_server.py \
  -e ADVISOR_PROVIDER=openai-compatible \
  -e ADVISOR_BASE_URL=http://localhost:11434/v1 \
  -e ADVISOR_MODEL=gemma3:latest
```

**No client at all.** Same code path, one shot — advice to stdout, errors to stderr,
non-zero exit on failure:

```bash
ADVISOR_PROVIDER=gemini-cli python3 server/advisor_server.py \
  "Queue or direct call here?" "Single node, 10 req/min, user waits on it."
```

## How it works

![Request lifecycle](docs/lifecycle.svg)

| Component | Role |
|---|---|
| `agents/advisor.md` | Carries the escalation rule. Always in context. Fallback when the MCP tool is down. |
| `server/advisor_server.py` | The `consult_advisor` MCP tool, and the standalone CLI. |
| `skills/` | `/consult` for direct questions, `/second-opinion` for one-off calls. |

The advisor is **stateless** — it sees only what the workhorse sends, never your session
history. That forces the workhorse to articulate the problem, which is half the value, and
it's why `context` matters: a non-Claude advisor can't read your files.

```bash
python3 -m unittest discover -s server -p 'test_*.py'
```

## Troubleshooting

**Settings don't apply** — restart Claude Code. Config is read when the server starts.

**`Executable not found in $PATH: ${user_config...}`** — you updated while Claude Code was
open, and the update added a new setting your running session doesn't know about. Restart.

**"does not support this model; version X or newer is required"** — the model name is
fine, your Claude Code is too old for it. Update it, or pick a model your version supports.
Homebrew installs lag the official release by a few days.

**"ADVISOR_MODEL is not set"** — `/plugin configure` never got a value, or you haven't
restarted since setting one. If you genuinely want your CLI's own default model, set
`advisor_model` to `cli-default`.

**"Not logged in" / "OAuth session expired"** — `anthropic-cli` needs the CLI
authenticated separately from your editor. Run `claude setup-token`. Consults fall back to
the bundled agent meanwhile, so nothing breaks.

**The desktop app can't see your environment** — GUI apps don't read `~/.zshrc`. Put API
keys in `/plugin configure`, not your shell. For the OAuth token, add a top-level `env`
block to `~/.claude/settings.json` with `CLAUDE_CODE_OAUTH_TOKEN`.

**Windows: the plugin won't start** — Windows has no `python3`. Set `python_command` to
`python` or `py` in `/plugin configure`, then restart.

**The vendor API paths** (`anthropic-api`, `openai-api`) have test coverage but no live
call has ever been made against them — no API keys on the author's machine. The local
`openai-compatible` path is exercised against ollama.

## Credits

Inspired by the advisor/executor pattern at
[vanja.io/advisor-and-executor](https://vanja.io/advisor-and-executor/).

MIT licensed.
