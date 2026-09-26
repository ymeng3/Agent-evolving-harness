# LOCAL BACKEND QUALIFICATION — FROZEN 2026-09-19 BEFORE ANY LOCAL PASS. 2-DAY CAP.
Purpose: replace the OpenRouter/Alibaba endpoint with a self-hosted instance of the SAME checkpoint
(Qwen3-30B-A3B-Instruct-2507, bf16, 2xA40 tensor-parallel, NO quantisation) so the closed loop and its
follow-ups iterate at ~$0 API. This is an equivalence test of a serving stack, NOT a model selection.
NOT tested: 7B, 14B, 32B, other families. Scope expansion is refused.
SET (9 passes, 96-game validation slice, seeds 1/2/3, all patches already exist):
  F0 (empty patch) | ARM HR = E1_HR_hist10_retry_basetemp | G_MECH07_plan_sub_goal_completion
ACCEPTANCE (all three, fixed now; API reference values on this slice):
  A1 |F0_local - 0.3229| <= 0.05         (0.3229 = API F0VAL96 3-seed mean on the same 96 games)
  A2 (H+R)_local - F0_local >= +8 pp     (API archive: +15.92 on the 134 pool)
  A3 G_MECH07_local - F0_local <= -5 pp  (API archive: -9.95 on the 134 pool)
  plus deterministic HARD checks: served model id == "qwen/qwen3-30b-a3b-instruct-2507"; dtype bf16;
  tensor-parallel 2; no quantisation flag; harness default base_url unchanged when BOS_BASE_URL unset.
PASS -> register "local bf16 Qwen3-30B-A3B" as a new comparability boundary; redo the 5 pre-loop passes
locally (free); run the frozen v2.1 loop locally (gpt-4o proposer only, ~$2). FAIL or not stable within
2 days -> launch the API loop as already qualified (replication PASS on 2026-09-17). No mixing of
backends inside one experiment, ever.
