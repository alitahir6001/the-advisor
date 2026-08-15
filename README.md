# The Advisor

A Claude Code plugin: your cheap workhorse model consults a stronger advisor — Claude,
Gemini, or GPT — before hard-to-reverse decisions. Fast and cheap by default, strong
where it counts.

![How it works](docs/loop.svg)

## Install

```
/plugin marketplace add alitahir6001/the-advisor
```

```
/plugin install the-advisor@the-advisor
```

Requires `python3`. Standard library only.

## Configure

**1. Advisor model** — edit your installed `.mcp.json`:

```
~/.claude/plugins/cache/the-advisor/the-advisor/<version>/.mcp.json
```

```json
"ADVISOR_MODEL": "opus"
```

Use the strongest model you have. It ships empty, which falls back to your CLI's default —
possibly no stronger than your workhorse. Restart the session after editing.

**2. Workhorse model** — run `/model`, pick something cheap.

Done.

### Optional

| Variable | Values |
|---|---|
| `ADVISOR_PROVIDER` | `anthropic-cli` (default), `gemini-cli`, `anthropic-api`, `openai-api` |
| `ADVISOR_MODEL` | any model name your provider accepts |
| `ADVISOR_LOG` | consult log path (defaults to the plugin's data directory) |

`*-cli` providers shell out to a CLI you're signed into, billing your subscription.
`*-api` providers use `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` and bill credits — written
but untested, no API keys on the author's machine.

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

## How it works

![Request lifecycle](docs/lifecycle.svg)

| Component | Role |
|---|---|
| `agents/advisor.md` | Carries the escalation rule. Always in context. Fallback advisor when the MCP tool is down. |
| `server/advisor_server.py` | The `consult_advisor` MCP tool. Preferred route — honors your provider config. |
| `skills/` | `/advisor` for direct questions, `/second-opinion` for one-off calls to an unconfigured provider. |

The advisor is **stateless** — it sees only what the workhorse sends, never your session
history. That forces the workhorse to articulate the problem, which is half the value, and
it's why `context` matters: a non-Claude advisor can't read your files.

## Troubleshooting

**"Not logged in" / "OAuth session expired"** — the `anthropic-cli` provider needs the CLI
authenticated separately from your editor. Run `claude setup-token`.

If you launch Claude Code as a desktop app, `~/.zshrc` won't work — GUI apps don't source
shell rc files. Add a top-level `env` block to `~/.claude/settings.json` instead:

```json
{
  "env": {
    "CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat01-..."
  }
}
```

Consults fall back to the bundled agent meanwhile, so nothing breaks.

## Credits

Inspired by the advisor/executor pattern described in
[vanja.io/advisor-and-executor](https://vanja.io/advisor-and-executor/).

MIT licensed.
