#!/usr/bin/env python3
"""Doctor: sanity-check the live advisor config, authoritative sources only -
nothing re-derived from a file the server might not actually be reading.

Default mode is free (no advisor call, like `brew doctor`/`flutter doctor`):
checks what's configured, what would run, and shows the last real log entry.
`--live` additionally makes one real advisor call (real cost) to prove the
whole pipeline actually works end to end, not just that it looks configured -
run that before shipping, not on every troubleshooting pass.

    python3 doctor.py          quick, free checks only
    python3 doctor.py --live   also runs one real, paid consult

Exit code doubles as a gate: 0 = pass, 1 = fail.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import advisor_server as adv


def check(label, ok, detail=""):
    print(f"[{'OK  ' if ok else 'FAIL'}] {label}" + (f" - {detail}" if detail else ""))
    return ok


def quick_checks():
    passed = True

    override = adv.read_model_override()
    env_model = os.environ.get("ADVISOR_MODEL")
    if override:
        model, model_source = override, "override file"
    elif env_model:
        model, model_source = env_model, "ADVISOR_MODEL"
    else:
        model, model_source = None, None
    passed &= check("a model is configured", bool(model),
                     f"{model} (from {model_source})" if model else
                     "run /advisor-model <model> or set ADVISOR_MODEL")

    if os.environ.get("ADVISOR_PROVIDER"):
        provider, provider_source = os.environ["ADVISOR_PROVIDER"], "ADVISOR_PROVIDER"
    else:
        provider = adv.infer_provider(model or "", os.environ.get("ADVISOR_BASE_URL", ""))
        provider_source = "inferred from model name"
    passed &= check("provider resolves to a known provider", provider in adv.PROVIDERS,
                     f"{provider} (from {provider_source})")

    if provider in ("anthropic-cli", "gemini-cli"):
        cli = "claude" if provider == "anthropic-cli" else "gemini"
        resolved = shutil.which(cli)
        passed &= check(f"{cli} CLI resolves on PATH", bool(resolved), resolved or "not found")
    elif provider == "openai-compatible":
        passed &= check("ADVISOR_BASE_URL is set", bool(os.environ.get("ADVISOR_BASE_URL")))
    elif provider in ("anthropic-api", "openai-api"):
        var = "ANTHROPIC_API_KEY" if provider == "anthropic-api" else "OPENAI_API_KEY"
        try:
            adv.api_key(var)  # env lookup only - no network call
            passed &= check("an API key resolves", True)
        except RuntimeError as e:
            passed &= check("an API key resolves", False, str(e))

    if os.path.exists(adv.LOG_PATH):
        with open(adv.LOG_PATH) as f:
            lines = [l for l in f if l.strip()]
        if lines:
            last = json.loads(lines[-1])
            print(f"[INFO] last real consult: {last['ts']}  "
                  f"{last['model']} ({last['provider']})  "
                  f"{'error: ' + last['error'] if last.get('error') else 'ok'}")
        else:
            print(f"[INFO] log exists but is empty: {adv.LOG_PATH}")
    else:
        print(f"[INFO] no consult log yet at {adv.LOG_PATH}")

    return passed


def live_check():
    before = os.path.getsize(adv.LOG_PATH) if os.path.exists(adv.LOG_PATH) else -1
    try:
        reply = adv.consult("Reply with exactly the word OK and nothing else.", "")
    except Exception as e:
        check("consult() completed without raising", False, str(e))
        return False

    passed = check("consult() completed without raising", True)

    grew = os.path.exists(adv.LOG_PATH) and os.path.getsize(adv.LOG_PATH) > max(before, 0)
    passed &= check("consult log grew by a new entry", grew, adv.LOG_PATH)
    if grew:
        with open(adv.LOG_PATH) as f:
            last = json.loads(f.readlines()[-1])
        passed &= check(
            "log entry's model/provider match the reply header",
            f"{last['model']} ({last['provider']})" in reply,
            f"log says: {last['model']} ({last['provider']})",
        )
        passed &= check(
            "log entry records which real input resolved model/provider",
            bool(last.get("model_source")) and bool(last.get("provider_source")),
            f"model_source={last.get('model_source')!r}, "
            f"provider_source={last.get('provider_source')!r}",
        )
    return passed


def main():
    live = "--live" in sys.argv[1:]
    passed = quick_checks()
    if live:
        print()
        passed = live_check() and passed
        print("\nPASS (live - real advisor call made)" if passed else "\nFAIL (live)")
    else:
        print("\nPASS (quick check only - no real advisor call made; add --live to fully "
              "verify end to end)" if passed else "\nFAIL (quick check)")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
