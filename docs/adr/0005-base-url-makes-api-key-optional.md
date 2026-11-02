---
status: accepted
date: 2026-08-15
---
# `openai-compatible` provider: `ADVISOR_BASE_URL` makes the API key optional

## Context and Problem Statement
The `openai-compatible` provider points the OpenAI request format at a user-supplied base URL, typically a local server such as ollama, LM Studio, or vLLM (dcb0936, 6ec855f). Those servers want no key, and sending an empty `Authorization` header breaks some of them (CLAUDE.md gotcha 6).

## Considered Options
* Always require an API key
* Make the key optional when `ADVISOR_BASE_URL` is set, and send no auth header without one

## Decision Outcome
Chosen option: "Key optional when `ADVISOR_BASE_URL` is set", because local servers need no key and an empty auth header breaks some of them (dcb0936 `api_key()`; CLAUDE.md gotcha 6).

### Consequences
* Good, because local models work with no key setup.
* Bad, because a missing key against a hosted endpoint behind a base URL fails at the remote end, not with a local error (inferred from dcb0936 `api_key()`).

## More Information
Evidence: dcb0936, 6ec855f; CLAUDE.md gotcha 6. A base URL also selects this provider automatically: [ADR-0011](0011-infer-provider-from-model-name.md).
