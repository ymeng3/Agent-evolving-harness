# CC-BOOST — gradient-boosted self-evolving rubric, and rubric-guided harness evolution. FROZEN 2026-10-02 BEFORE ANY NUMBER.

Owner: kainingshi (branch cc/dev; tags CC_*). Written before any of the runs below exist. Amendments go at the bottom, dated,
written BEFORE the runs they govern. Proposer for everything = the executor itself (Qwen3.8-27B on the shared A800), so the
"self" claim does not rest on a stronger teacher; no gpt-4o / Opus in any arm.

## 0. Regime decision (thinking ON vs OFF for the executor)
Data: CC_T0_F0_disc seeds 1,2 (thinking OFF; parse fix ON; timeout 900) vs CC_F0_fix seed 1 (thinking ON, same otherwise; 26/50).
Rule: choose thinking OFF iff mean success(T0 disc s1,s2) >= 26/50 - 4 = 22/50 (i.e. within 8pp); otherwise thinking ON.
Reason: OFF is expected to be several times faster per pass; within 8pp the extra passes buy more power than the base rate costs.
The chosen regime is used for every later executor run. Report wall time per pass for both.

## 1. Stage 1 — rubric as gradient boosting (offline; proposer calls only, no executor rollouts)
Object. A rubric dimension is an executable detector `detect(steps) -> float` over the first L = 15 cells of a trajectory
(fields per cell: index, code, output tail (<=200 chars), error flag, reply tail (<=600 chars)). Goal-check fields (gp, gf, G,
harm_fail) and anything after cell L are NEVER visible (no leakage). Landmark set = trajectories that have not called
complete_task within the first L cells and have > L cells (the "still running at L" set), so length cannot leak the outcome.
Model. Ridge-logistic additive model F(x) = b + sum_k w_k z_k(x) for won, z_k = standardised detector k (lambda = 1).
Boosting round. Fit F on the discovery landmark set (seeds pooled, folds grouped by task); out-of-fold p_i; pseudo-residual
r_i = y_i - p_i (= negative gradient of log-loss in F). The proposer gets the current rubric and EXAMPLES, writes P = 3 candidate
detectors; each must compile under the patch sandbox rules, run without error on >= 95% of trajectories, and not be constant.
Admission (the "weak learner" step): add the candidate with the largest grouped-CV log-loss improvement (5 repeats x 5 folds)
if that improvement is >= 0.005 nats; otherwise the round admits nothing.
Arms (same proposer, same prompt template, same number of example cells):
  BOOST      examples = the 4 most negative residuals (unexplained failures) + 2 most positive (unexplained successes)
  UNTARGET   examples = 4 random failures + 2 random successes (seeded) — ablates residual targeting, the XGBoost part
  FIXED      6 hand-written generic detectors (error rate, longest error streak, api_docs share, repeated identical cell,
             distinct apps touched, empty/None outputs) — no proposer, no evolution
Rounds R = 6 for BOOST and UNTARGET.
Held-out read-out: model fit on all discovery landmark trajectories, scored on the VALIDATION landmark set (new task families,
F0 runs CC_*_F0_val seeds 1,2): log-loss, AUC, Brier, per round. CIs by task-cluster bootstrap (2000).
Primary Stage-1 endpoint: validation log-loss after round 6, BOOST vs UNTARGET (paired bootstrap over validation tasks).
Signal := BOOST better with the 90% CI of the difference excluding 0. Secondary: BOOST vs FIXED; admitted-dimension counts.

## 2. Stage 2 — rubric-guided harness evolution (executor rollouts on Validation)
Edit generation (proposer = Qwen3.8-27B, thinking ON, v3 two-layer patch format, 1-3 edits, minimal repair):
  G_BOOST    guidance = one of the top-3 BOOST dimensions by failure mass (sum over discovery landmark failures of -w_k z_k,
             positive part), given as its detector code + the proposer's own one-line description + 3 firing failure windows;
             the edit must trigger on that mechanism online.
  G_RAW      guidance = 3 raw failure windows chosen at random (same window format/length), "find a mechanism and repair it".
  G_GENERIC  guidance = generic rubric text (tool-call accuracy, avoid loops, explore alternative approaches) + 3 random failure
             windows — the Dream-RSI-style "directional guidance" control.
3 edits per arm. Each edit must load (load_v3) and fire on >= 3 discovery tasks in the offline dry-run, else regenerate (<= 3 tries).
Evaluation: each edit = one pass on tasks_challenge_val50, seed 1, chosen regime; paired with CC_*_F0_val seed 1; F0 seed 2 gives
the seed-noise reference. Primary Stage-2 endpoint: arm-mean paired success difference vs F0 (150 paired task outcomes per arm),
G_BOOST vs G_RAW and vs G_GENERIC, paired sign-flip randomisation test. Secondary: G sign test; localized effect on the tasks where
the targeted detector fired in F0 (G_BOOST only); manipulation check (detector firing rate drops in the edited runs).
Power is low (MDE ~10pp per arm contrast); results are a pilot and are reported with CIs, not as confirmation.

## 3. Iteration rule (user authorised iterating until a signal appears)
If an endpoint shows no signal, the next iteration may change ONE thing at a time — landmark L, proposer context, admission
threshold, number of rounds, edit format — each written here as a dated amendment before it runs, with the reason. The
validation set is reused across iterations; the sealed test set is never touched. Every iteration is reported, including null ones.

## Amendments
(none yet)
