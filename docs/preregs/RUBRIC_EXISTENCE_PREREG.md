# BEHAVIOURAL-SIGNATURE EXISTENCE TEST (offline, $0) — FROZEN 2026-09-20 BEFORE ANY NUMBER
Purpose: cheapest falsifier for the "diagnostic probes / vector-valued credit" idea. Question: do known interventions
have DISTINGUISHABLE behavioural signatures that scalar success hides? If H and R are not separable here, the idea dies
without spending environment compute. This is NOT a rubric judge: stored trajectories hold only (action, valid,
admissible) per step, so every dimension below is computed, not scored by an LLM. LLM-judged dimensions (understanding,
planning) would need an observation-logging re-run and are a separate, later decision.
DATA: API-era 134-pool, 3 seeds each: F0, N04 (H = HISTORY_LENGTH 10), N03 (R = retry w/ reasoning), E1_HR (H+R),
G_MECH07 (negative compound). Local-v2 sanity: LQ_F0/LQ_HR/LQ_MECH07 (96 games).
DIMENSIONS (per pass, then seed-mean; deltas vs F0 in pp or ratio):
  succ      success rate
  invalid   invalid-action rate over steps
  recover   P(valid at t+1 | invalid at t)            [recovery]
  loop      fraction of episodes with a 3-repeat action  [state tracking / stuck]
  breadth   distinct "go to <X>" targets per episode / steps taken  [exploration vs dithering]
  steps_win mean steps among successful episodes       [efficiency]
  maxed     fraction hitting 50 steps
PREDICTIONS (frozen): H: loop DOWN, breadth UP, recover ~0.   R: recover UP, invalid DOWN, loop ~0.
  H+R: both.  MECH07: loop UP and/or maxed UP with recover ~0 (a planning-level failure, not a recovery failure).
KILL: H and R share the same dominant delta dimension, or their signature vectors differ by less than the F0 seed-to-seed
  spread on every dimension  -> idea killed at $0.  PROMOTE: distinct dominant dimensions as predicted -> design the
  on-demand probe version (LLM proposes probe, environment executes, Credit rule decides), never a fixed judge rubric.
