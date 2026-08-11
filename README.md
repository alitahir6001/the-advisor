# The Advisor

A second-opinion layer for [Claude Code](https://claude.com/claude-code).

A cheap, fast model does the work. When it reaches a decision that's expensive to get
wrong, it is *obligated* to consult a stronger model first — automatically, without you
asking. The advisor can be Claude, Gemini, or OpenAI: which model answers is server
config, not code.

```
you ──► workhorse (cheap model) ──consult──► advisor (strong model, any provider)
             │                                          │
             └──────────────── advice ◄─────────────────┘
```

## Why

Frontier models are expensive and slow. Cheap models are fast but make bad
architectural calls. This gets you both: the cheap model drives, and escalates on the
handful of decisions where being wrong is costly.

## Install

```
/plugin marketplace add alitahir6001/the-advisor
```

```
/plugin install the-advisor@the-advisor
```

Requires `python3` (standard library only — nothing to `pip install`).

## Configure the advisor

**Set `ADVISOR_MODEL` to the strongest model you have access to.** This is the one
setting that matters. If you leave it empty, the CLI's own default model answers — which
may be no stronger than your workhorse, defeating the point.

Edit the plugin's `.mcp.json`:

| Variable | Values |
|---|---|
| `ADVISOR_PROVIDER` | `anthropic-cli` (default), `gemini-cli`, `anthropic-api`, `openai-api` |
| `ADVISOR_MODEL` | any model name your provider accepts |
| `ADVISOR_LOG` | consult log path (defaults to the plugin's data directory) |

The `*-cli` providers shell out to a vendor CLI you're already logged into, so they bill
your existing subscription. The `*-api` providers use `ANTHROPIC_API_KEY` /
`OPENAI_API_KEY` and bill credits.

Then set your session to a cheaper model (`/model`) — that's the workhorse. Work
normally.

### If the advisor reports "Not logged in"

The `anthropic-cli` provider shells out to `claude -p`, which needs the CLI itself to be
authenticated — separate from whatever is signed in to your editor. Log in once with
`claude` → `/login`. For a durable headless token, run `claude setup-token` and export
the result as `CLAUDE_CODE_OAUTH_TOKEN` in your shell profile (this variable is passed
through to the advisor subprocess; other `CLAUDE*` variables are deliberately stripped).
Until it's fixed, consults fall back to the bundled advisor agent, so nothing breaks.

## What you get

**Automatic escalation.** The workhorse consults before architectural or hard-to-reverse
decisions, when the same fix has failed twice, or on a tradeoff it can't resolve alone.
It stays silent on routine work.

**Ask directly.** `/advisor what do you think about this approach?` — no escalation bar,
any question qualifies.

**Cross-vendor consults.** `/consult-advisor-cli` routes a one-off question to a specific
vendor CLI when you want a different provider's take.

**A decision log.** Every consult is appended to a JSONL file — question, context,
verbatim reply, provider, elapsed time. Read it with:

```bash
python3 server/consults.py            # recent consults, one line each
python3 server/consults.py 3          # full entry 3
python3 server/consults.py --stats    # counts by provider and day
```

## How it works

Three components, layered so the pattern degrades gracefully:

| Component | Role |
|---|---|
| `agents/advisor.md` | Carries the escalation policy and routes consults. Always in context. |
| `.mcp.json` + `server/advisor_server.py` | The `consult_advisor` tool. Preferred route — honors your provider config. |
| `skills/` | `/advisor` for direct questions, `/consult-advisor-cli` for one-off vendor calls. |

The server is a ~250-line MCP stdio server speaking newline-delimited JSON-RPC. It takes
two strings — `question` and `context` — assembles a prompt with a fixed output contract
(Recommendation / Reasoning / Risks), dispatches to the configured provider by subprocess
or HTTPS, logs the exchange, and returns the reply.

The advisor is **stateless**: it sees only what the workhorse sends it, never the session
history. That forces the workhorse to articulate the problem, which is half the value.
It's also why `context` matters — a non-Claude advisor can't read your files, so that
field is everything it knows.

### One design note

The mandatory escalation rule lives on the *agent description*, not the MCP tool. Tool
schemas can be deferred out of context until something searches for them, and a rule the
model never sees can't fire — verified by testing, which overturned the opposite design.
The agent description is always loaded, so that's where the policy belongs. Everything
else is deliberately non-directive to avoid competing mandates.

## Credits

Inspired by the advisor/executor pattern described in
[vanja.io/advisor-and-executor](https://vanja.io/advisor-and-executor/).

## License

MIT
