---
name: advisor
description: Ask the advisor a direct question on the user's behalf. Use
  when the user says "/advisor ...", "ask the advisor ...", or "what does
  the advisor think about ...". Unlike proactive consults, there is no
  escalation bar - any question the user wants a second opinion on
  qualifies.
---

# Ask the advisor directly

1. Take the user's question as the consult question, verbatim where
   possible. The advisor is stateless: if the conversation holds context it
   needs (the idea under discussion, constraints, repo-relative file
   paths), package that briefly alongside the question.
2. Route like any consult: the consult_advisor MCP tool when available,
   the advisor subagent otherwise.
3. Relay the advisor's reply to the user in full — do not compress it.
   Add your own take afterward only where it differs, clearly labeled.
