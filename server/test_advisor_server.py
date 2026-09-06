#!/usr/bin/env python3
"""Tests for the advisor MCP server.

Stdlib only, to match the server's no-install promise:

    python3 -m unittest discover -s server -p 'test_*.py' -v

Nine tests, one per concern. Nothing here touches the network, a vendor CLI,
or the real consult log.
"""

import io
import json
import os
import re
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
    "ADVISOR_BASE_URL",
    "ADVISOR_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
)


@contextmanager
def env(**overrides):
    """Run with a known-clean advisor env; unnamed vars are unset.

    ADVISOR_MODEL defaults to a stub because consult() now refuses to run
    without one - tests that care about that pass ADVISOR_MODEL="" instead.
    shutil.which is neutralised so tests see bare command names, not paths.
    """
    with mock.patch.dict(os.environ), \
            mock.patch.object(adv.shutil, "which", return_value=None):
        for key in ADVISOR_VARS:
            os.environ.pop(key, None)
        os.environ["ADVISOR_MODEL"] = "test-model"
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
        self.assertTrue(ok["content"][0]["text"].endswith("\n\nadvice"))
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
            # 'cli-default' is the only way to omit the flag, and it is opt-in.
            ("anthropic-cli", adv.CLI_DEFAULT, ["claude", "-p", prompt]),
            ("anthropic-cli", "big", ["claude", "-p", prompt, "--model", "big"]),
            ("gemini-cli", adv.CLI_DEFAULT, ["gemini", "-p", prompt]),
            # Note the flag order flip: -m comes before -p here, not after.
            ("gemini-cli", "gem", ["gemini", "-m", "gem", "-p", prompt]),
        ]
        for provider, model, expected in cli_cases:
            with self.subTest(provider=provider, model=model):
                overrides = {"ADVISOR_PROVIDER": provider,
                             "ADVISOR_MODEL": model}
                with env(**overrides), temp_log(), \
                        mock.patch.object(adv.subprocess, "run",
                                          return_value=completed()) as run:
                    self.assertTrue(adv.consult("q", "c").endswith("\n\nadvice"))
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
                    self.assertTrue(adv.consult("q", "c").endswith("\n\nadvice"))

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
        with env(ADVISOR_PROVIDER="openai-compatible", ADVISOR_MODEL="m"), temp_log():
            with self.assertRaises(RuntimeError) as e:
                adv.consult("q", "c")
            self.assertIn("ADVISOR_BASE_URL", str(e.exception))

        with env(ADVISOR_PROVIDER="claude-4-opus"), temp_log():
            with self.assertRaises(RuntimeError) as e:
                adv.consult("q", "c")
            self.assertIn("anthropic-cli", str(e.exception))

        for provider in ("anthropic-api", "openai-api"):
            with self.subTest(provider=provider, missing="model"), \
                    env(ADVISOR_PROVIDER=provider,
                        ADVISOR_MODEL=adv.CLI_DEFAULT), temp_log():
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


class TestModelIsRequired(unittest.TestCase):
    """An unset model used to inherit the workhorse's own model, making the
    advisor the same model twice while the log still read as healthy."""

    def test_unset_model_is_refused_and_cli_default_is_opt_in(self):
        # Every provider refuses, and the error names the fix.
        for provider in ("anthropic-cli", "gemini-cli", "openai-compatible"):
            with self.subTest(provider=provider), \
                    env(ADVISOR_PROVIDER=provider, ADVISOR_MODEL=""), \
                    temp_log() as log, \
                    mock.patch.object(adv.subprocess, "run") as run:
                with self.assertRaises(RuntimeError) as e:
                    adv.consult("q", "c")
                self.assertIn("ADVISOR_MODEL", str(e.exception))
                self.assertIn(adv.CLI_DEFAULT, str(e.exception))
                # No vendor call was made, and the refusal is on the record.
                run.assert_not_called()
                self.assertEqual(len(log_entries(log)), 0)

        # Asking for it explicitly still works, and omits the flag.
        with env(ADVISOR_PROVIDER="anthropic-cli",
                 ADVISOR_MODEL=adv.CLI_DEFAULT), temp_log() as log, \
                mock.patch.object(adv.subprocess, "run",
                                  return_value=completed()) as run:
            self.assertTrue(adv.consult("q", "c").endswith("\n\nadvice"))
            entries = log_entries(log)  # read before the temp dir goes away
        self.assertNotIn("--model", run.call_args.args[0])
        # Logged as the sentinel, never as null - null is what hid this bug.
        self.assertEqual(entries[0]["model"], adv.CLI_DEFAULT)


