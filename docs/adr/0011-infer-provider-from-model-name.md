---
status: accepted
date: 2026-09-05
---
# Detect the provider from the model name or base URL; explicit `ADVISOR_PROVIDER` wins

## Context and Problem Statement
Users had to set both a provider and a model (inferred from 9141c00, "simplified install/setup"). The model name almost always implies the provider, so asking for both adds a setup step and a way to get them out of sync.

## Considered Options
* User must set the provider (previous behavior)
* Infer the provider from the model name or base URL, with an explicit `ADVISOR_PROVIDER` overriding

## Decision Outcome
Chosen option: "Infer, explicit wins", because install then needs only a model. A base URL means `openai-compatible`; `gemini-*` means `gemini-cli`; `gpt-*`, `o1-`/`o3-`/`o4-`, and `chatgpt-*` mean `openai-api`; anything else, including `cli-default`, means `anthropic-cli` (`server/advisor_server.py:69-80`).

### Consequences
* Good, because the Quickstart is one `--config advisor_model=...` flag (README.md:24, README.md:46-48).
* Bad, because a model name that does not match a prefix falls through to `anthropic-cli`, so non-Claude models outside these prefixes need `ADVISOR_PROVIDER` set (inferred from `server/advisor_server.py:80`).

## More Information
Evidence: 9141c00, 752816c (tests); `server/advisor_server.py:69-80`. Related: [ADR-0005](0005-base-url-makes-api-key-optional.md), [ADR-0009](0009-provenance-in-consult-log-not-reply-header.md) (`provider_source` records whether inference or the explicit setting won).
