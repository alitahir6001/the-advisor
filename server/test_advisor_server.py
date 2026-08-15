#!/usr/bin/env python3
"""Tests for the advisor MCP server.

Stdlib only, to match the server's no-install promise:

    python3 -m unittest discover -s server -p 'test_*.py' -v

Five tests, one per concern. Nothing here touches the network, a vendor CLI,
or the real consult log.
"""

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import advisor_server as adv

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADVISOR_VARS = (
    "ADVISOR_PROVIDER",
    "ADVISOR_MODEL",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
)


@contextmanager
def env(**overrides):
    """Run with a known-clean advisor env; unnamed vars are unset."""
    with mock.patch.dict(os.environ):
        for key in ADVISOR_VARS:
            os.environ.pop(key, None)
        for key, value in overrides.items():
            os.environ[key] = value
        yield


@contextmanager
def temp_log():
    """Redirect the consult log; LOG_PATH is fixed at import time."""
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "consult-log.jsonl")
        with mock.patch.object(adv, "LOG_PATH", path):
            yield path


def log_entries(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def completed(stdout="advice", stderr="", returncode=0):
    return subprocess.CompletedProcess([], returncode, stdout, stderr)


class FakeResponse(io.StringIO):
    """urlopen's context-manager contract, backed by a canned JSON body."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class TestJsonRpcLoop(unittest.TestCase):
    """The loop is the only entry point: nothing may take it down mid-session."""

    def test_session_survives_bad_input_and_provider_failure(self):
        requests = [
            "",
            "{not json at all",
            json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}),
            json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                        "params": {"protocolVersion": "2025-06-18"}}),
            json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"}),
            json.dumps({"jsonrpc": "2.0", "id": 3, "method": "tools/call",
                        "params": {"arguments": {"question": "q", "context": "c"}}}),
            json.dumps({"jsonrpc": "2.0", "id": 4, "method": "totally/unknown"}),
            json.dumps({"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                        "params": {"arguments": {"question": "boom"}}}),
            json.dumps({"jsonrpc": "2.0", "id": 6, "method": "ping"}),
        ]

        def fake_dispatch(provider, model, prompt):
            if "boom" in prompt:
                raise RuntimeError("provider exploded")
            return "advice"

        with env(), temp_log() as log, \
                mock.patch.object(adv, "_dispatch", fake_dispatch), \
                mock.patch.object(sys, "stdin", io.StringIO("\n".join(requests) + "\n")), \
                mock.patch.object(sys, "stdout", io.StringIO()) as out:
            adv.main()
            replies = [json.loads(line) for line in out.getvalue().splitlines() if line]
            # Read before the temp dir goes away.
            entries = log_entries(log)

        # Blank and malformed lines are skipped, the notification draws no reply,
        # and every id after them is still answered - in order.
        self.assertEqual([r["id"] for r in replies], [1, 2, 3, 4, 5, 6])
        self.assertTrue(all(r["jsonrpc"] == "2.0" for r in replies))
        by_id = {r["id"]: r for r in replies}

        init = by_id[1]["result"]
        self.assertEqual(init["protocolVersion"], "2025-06-18")
        self.assertIn("tools", init["capabilities"])
        self.assertEqual(init["serverInfo"]["name"], "advisor")

        tools = by_id[2]["result"]["tools"]
        self.assertEqual([t["name"] for t in tools], ["consult_advisor"])
        self.assertEqual(tools[0]["inputSchema"]["required"], ["question"])

        ok = by_id[3]["result"]
        self.assertEqual(ok["content"][0]["text"], "advice")
        self.assertNotIn("isError", ok)

        self.assertEqual(by_id[4]["error"]["code"], -32601)

        failed = by_id[5]["result"]
        self.assertTrue(failed["isError"])
        self.assertIn("provider exploded", failed["content"][0]["text"])

        self.assertEqual(by_id[6]["result"], {})

        # Both consults are on the record, the failure included.
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["reply"], "advice")
        self.assertIsNone(entries[0]["error"])
        self.assertIsNone(entries[1]["reply"])
        self.assertIn("provider exploded", entries[1]["error"])


class TestProviderDispatch(unittest.TestCase):
    """The model-agnostic promise. The *-api adapters get no other coverage."""

    def test_every_provider_builds_the_right_call(self):
        prompt = adv.build_prompt("q", "c")

        cli_cases = [
            ("anthropic-cli", None, ["claude", "-p", prompt]),
            ("anthropic-cli", "big", ["claude", "-p", prompt, "--model", "big"]),
            ("gemini-cli", None, ["gemini", "-p", prompt]),
            # Note the flag order flip: -m comes before -p here, not after.
            ("gemini-cli", "gem", ["gemini", "-m", "gem", "-p", prompt]),
        ]
        for provider, model, expected in cli_cases:
            with self.subTest(provider=provider, model=model):
                overrides = {"ADVISOR_PROVIDER": provider}
                if model:
                    overrides["ADVISOR_MODEL"] = model
                with env(**overrides), temp_log(), \
                        mock.patch.object(adv.subprocess, "run",
                                          return_value=completed()) as run:
                    self.assertEqual(adv.consult("q", "c"), "advice")
                self.assertEqual(run.call_args.args[0], expected)

        api_cases = [
            {
                "provider": "anthropic-api",
                "keyvar": "ANTHROPIC_API_KEY",
                "url": "https://api.anthropic.com/v1/messages",
                "headers": {"x-api-key": "k", "anthropic-version": "2023-06-01"},
                "body": {"content": [{"type": "text", "text": "advice"},
                                     {"type": "thinking", "thinking": "ignored"}]},
                # Required by this API, and 2048 truncated replies mid-Risks.
                "min_max_tokens": 4096,
            },
            {
                "provider": "openai-api",
                "keyvar": "OPENAI_API_KEY",
                "url": "https://api.openai.com/v1/chat/completions",
                "headers": {"authorization": "Bearer k"},
                "body": {"choices": [{"message": {"content": "advice"}}]},
            },
        ]
        for case in api_cases:
            with self.subTest(provider=case["provider"]):
                overrides = {"ADVISOR_PROVIDER": case["provider"],
                             "ADVISOR_MODEL": "strong", case["keyvar"]: "k"}
                with env(**overrides), temp_log(), \
                        mock.patch.object(adv.urllib.request, "urlopen") as urlopen:
                    urlopen.return_value = FakeResponse(json.dumps(case["body"]))
                    # Only text blocks survive; other block types are dropped.
                    self.assertEqual(adv.consult("q", "c"), "advice")

                req = urlopen.call_args.args[0]
                self.assertEqual(req.full_url, case["url"])
                self.assertEqual(req.method, "POST")
                sent = {k.lower(): v for k, v in req.headers.items()}
                for header, value in case["headers"].items():
                    self.assertEqual(sent[header], value)
                self.assertEqual(sent["content-type"], "application/json")

                body = json.loads(req.data)
                self.assertEqual(body["model"], "strong")
                if "min_max_tokens" in case:
                    self.assertGreaterEqual(body["max_tokens"], case["min_max_tokens"])
                else:
                    # Optional here; setting it would cap replies and newer
                    # models reject the field outright.
                    self.assertNotIn("max_tokens", body)

        # Misconfiguration fails loudly, and names what to fix.
        with env(ADVISOR_PROVIDER="claude-4-opus"), temp_log():
            with self.assertRaises(RuntimeError) as e:
                adv.consult("q", "c")
            self.assertIn("anthropic-cli", str(e.exception))

        for provider in ("anthropic-api", "openai-api"):
            with self.subTest(provider=provider, missing="model"), \
                    env(ADVISOR_PROVIDER=provider), temp_log():
                with self.assertRaises(RuntimeError) as e:
                    adv.consult("q", "c")
                self.assertIn("ADVISOR_MODEL", str(e.exception))

        for provider, keyvar in (("anthropic-api", "ANTHROPIC_API_KEY"),
                                 ("openai-api", "OPENAI_API_KEY")):
            with self.subTest(provider=provider, missing="key"), \
                    env(ADVISOR_PROVIDER=provider, ADVISOR_MODEL="strong"), temp_log():
                with self.assertRaises(RuntimeError) as e:
                    adv.consult("q", "c")
                self.assertIn(keyvar, str(e.exception))


class TestCliInvocation(unittest.TestCase):
    """Three fixes with no visible marker: session isolation, stdin, error text."""

    def test_child_is_isolated_authenticated_and_reports_real_cause(self):
        parent = {
            "CLAUDE_CODE_ENTRYPOINT": "cli",
            "CLAUDECODE": "1",
            "CLAUDE_CODE_OAUTH_TOKEN": "sk-ant-oat01-secret",
            "PATH": "/usr/bin",
        }
        with env(ADVISOR_PROVIDER="anthropic-cli"), temp_log(), \
                mock.patch.dict(os.environ, parent), \
                mock.patch.object(adv.subprocess, "run",
                                  return_value=completed()) as run:
            adv.consult("q", "c")

        kwargs = run.call_args.kwargs
        child = kwargs["env"]
        # Inherited CLAUDE* markers make `claude -p` behave as a nested session.
        self.assertNotIn("CLAUDE_CODE_ENTRYPOINT", child)
        self.assertNotIn("CLAUDECODE", child)
        # ...except the token, which is the entire auth for this provider.
        self.assertEqual(child["CLAUDE_CODE_OAUTH_TOKEN"], "sk-ant-oat01-secret")
        self.assertEqual(child["PATH"], "/usr/bin")
        # Without DEVNULL the child inherits our live JSON-RPC pipe and stalls.
        self.assertIs(kwargs["stdin"], subprocess.DEVNULL)
        self.assertTrue(kwargs["capture_output"])
        self.assertTrue(kwargs["text"])
        self.assertGreater(kwargs["timeout"], 0)

        # Vendor CLIs print auth failures to stdout, so stderr alone says nothing.
        with env(ADVISOR_PROVIDER="anthropic-cli"), temp_log(), \
                mock.patch.object(adv.subprocess, "run",
                                  return_value=completed(
                                      stdout="Invalid API key / Not logged in",
                                      stderr="", returncode=1)):
            with self.assertRaises(RuntimeError) as e:
                adv.consult("q", "c")
        self.assertIn("Not logged in", str(e.exception))
        self.assertIn("exited 1", str(e.exception))

        # When stderr does carry the cause, it wins over incidental stdout.
        with env(ADVISOR_PROVIDER="anthropic-cli"), temp_log(), \
                mock.patch.object(adv.subprocess, "run",
                                  return_value=completed(
                                      stdout="banner noise",
                                      stderr="model not found", returncode=1)):
            with self.assertRaises(RuntimeError) as e:
                adv.consult("q", "c")
        self.assertIn("model not found", str(e.exception))
        self.assertNotIn("banner noise", str(e.exception))


class TestPromptAndLog(unittest.TestCase):
    """The log is the post-mortem record, and must never fail a good consult."""

    def test_prompt_shape_and_log_durability(self):
        self.assertNotIn("Context:", adv.build_prompt("q", ""))
        full = adv.build_prompt("why a queue?", "options: a, b")
        self.assertLess(full.index(adv.ADVISOR_SYSTEM), full.index("Question:"))
        self.assertLess(full.index("Question:"), full.index("Context:"))
        self.assertIn("why a queue?", full)
        self.assertIn("options: a, b", full)

        reply = "Recommendation: ship it\nReasoning: ...\nRisks: ..."
        with env(ADVISOR_PROVIDER="anthropic-cli", ADVISOR_MODEL="strong"), \
                temp_log() as log, \
                mock.patch.object(adv.subprocess, "run",
                                  return_value=completed(stdout=reply)):
            self.assertEqual(adv.consult("why a queue?", "options: a, b"), reply)

            entry, = log_entries(log)
            # Verbatim on purpose: summaries drop the conditional caveats.
            self.assertEqual(entry["reply"], reply)
            self.assertEqual(entry["question"], "why a queue?")
            self.assertEqual(entry["context"], "options: a, b")
            self.assertEqual(entry["provider"], "anthropic-cli")
            self.assertEqual(entry["model"], "strong")
            self.assertIsNone(entry["error"])
            self.assertIsInstance(entry["elapsed_s"], float)
            self.assertTrue(entry["ts"].endswith("+00:00"))

        # A failed consult is logged and re-raised, not swallowed.
        with env(ADVISOR_PROVIDER="anthropic-cli"), temp_log() as log, \
                mock.patch.object(adv, "_dispatch", side_effect=RuntimeError("timeout")):
            with self.assertRaises(RuntimeError):
                adv.consult("q", "c")
            entry, = log_entries(log)
            self.assertIsNone(entry["reply"])
            self.assertIn("timeout", entry["error"])

        # An unwritable log path degrades quietly; the advice still gets through.
        unwritable = os.path.join(__file__, "nope", "log.jsonl")
        with env(ADVISOR_PROVIDER="anthropic-cli"), \
                mock.patch.object(adv, "LOG_PATH", unwritable), \
                mock.patch.object(adv.subprocess, "run",
                                  return_value=completed(stdout="advice")):
            self.assertEqual(adv.consult("q", "c"), "advice")


class TestVersion(unittest.TestCase):
    """Already drifted once (0.1.0 vs 0.1.2); cheaper to test than to remember."""

    def test_server_version_matches_plugin_manifest(self):
        with open(os.path.join(REPO_ROOT, ".claude-plugin", "plugin.json")) as f:
            manifest = json.load(f)
        reported = adv.handle(
            {"method": "initialize", "params": {}}
        )["serverInfo"]["version"]
        self.assertEqual(reported, manifest["version"])


if __name__ == "__main__":
    unittest.main()