class TestAttributionHeader(unittest.TestCase):
    """Every reply says which model answered. A consult that silently ran the
    wrong model used to look identical to a correct one."""

    def test_header_names_both_models_and_log_stays_clean(self):
        with env(ADVISOR_PROVIDER="anthropic-cli", ADVISOR_MODEL="big"), \
                temp_log() as log, \
                mock.patch.object(adv.subprocess, "run",
                                  return_value=completed()) as run:
            out = adv.consult("q", "c", "haiku-workhorse")
            entries = log_entries(log)

        first, second, blank, body = out.split("\n", 3)
        self.assertIn("big", first)
        self.assertIn("anthropic-cli", first)
        self.assertIn("haiku-workhorse", second)
        self.assertEqual(body, "advice")
        # The header is presentation only - the log keeps the raw reply, and
        # the advisor is never asked to produce it.
        self.assertEqual(entries[0]["reply"], "advice")
        self.assertNotIn("Workhorse", run.call_args.args[0][-1])

        # An unreported workhorse says so rather than inventing one.
        with env(ADVISOR_PROVIDER="anthropic-cli", ADVISOR_MODEL="big"), \
                temp_log(), \
                mock.patch.object(adv.subprocess, "run",
                                  return_value=completed()):
            self.assertIn("Workhorse = not reported", adv.consult("q", "c"))


class TestProviderInference(unittest.TestCase):
    """Provider is auto-detected from the model name when not set explicitly."""

    def test_inference_from_model_prefix_and_base_url(self):
        cases = [
            ("claude-opus-5", "", "anthropic-cli"),
            ("claude-fable-5-1", "", "anthropic-cli"),
            ("opus", "", "anthropic-cli"),
            ("gemini-3.1-pro-preview", "", "gemini-cli"),
            ("gemini_2.5-flash", "", "gemini-cli"),
            ("gpt-5.6", "", "openai-api"),
            ("o3-mini", "", "openai-api"),
            ("o4-mini", "", "openai-api"),
            ("chatgpt-4o-latest", "", "openai-api"),
            (adv.CLI_DEFAULT, "", "anthropic-cli"),
            ("unknown-model", "", "anthropic-cli"),
            # A base URL is the strongest signal: always openai-compatible.
            ("gemma3:latest", "http://localhost:11434/v1", "openai-compatible"),
            ("claude-opus-5", "http://proxy.internal/v1", "openai-compatible"),
        ]
        for model, base_url, expected in cases:
            with self.subTest(model=model, base_url=base_url):
                self.assertEqual(adv.infer_provider(model, base_url), expected)

    def test_explicit_provider_overrides_inference(self):
        # A Gemini model with an explicit anthropic-cli provider: the explicit
        # value wins, even though inference would say gemini-cli.
        with env(ADVISOR_PROVIDER="anthropic-cli",
                 ADVISOR_MODEL="gemini-3.1-pro"), temp_log(), \
                mock.patch.object(adv.subprocess, "run",
                                  return_value=completed()) as run:
            adv.consult("q", "c")
        self.assertEqual(run.call_args.args[0][0], "claude")

    def test_blank_provider_triggers_inference(self):
        with env(ADVISOR_PROVIDER="", ADVISOR_MODEL="gpt-5.6",
                 OPENAI_API_KEY="k"), temp_log(), \
                mock.patch.object(adv.urllib.request, "urlopen") as urlopen:
            body = {"choices": [{"message": {"content": "advice"}}]}
            urlopen.return_value = FakeResponse(json.dumps(body))
            result = adv.consult("q", "c")
        self.assertTrue(result.endswith("\n\nadvice"))
        self.assertIn("openai-api", result.split("\n")[0])


