#!/usr/bin/env python3
"""Model-agnostic advisor MCP server (stdio transport, newline-delimited JSON-RPC).

Exposes one tool, consult_advisor. Which model answers is server config,
invisible to the workhorse:

  ADVISOR_PROVIDER  anthropic-cli | gemini-cli | anthropic-api | openai-api
  ADVISOR_MODEL     model for that provider. Set this to the strongest model
                    you have. Unset on a CLI provider means the CLI's own
                    default answers - which may be no stronger than the
                    workhorse, defeating the point. Required for *-api.
  ADVISOR_LOG       consult log path (default: beside this file)
  ANTHROPIC_API_KEY / OPENAI_API_KEY  required by the *-api providers only

CLI providers bill the vendor subscription; API providers bill credits.
Pure stdlib on purpose: no install step on a new machine.
"""

import datetime
import json
import os
import subprocess
import sys
import time
import urllib.request

PROTOCOL_VERSION = "2024-11-05"

ADVISOR_SYSTEM = (
    "You are a senior technical advisor consulted mid-task by a working "
    "agent. Answer only what is asked. Reply with: Recommendation (one "
    "clear choice or action), Reasoning (the 2-4 load-bearing points), "
    "Risks (what could make this wrong). Do not write code."
)

TOOL_DESCRIPTION = (
    "Second-opinion advisor on an external model chosen by server config "
    "(ADVISOR_PROVIDER / ADVISOR_MODEL). The preferred consult route for "
    "architectural or hard-to-reverse decisions, twice-failed fixes, and "
    "tradeoffs unresolvable from the task. Send one focused question; put "
    "options, constraints, and what was already tried in context. The "
    "advisor is stateless and sees only what you send. Never consult it "
    "for routine work you can complete yourself."
)

# No default model IDs on purpose: they go stale, and pinning one would
# undercut the point of keeping the advisor identity in config.
PROVIDERS = ("anthropic-cli", "gemini-cli", "anthropic-api", "openai-api")


LOG_PATH = os.environ.get("ADVISOR_LOG") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "consult-log.jsonl"
)


def ensure_log_dir():
    d = os.path.dirname(LOG_PATH)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


def log_consult(provider, model, question, context, reply, error, start):
    # Full verbatim reply on purpose (advisor-reviewed decision, 2026-07-12):
    # summaries lose the conditional caveats that post-mortems need.
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "provider": provider,
        "model": model,
        "elapsed_s": round(time.time() - start, 1),
        "question": question,
        "context": context,
        "reply": reply,
        "error": error,
    }
    try:
        ensure_log_dir()
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except OSError:
        pass


def build_prompt(question, context):
    parts = [ADVISOR_SYSTEM, "Question:\n" + question]
    if context:
        parts.append("Context:\n" + context)
    return "\n\n".join(parts)


def subprocess_env():
    # claude -p refuses/misbehaves when it inherits the parent session's
    # CLAUDE* markers; strip them so the advisor runs as a fresh session.
    # CLAUDE_CODE_OAUTH_TOKEN is the exception - stripping it logs the
    # subprocess out, which is the whole auth for the anthropic-cli path.
    keep = {"CLAUDE_CODE_OAUTH_TOKEN"}
    return {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("CLAUDE") or k in keep
    }


def run_cli(cmd):
    proc = subprocess.run(
        cmd, capture_output=True, text=True, timeout=300, env=subprocess_env()
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"{cmd[0]} exited {proc.returncode}: {proc.stderr.strip()[:500]}"
        )
    return proc.stdout.strip()


def http_json(url, headers, body):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={**headers, "content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def consult(question, context):
    provider = os.environ.get("ADVISOR_PROVIDER", "anthropic-cli")
    if provider not in PROVIDERS:
        raise RuntimeError(
            f"unknown ADVISOR_PROVIDER {provider!r}; expected one of "
            + ", ".join(PROVIDERS)
        )
    model = os.environ.get("ADVISOR_MODEL") or None
    prompt = build_prompt(question, context)
    start = time.time()
    try:
        reply = _dispatch(provider, model, prompt)
        log_consult(provider, model, question, context, reply, None, start)
        return reply
    except Exception as e:
        log_consult(provider, model, question, context, None, str(e), start)
        raise


def _dispatch(provider, model, prompt):
    # CLI providers fall back to the CLI's own default model when unset.
    if provider == "anthropic-cli":
        cmd = ["claude", "-p", prompt]
        if model:
            cmd += ["--model", model]
        return run_cli(cmd)

    if provider == "gemini-cli":
        cmd = ["gemini", "-p", prompt]
        if model:
            cmd = ["gemini", "-m", model, "-p", prompt]
        return run_cli(cmd)

    if not model:
        raise RuntimeError(f"ADVISOR_MODEL must be set for provider {provider}")

    if provider == "anthropic-api":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        data = http_json(
            "https://api.anthropic.com/v1/messages",
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
            {
                "model": model,
                "max_tokens": 2048,
                "system": ADVISOR_SYSTEM,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        return "\n".join(
            b["text"] for b in data["content"] if b["type"] == "text"
        )

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY not set")
    data = http_json(
        "https://api.openai.com/v1/chat/completions",
        {"authorization": f"Bearer {key}"},
        {
            "model": model,
            "messages": [
                {"role": "system", "content": ADVISOR_SYSTEM},
                {"role": "user", "content": prompt},
            ],
        },
    )
    return data["choices"][0]["message"]["content"]


TOOL = {
    "name": "consult_advisor",
    "description": TOOL_DESCRIPTION,
    "inputSchema": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "One focused question - a single decision or problem.",
            },
            "context": {
                "type": "string",
                "description": "Options, constraints, what was already tried, "
                "and repo-relative paths of the relevant files. Non-Claude "
                "advisors cannot read files - this field is all they see.",
            },
        },
        "required": ["question"],
    },
}


def handle(msg):
    method = msg.get("method")
    if method == "initialize":
        return {
            "protocolVersion": msg["params"].get(
                "protocolVersion", PROTOCOL_VERSION
            ),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "advisor", "version": "0.1.0"},
        }
    if method == "tools/list":
        return {"tools": [TOOL]}
    if method == "tools/call":
        args = msg["params"].get("arguments", {})
        try:
            text = consult(args.get("question", ""), args.get("context", ""))
            return {"content": [{"type": "text", "text": text}]}
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Advisor error: {e}"}],
                "isError": True,
            }
    if method == "ping":
        return {}
    return None


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        msg = json.loads(line)
        if "id" not in msg:
            continue
        result = handle(msg)
        if result is None:
            reply = {
                "jsonrpc": "2.0",
                "id": msg["id"],
                "error": {"code": -32601, "message": f"unknown method: {msg.get('method')}"},
            }
        else:
            reply = {"jsonrpc": "2.0", "id": msg["id"], "result": result}
        sys.stdout.write(json.dumps(reply) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
