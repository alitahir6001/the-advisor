# The Advisor

Your cheap workhorse model consults a stronger advisor before hard-to-reverse decisions.
Fast and cheap by default, strong where it counts.

**Any model on either side.** The advisor can be Claude, Gemini, GPT, or a model running on
your own machine. The workhorse can be Claude Code, any MCP client, or a shell script.
Nothing is hardcoded — you pick both.

![How it works](docs/loop.svg)

## Setup

Three steps. Requires `python3` — standard library only, nothing to install.

**1. Install**

```
/plugin marketplace add alitahir6001/the-advisor
```

```
/plugin install the-advisor@the-advisor
```

**2. Name your advisor.** Open this file:

```
~/.claude/plugins/cache/the-advisor/the-advisor/<version>/.mcp.json
```

Set `ADVISOR_MODEL` to the strongest model you have, then restart Claude Code:

```json
"ADVISOR_MODEL": "opus"
```

It ships empty, which falls back to your CLI's default — possibly no stronger than your
workhorse, which defeats the point. This is the one step you shouldn't skip.

**3. Pick a cheap workhorse.** Run `/model`, choose something fast.

That's it. Consults now go to the strong model, everything else stays cheap.

## Using a different advisor

Step 2 assumes Claude. To point the advisor somewhere else, set `ADVISOR_PROVIDER` in the
same file:

| Advisor | `ADVISOR_PROVIDER` | Also set |
|---|---|---|
| Claude, via your subscription | `anthropic-cli` (default) | `ADVISOR_MODEL=opus` |
| Gemini, via your subscription | `gemini-cli` | `ADVISOR_MODEL=gemini-2.5-pro` |
| Claude, via API credits | `anthropic-api` | `ANTHROPIC_API_KEY`, `ADVISOR_MODEL` |
| GPT, via API credits | `openai-api` | `OPENAI_API_KEY`, `ADVISOR_MODEL` |
| **Local model** (ollama, LM Studio, vLLM) | `openai-compatible` | `ADVISOR_BASE_URL`, `ADVISOR_MODEL` |
| Gateway (OpenRouter, Groq, Together) | `openai-compatible` | `ADVISOR_BASE_URL`, `OPENAI_API_KEY`, `ADVISOR_MODEL` |

A local advisor needs no API key:

```json
"ADVISOR_PROVIDER": "openai-compatible",
"ADVISOR_BASE_URL": "http://localhost:11434/v1",
"ADVISOR_MODEL": "gemma3:latest"
```

`ADVISOR_BASE_URL` works with `openai-api` and `anthropic-api` too, if you route through a
proxy. Setting it makes the API key optional.

## Using a different workhorse

Not on Claude Code? Clone the repo — the server works on its own.

### Any MCP client

The server is plain MCP over stdio. Clone the repo and register it — Gemini CLI, for
example:

```bash
gemini mcp add advisor python3 /path/to/the-advisor/server/advisor_server.py \
  -e ADVISOR_PROVIDER=openai-compatible \
  -e ADVISOR_BASE_URL=http://localhost:11434/v1 \
  -e ADVISOR_MODEL=gemma3:latest
```

### No client at all

Same code path, one shot:

```bash
ADVISOR_PROVIDER=gemini-cli python3 server/advisor_server.py \
  "Queue or direct call here?" "Single node, 10 req/min, user waits on it."
```

Advice to stdout, errors to stderr, non-zero exit on failure — pipe it or wire it into
whatever agent you already have.

## Use it

Ask directly:

```
/advisor is a queue the right call here, or am I overbuilding?
```

Or let it escalate on its own — the bundled agent consults before architectural calls,
twice-failed fixes, and unresolvable tradeoffs, and stays quiet on routine work.

Route one question to an unconfigured provider (not logged, no restart needed):

```
/second-opinion ask gemini what it thinks about this schema
```

Read the log — every consult is appended as JSON:

```bash
python3 server/consults.py            # recent consults, one per line
python3 server/consults.py 3          # full entry 3
python3 server/consults.py --stats    # counts by provider and day
```

### Other settings

| Variable | Values |
|---|---|
| `ADVISOR_MODEL` | any model name your provider accepts |
| `ADVISOR_BASE_URL` | API root override; makes the API key optional |
| `ADVISOR_LOG` | consult log path (defaults to the plugin's data directory) |

`*-cli` providers shell out to a CLI you're signed into, billing your subscription.
`*-api` providers bill credits. The vendor API paths have test coverage but no live call
has been made against them — no API keys on the author's machine. The local
`openai-compatible` path is exercised against ollama.

## How it works

![Request lifecycle](docs/lifecycle.svg)

| Component | Role |
|---|---|
| `agents/advisor.md` | Carries the escalation rule. Always in context. Fallback advisor when the MCP tool is down. |
| `server/advisor_server.py` | The `consult_advisor` MCP tool, and the standalone CLI. |
| `skills/` | `/advisor` for direct questions, `/second-opinion` for one-off calls to an unconfigured provider. |

The advisor is **stateless** — it sees only what the workhorse sends, never your session
history. That forces the workhorse to articulate the problem, which is half the value, and
it's why `context` matters: a non-Claude advisor can't read your files.

Run the tests with:

```bash
python3 -m unittest discover -s server -p 'test_*.py'
```

## Troubleshooting

**"Not logged in" / "OAuth session expired"** — the `anthropic-cli` provider needs the CLI
authenticated separately from your editor. Run `claude setup-token`.

If you launch Claude Code as a desktop app, `~/.zshrc` won't work — GUI apps don't source
shell rc files. Add a top-level `env` block to `~/.claude/settings.json` instead:

```json
{
  "env": {
    "CLAUDE_CODE_OAUTH_TOKEN": "<your token>"
  }
}
```

Consults fall back to the bundled agent meanwhile, so nothing breaks.

## Credits

Inspired by the advisor/executor pattern described in
[vanja.io/advisor-and-executor](https://vanja.io/advisor-and-executor/).

MIT licensed.