class TestUserConfigSubstitution(unittest.TestCase):
    """An unset userConfig option arrives as "" in env, not absent (verified
    against Claude Code 2.1.222). Empty must therefore mean unset everywhere."""

    def test_blank_values_fall_back_and_never_shadow_the_shell(self):
        # A blank provider is the default, not an unknown provider.
        with env(ADVISOR_PROVIDER="", ADVISOR_MODEL="m"), temp_log(), \
                mock.patch.object(adv.subprocess, "run") as run:
            run.return_value = completed()
            adv.consult("q", "c")
        self.assertEqual(run.call_args.args[0][0], "claude")

        body = json.dumps({"choices": [{"message": {"content": "advice"}}]})

        # A blank ADVISOR_API_KEY must not shadow the shell's vendor key.
        with env(ADVISOR_PROVIDER="openai-api", ADVISOR_MODEL="m",
                 ADVISOR_API_KEY="", ADVISOR_BASE_URL="",
                 OPENAI_API_KEY="from-shell"), temp_log(), \
                mock.patch.object(adv.urllib.request, "urlopen") as urlopen:
            urlopen.return_value = FakeResponse(body)
            adv.consult("q", "c")
        sent = {k.lower(): v for k, v in urlopen.call_args.args[0].headers.items()}
        self.assertEqual(sent["authorization"], "Bearer from-shell")

        # Set in the GUI, it wins - that is the whole point of the option.
        with env(ADVISOR_PROVIDER="openai-api", ADVISOR_MODEL="m",
                 ADVISOR_API_KEY="from-gui", OPENAI_API_KEY="from-shell"), \
                temp_log(), \
                mock.patch.object(adv.urllib.request, "urlopen") as urlopen:
            urlopen.return_value = FakeResponse(body)
            adv.consult("q", "c")
        sent = {k.lower(): v for k, v in urlopen.call_args.args[0].headers.items()}
        self.assertEqual(sent["authorization"], "Bearer from-gui")

    def test_manifest_options_and_mcp_config_agree(self):
        """Every declared option is wired up, and nothing references an option
        that no longer exists. `command` counts too, not just `env`."""
        with open(os.path.join(REPO_ROOT, ".claude-plugin", "plugin.json")) as f:
            declared = set(json.load(f)["userConfig"])
        with open(os.path.join(REPO_ROOT, ".mcp.json")) as f:
            server = json.load(f)["mcpServers"]["advisor"]
        blob = json.dumps(server)
        referenced = set(re.findall(r"\$\{user_config\.([^}]+)\}", blob))
        self.assertEqual(declared, referenced)


