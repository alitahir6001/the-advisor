#!/usr/bin/env python3
"""Advisor MCP server: stdio transport, newline-delimited JSON-RPC, one tool.

Which model answers is server config (ADVISOR_*, see README), invisible to
the workhorse. Stdlib only, so there is no install step.

    python3 advisor_server.py                  serve MCP on stdio
    python3 advisor_server.py "q" ["context"]  one-shot, no MCP client needed
"""

import datetime
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request

PROTOCOL_VERSION = "2024-11-05"

ADVISOR_SYSTEM = (
    "You are a senior technical advisor. Provide expert analysis and "
    "professional judgment on technical issues, workflows, and systems. "
    "Answer directly. For complex architectural or strategic choices, "
    "structure your reply with: Analysis, Recommendation, and Risks. "
    "Do not write code unless asked."
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

# Opt-in only: an unset ADVISOR_MODEL is more often an accident than intent.
CLI_DEFAULT = "cli-default"

# No default model IDs - they go stale and undercut per-user config.
PROVIDERS = (
    "anthropic-cli",
    "gemini-cli",
    "anthropic-api",
    "openai-api",
    "openai-compatible",
)

# openai-compatible is openai-api pointed elsewhere - no default host.
API_BASES = {
    "anthropic-api": "https://api.anthropic.com/v1",
    "openai-api": "https://api.openai.com/v1",
    "openai-compatible": None,
}


def infer_provider(model, base_url=""):
    """Best-guess provider from the model name. Explicit ADVISOR_PROVIDER wins."""
    if base_url:
        return "openai-compatible"
    if not model or model == CLI_DEFAULT:
        return "anthropic-cli"
    m = model.lower()
    if m.startswith(("gemini-", "gemini_")):
        return "gemini-cli"
    if m.startswith(("gpt-", "o1-", "o3-", "o4-", "chatgpt-")):
        return "openai-api"
    return "anthropic-cli"


# Fixed, identity-independent path - desktop app and CLI resolve this
# plugin differently otherwise (see CLAUDE.md gotcha 25).
THE_ADVISOR_DIR = os.path.expanduser("~/.the-advisor")

LOG_PATH = os.environ.get("ADVISOR_LOG") or os.path.join(
    THE_ADVISOR_DIR, "consult-log.jsonl"
)


def ensure_log_dir():
    d = os.path.dirname(LOG_PATH)
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)


MODEL_OVERRIDE_PATH = os.path.join(THE_ADVISOR_DIR, "model")


def read_model_override():
    # File, not userConfig - identity-independent, re-read every call, no
    # restart needed (see CLAUDE.md gotcha 21).
    try:
        with open(MODEL_OVERRIDE_PATH) as f:
            return f.read().strip() or None
    except OSError:
        return None


def log_consult(provider, model, question, context, reply, error, start,
                 model_source=None, provider_source=None):
    # Full verbatim reply on purpose and confirm the model being used.
    entry = {
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "provider": provider,
        "provider_source": provider_source,
        "model": model,
        "model_source": model_source,
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


def attribution(provider, model, workhorse):
    return (
        f"Advisor   = {model} ({provider})\n"
        f"Workhorse = {workhorse or 'not reported'}"
    )


def build_prompt(question, context):
    parts = [ADVISOR_SYSTEM, "Question:\n" + question]
    if context:
        parts.append("Context:\n" + context)
    return "\n\n".join(parts)


def subprocess_env():
    # Strip inherited CLAUDE* vars so the subprocess runs fresh, except the
    # OAuth token - stripping it would log the CLI out.
    keep = {"CLAUDE_CODE_OAUTH_TOKEN"}
    return {
        k: v
        for k, v in os.environ.items()
        if not k.startswith("CLAUDE") or k in keep
    }


def run_cli(cmd):
    # Resolve absolute path - avoids WinError 2 on Windows.
    resolved = shutil.which(cmd[0])
    if resolved:
        cmd[0] = resolved

    # stdin=DEVNULL: otherwise the child inherits the live JSON-RPC pipe and stalls.
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,
        env=subprocess_env(),
        stdin=subprocess.DEVNULL,
        shell=os.name == "nt",
    )
    if proc.returncode != 0:
        # CLIs report auth failures on stdout, so stderr alone hides the cause.
        detail = (proc.stderr.strip() or proc.stdout.strip())[:500]
        raise RuntimeError(f"{cmd[0]} exited {proc.returncode}: {detail}")
    return proc.stdout.strip()


def api_base(provider):
    base = os.environ.get("ADVISOR_BASE_URL") or API_BASES[provider]
    if not base:
        raise RuntimeError(
            "ADVISOR_BASE_URL must be set for provider openai-compatible "
            "(e.g. http://localhost:11434/v1 for ollama)"
        )
    return base.rstrip("/")


