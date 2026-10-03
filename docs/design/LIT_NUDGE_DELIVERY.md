# Literature: how to deliver diagnosed-problem feedback to an LLM agent (2026-10-03, research agent; tags as given)

Key takeaway: Dream-RSI's negative result concerns abstract, forward-looking direction-setting in open-ended exploration; state-conditioned,
specific, corrective feedback is consistently positive in the literature.

Evidence summary
- Timing: AutoGuide (Fu et al. 2024, arXiv 2403.08978) state-matched guidelines beat ReAct and ExpeL-upfront (ALFWorld 54.5/59.0/79.1;
  WebShop 30/35/46; WebArena-Reddit 8.0/21.8/47.1); same guidelines without context matching 37 vs 46; top-k 0/1/2/3 -> 30/42/46/47.
  JEF Hinter (2510.04373) per-step retrieved hints beat human/document hints. Counterpoint Leins et al. 2026 (2609.24532): adaptive timing did
  not beat fixed schedules; behaviour-specific generated instruction cut decline 87% vs generic reminder 22-27% -> CONTENT > TIMING.
  Budget Tracker (2511.17006): factual budget block after every tool response, +1.3-1.6 pts, -31% cost at small budgets.
- Content: AgentDebug (2509.25370) root-cause-step corrective feedback up to +26% relative; Reflexion (2303.11366) grounded verbal
  diagnosis helps, ungrounded reflection hurt (Rust-hard 0.52 < baseline); Self-Debug (2304.05128). State what to do and why (Anthropic docs);
  error responses specific and actionable with correctly formatted examples (Anthropic writing tools for agents).
- Placement: lost in the middle (Liu et al. 2023); lost in conversation (Laban et al. 2025, 2505.06120); SWE-agent puts feedback in the
  observation right after the action (linter: 18.0 vs 15.0). -> end of the latest observation.
- Form: self-critique without external signal does not help (Huang et al. 2310.01798; Kamoi et al. TACL 2024); external tool-grounded
  feedback does. MINT (2309.10691): NL feedback +2-17%. AgentSpec (2503.18666): trigger/predicate/enforcement; block deterministic violations.
- Dosage/risks: IFScale (2507.11538) adherence decays with number of simultaneous instructions; distraction; sycophancy (false-positive
  nudges cause wrong turns); over-constraint (Dream-RSI); premature completion (Laban).
- Optimizing the nudge text: GEPA (2507.19457), OPRO (2309.03409; small LLMs weak optimizers), TextGrad (2406.07496), ACE (2510.04618, beware
  context collapse); prompt sensitivity up to 76 pts from formatting (Sclar et al. 2310.11324) -> several paraphrases.

Design checklist: (1) ground in observed evidence (quote counts / the offending output); (2) one concrete next action with the exact API
signature or a 2-4 line code skeleton; (3) one "why" clause; (4) at the end of the current observation; (5) <= 1-2 notes per step, ranked;
(6) escalate hint -> specific hint with code -> hard constraint for deterministic violations; (7) cooldown and dedupe; (8) budget as a factual
tracker every step, advice only on waste, never "finish now" without evidence the task is done; (9) hedge low-precision detectors;
(10) local, step-scoped, no global strategy advice; (11) log compliance separately from success; (12) freeze 2-3 paraphrases.
Ablations: content x timing 2x2; placement (observation end / system prompt / critique turn); hint vs constraint vs GEPA-optimized text.