class TestByoEndpoint(unittest.TestCase):
    """Any OpenAI-compatible host, local included, with no vendor key."""

    def test_base_url_redirects_and_makes_the_key_optional(self):
        ollama = "http://localhost:11434/v1"
        body = json.dumps({"choices": [{"message": {"content": "advice"}}]})

        # A local server needs no key, and must not be sent an empty one.
        for provider in ("openai-compatible", "openai-api"):
            with self.subTest(provider=provider), \
                    env(ADVISOR_PROVIDER=provider, ADVISOR_MODEL="gemma3:latest",
                        ADVISOR_BASE_URL=ollama), temp_log(), \
                    mock.patch.object(adv.urllib.request, "urlopen") as urlopen:
                urlopen.return_value = FakeResponse(body)
                self.assertTrue(adv.consult("q", "c").endswith("\n\nadvice"))

            req = urlopen.call_args.args[0]
            self.assertEqual(req.full_url, ollama + "/chat/completions")
            sent = {k.lower() for k in req.headers}
            self.assertNotIn("authorization", sent)

        # A trailing slash must not produce a doubled one.
        with env(ADVISOR_PROVIDER="openai-compatible", ADVISOR_MODEL="m",
                 ADVISOR_BASE_URL=ollama + "/"), temp_log(), \
                mock.patch.object(adv.urllib.request, "urlopen") as urlopen:
            urlopen.return_value = FakeResponse(body)
            adv.consult("q", "c")
        self.assertEqual(urlopen.call_args.args[0].full_url,
                         ollama + "/chat/completions")

        # A key is still sent when one is supplied (gateways like OpenRouter).
        with env(ADVISOR_PROVIDER="openai-compatible", ADVISOR_MODEL="m",
                 ADVISOR_BASE_URL="https://openrouter.ai/api/v1",
                 OPENAI_API_KEY="k"), temp_log(), \
                mock.patch.object(adv.urllib.request, "urlopen") as urlopen:
            urlopen.return_value = FakeResponse(body)
            adv.consult("q", "c")
        sent = {k.lower(): v for k, v in urlopen.call_args.args[0].headers.items()}
        self.assertEqual(sent["authorization"], "Bearer k")

        # The Anthropic path redirects too, for proxies and gateways.
        with env(ADVISOR_PROVIDER="anthropic-api", ADVISOR_MODEL="m",
                 ADVISOR_BASE_URL="https://proxy.internal/v1"), temp_log(), \
                mock.patch.object(adv.urllib.request, "urlopen") as urlopen:
            urlopen.return_value = FakeResponse(
                json.dumps({"content": [{"type": "text", "text": "advice"}]}))
            self.assertTrue(adv.consult("q", "c").endswith("\n\nadvice"))
        self.assertEqual(urlopen.call_args.args[0].full_url,
                         "https://proxy.internal/v1/messages")


class TestStandaloneCli(unittest.TestCase):
    """Entry point for workhorses that speak no MCP at all."""

    def test_one_shot_consult_prints_reply_and_reports_failure(self):
        with env(ADVISOR_PROVIDER="anthropic-cli"), temp_log(), \
                mock.patch.object(adv, "_dispatch", return_value="advice"), \
                mock.patch.object(sys, "stdout", io.StringIO()) as out:
            code = adv.ask_once(["why a queue?", "options: a, b"])
        self.assertEqual(code, 0)
        self.assertTrue(out.getvalue().endswith("\n\nadvice\n"))

        # Context is optional.
        with env(ADVISOR_PROVIDER="anthropic-cli"), temp_log(), \
                mock.patch.object(adv, "_dispatch", return_value="advice") as d, \
                mock.patch.object(sys, "stdout", io.StringIO()):
            adv.ask_once(["just the question"])
        self.assertIn("just the question", d.call_args.args[2])
        self.assertNotIn("Context:", d.call_args.args[2])

        # Failure goes to stderr with a non-zero exit, so callers can branch.
        with env(ADVISOR_PROVIDER="anthropic-cli"), temp_log(), \
                mock.patch.object(adv, "_dispatch",
                                  side_effect=RuntimeError("no auth")), \
                mock.patch.object(sys, "stdout", io.StringIO()) as out, \
                mock.patch.object(sys, "stderr", io.StringIO()) as err:
            code = adv.ask_once(["q"])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("no auth", err.getvalue())


class TestCliInvocation(unittest.TestCase):
    """Three fixes with no visible marker: session isolation, stdin, error text."""

    def test_child_is_isolated_authenticated_and_reports_real_cause(self):
        parent = {
            "CLAUDE_CODE_ENTRYPOINT": "cli",
            "CLAUDECODE": "1",
            "CLAUDE_CODE_OAUTH_TOKEN": "fake-token-not-a-real-key",
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
        self.assertEqual(child["CLAUDE_CODE_OAUTH_TOKEN"], "fake-token-not-a-real-key")
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
            self.assertTrue(
            adv.consult("why a queue?", "options: a, b").endswith("\n\n" + reply))

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
            self.assertTrue(adv.consult("q", "c").endswith("\n\nadvice"))


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