def api_key(var):
    # ADVISOR_API_KEY wins, else the vendor var; no key required for a local
    # server behind ADVISOR_BASE_URL.
    key = os.environ.get("ADVISOR_API_KEY") or os.environ.get(var)
    if not key and not os.environ.get("ADVISOR_BASE_URL"):
        raise RuntimeError(f"neither ADVISOR_API_KEY nor {var} is set")
    return key


def http_json(url, headers, body):
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode(),
        headers={**headers, "content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.load(resp)


def consult(question, context, workhorse=None):
    # Override file wins over ADVISOR_MODEL (CLAUDE.md gotcha 21); sources are
    # recorded here, at the point of decision, for the log (gotcha 26).
    override = read_model_override()
    if override:
        model, model_source = override, "override file (~/.the-advisor/model)"
    elif os.environ.get("ADVISOR_MODEL"):
        model, model_source = os.environ["ADVISOR_MODEL"], "ADVISOR_MODEL"
    else:
        model, model_source = None, None
    if not model:
        # Refuse rather than silently reuse the workhorse's own model (gotcha 11).
        raise RuntimeError(
            "ADVISOR_MODEL is not set. Easiest fix, no restart needed:\n"
            "  /advisor-model <model>\n"
            "Or set it at install time:\n"
            "  claude plugin install the-advisor@the-advisor "
            "--config advisor_model=<model>\n"
            "Use 'cli-default' as the model to deliberately run your CLI's own "
            "default. (/plugin configure also works, but only in a terminal.)"
        )
    # `or` not a get() default: an unset userConfig key substitutes as "".
    if os.environ.get("ADVISOR_PROVIDER"):
        provider, provider_source = os.environ["ADVISOR_PROVIDER"], "ADVISOR_PROVIDER"
    else:
        provider = infer_provider(model, os.environ.get("ADVISOR_BASE_URL", ""))
        provider_source = "inferred from model name"
    if provider not in PROVIDERS:
        raise RuntimeError(
            f"unknown ADVISOR_PROVIDER {provider!r}; expected one of "
            + ", ".join(PROVIDERS)
        )
    prompt = build_prompt(question, context)
    start = time.time()
    try:
        reply = _dispatch(provider, model, prompt)
        log_consult(provider, model, question, context, reply, None, start,
                    model_source, provider_source)
        return attribution(provider, model, workhorse) + "\n\n" + reply
    except Exception as e:
        log_consult(provider, model, question, context, None, str(e), start,
                    model_source, provider_source)
        raise


def _dispatch(provider, model, prompt):
    # The one way to get the CLI's own default, and it has to be asked for.
    if model == CLI_DEFAULT:
        model = None

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
        raise RuntimeError(
            f"{CLI_DEFAULT!r} only works with the *-cli providers; "
            f"provider {provider} needs a real ADVISOR_MODEL"
        )

    if provider == "anthropic-api":
        # Base first - a missing host is a more useful error than a maybe-unneeded key.
        base = api_base(provider)
        key = api_key("ANTHROPIC_API_KEY")
        headers = {"anthropic-version": "2023-06-01"}
        if key:
            headers["x-api-key"] = key
        data = http_json(
            base + "/messages",
            headers,
            {
                "model": model,
                # Advice runs long; 2048 truncated replies mid-Risks.
                "max_tokens": 4096,
                "system": ADVISOR_SYSTEM,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        return "\n".join(
            b["text"] for b in data["content"] if b["type"] == "text"
        )

    base = api_base(provider)
    key = api_key("OPENAI_API_KEY")
    headers = {"authorization": f"Bearer {key}"} if key else {}
    data = http_json(
        base + "/chat/completions",
        headers,
        {
            "model": model,
            # No max_tokens - optional here, and newer models reject it for max_completion_tokens.
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
            "workhorse_model": {
                "type": "string",
                "description": "The model YOU are running as, e.g. "
                "claude-haiku-4-5. Echoed back in the reply header so the user "
                "can see advisor and workhorse are not the same model. Say so "
                "plainly if you are unsure rather than guessing.",
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
            # Kept in step with .claude-plugin/plugin.json by the test suite.
            "serverInfo": {"name": "advisor", "version": "0.4.0"},
        }
    if method == "tools/list":
        return {"tools": [TOOL]}
    if method == "tools/call":
        args = msg["params"].get("arguments", {})
        try:
            text = consult(
                args.get("question", ""),
                args.get("context", ""),
                args.get("workhorse_model"),
            )
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
        # A malformed line must not kill the server for the whole session.
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(msg, dict) or "id" not in msg:
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


def ask_once(argv):
    """One-shot consult for workhorses that speak no MCP."""
    try:
        sys.stdout.write(consult(argv[0], argv[1] if len(argv) > 1 else "") + "\n")
    except Exception as e:
        sys.stderr.write(f"Advisor error: {e}\n")
        return 1
    return 0


if __name__ == "__main__":
    # Args mean one-shot; no args means serve MCP on stdio.
    sys.exit(ask_once(sys.argv[1:]) if len(sys.argv) > 1 else main())
