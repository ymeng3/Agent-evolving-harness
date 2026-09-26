# COMPONENT-CREDIT BREADTH DIAGNOSTIC — DRAFT v0, 2026-09-24. Not frozen; awaiting user review of scope/GPU.
QUESTION: does trajectory-local evidence (local CF at budget B; later a value proxy) have cross-component predictive
validity for persistent-component credit, measured against a CI-graded global paired LOO ruler?
RULER (frozen): gamma_i^global from paired persistent LOO (same seeds/slots, exact prefix reuse where applicable);
  class = harmful if UCB95 < -2pp, helpful if LCB95 > +2pp, else neutral/uncertain. Target: every benchmark pair at
  >= 192 paired episodes (2 seeds x 96) and >= 288 for |point gamma| in [2, 8]pp (the ambiguous band).
INVENTORY (Step 0, $0, hag/credit_benchmark_inventory.txt): 35 pairs with a global paired LOO today (families: HISTORY 11,
  retry 8, memory 7, fallback 3, format_prompt 3, parse 2, TEMPERATURE 1); at delta=2 only 1 harmful / 2 helpful / 32
  uncertain because 24 pairs are single-seed n=96. Plus 8 single-unit archival candidates vs F0 (N01 parser, N03 retry,
  N04 history, N05, N07, E1_T, E1_HT, E1_HR) with 268-402 paired episodes = firm ruler for free, but no step logs.
STRATIFICATION (frozen): families >= 5 pairs each for retry/fallback/memory/HISTORY/format/parse, >= 2 for TEMPERATURE;
  classes: target >= 6 harmful, >= 8 helpful, rest neutral; lineages: P1b, Loop-1, Loop-2, host, MECH07, archival N/E1.
  Evaluation grouped by candidate (leave-one-candidate-out; bootstrap over candidates, never over components).
GPU STEP 1 (ruler firming): add seed 2 (and seed 3 where the point gamma is in the ambiguous band) for the ~14 pairs with
  |point gamma| >= 4 and single seed; ~28-40 passes. Also step-logged C re-runs for candidates lacking logs (~14 passes)
  so activation states exist for Step 2.
GPU STEP 2 (local CF ladder): B in {8,16,32} activation states x ON/OFF x 2 replicates, prefix replayed; ~20 components;
  equal-cost reporting (LLM calls, % of full LOO). Metrics: Spearman vs ruler; 3-class accuracy; false-keep (harmful kept)
  and false-drop (helpful dropped) rates; regret L = FK + FD; cost to reach a target decision reliability. Baselines:
  activation-rate-only and random-sign.
STEP 3 (value proxy, only if Step 2 shows ranking signal): delta-V proxy from paired trajectories; no training first.
KILL/CONTINUE (frozen): local CF not better than the activation-rate baseline in leave-one-candidate-out -> not a credit
  estimator; ranking signal but decision accuracy only at high B -> cheap screening only; regret reduced at low/mid B ->
  develop adaptive allocation. Estimated compute: Step 1 ~12-15 GPU-h, Step 2 ~10-12 GPU-h on one A800.
