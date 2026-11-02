# Backlog

Parked items only. Not read at session start; history lives in history.md.

## Parked items (not session-bound)
- Automate the `ADVISOR_MODEL` cache edit so it survives version bumps.
- ~~Clean test of proactive escalation (route 3) in a session that never mentions the
  advisor.~~ Done, session 7: real negative result, see handoff.md and current-task item
  23. Follow-up parked below (hook-based redesign).
- **Hook-based escalation redesign, not started (session 7):** after the proactive
  escalation mandate was proven not to fire (neither for subagents nor the primary
  top-level-session case - see current-task item 23 / handoff.md), the advisor was
  consulted on whether to keep marketing it. Recommendation taken: pull the promise from
  the README, keep the mandate text as a free, unmeasured best-effort in
  `agents/advisor.md`. Its separate recommendation, if the feature is ever wanted for real:
  stop trying to get the model to self-classify "I am about to finalize a hard decision" -
  it can't do that reliably, since it's judging its own not-yet-emitted output against a
  fuzzy bar while competing with its strongest prior (finish the task now). Instead, hook a
  real, observable harness event - a plan-mode-exit hook (highest leverage: that transition
  already *is* the "about to finalize an architectural decision" moment) or a session-end
  hook that runs a dedicated, cheap classifier over the final response with no competing
  incentive to just finish. Risks it flagged: over-triggering annoyance, a real bump in
  onboarding complexity (hooks in `settings.json` vs. today's zero-install MCP+skill
  story - probably an opt-in v0.4-style experiment, not a default), and the subagent path
  needs the mandate composed into each spawned agent's own prompt regardless (ties to
  gotcha 24), which is a plugin-composition change, not a text edit. Verify real Claude
  Code hook event names/payloads before designing against them - not done, this is a shape,
  not a spec.
- **Bigger product direction, floated by the user, not started:** advisor gives code/
  architecture snippets instead of only prose; advisor generates project-specific skills or
  project-level guidelines for how cheap workhorses should operate in a project; subagents
  acting as their own workhorses, all consulting the same advisor as their orchestrator.
  First real test of the last one (session 6): a subagent could reach `consult_advisor`
  fine, but only after explicitly searching for it - not default-visible. Asked the advisor
  itself for the biggest risk of parallel subagent consults: divergent answers are
  invisible and get built into different parts of the codebase before anyone compares
  notes, because the advisor's authority (one caller, one answer, settled) stops working
  once there are N callers. Its recommendation: keep cross-cutting/architectural questions
  at the orchestrator only (ask once, hand the answer down as a constraint); subagents may
  self-consult on decisions fully contained in their own scope, and should bubble up
  anything cross-cutting instead of asking it themselves. If subagent consults are allowed
  anyway, mitigate procedurally (orchestrator reviews every subagent reply together before
  integrating), not by adding server-side state to the advisor - that undoes the stateless
  design and still can't reconcile conflicting answers.
  **Session 7 root-cause finding:** a fresh general-purpose subagent, given a genuinely
  hard-to-reverse architecture question with no mention of "advisor"/"consult" anywhere,
  made zero tool calls and never escalated (confirmed by an empty consult log, not just a
  self-report). A direct introspection probe explained why: the escalation mandate lives
  only in the `advisor` agent's own frontmatter description, part of the "available agent
  types" system-reminder shown to whoever might spawn it - and a spawned subagent never
  sees that listing at all. It sees the bare `consult_advisor` tool *name* in its
  deferred-tools list and nothing else - no hint of what it's for or when to reach for it.
  So the gap isn't "subagents lack a channel to talk to the advisor" (the channel already
  works once discovered); it's that the escalation *criteria* never reach the subagent's
  context, and nothing prompts it to self-initiate a `ToolSearch` for a bare, undescribed
  tool name. The cheap fix in principle - whoever spawns a subagent hands it the escalation
  rule explicitly in its own task prompt - reintroduces the divergent-answers risk above if
  done carelessly. User's call (2026-09-07): table the whole idea until after v1.0 ships,
  likely a v1.5/2.0 feature.

