# VERIFIER LINE ON SCIWORLD — FROZEN 2026-09-24 17:30 CDT BEFORE THE PASSES RUN.
Why SciWorld: its verifier scores subgoals DURING the episode (score rises when a graded step is completed), so a
component's effect can be seen mid-trajectory, which ALFWorld never allowed. Same hook API; harness bos_sciworld.py
(prompt = SEED's SciWorld template; off-task 'focus on' is guarded at harness level for every config).
RUNS (seed 1, 48 episodes = 12 tasks x 4 variations, 40-step cap, easy simplification, local A800, $0 API):
  SW_F0 (no patch) | SW_retry (2-attempt corrective retry) | SW_fb (fallback 'look around') | SW_hist10 (HISTORY_LENGTH=10)
GROUND TRUTH per component = paired LOO vs F0 on (a) success and (b) mean final score (episode-paired; score is the
finer ruler here).
VERIFIER SIGNAL (frozen): for trigger components (retry, fallback): V = mean score gain in the 3 steps after an
activation, minus the episode's baseline per-step score gain (same episode, non-activation steps). For history10:
paired score-timing profile T = (fraction of episodes reaching score>0 ON - OFF) + (mean step of first score gain, OFF - ON,
scaled by 1/40).
PREDICTIONS: sign(V) == sign(paired LOO on mean score) for retry AND for fallback; sign(T) == sign(LOO) for history10 is
expected, not required. KILL: V disagrees with the LOO sign for both retry and fallback -> mid-episode verifier evidence does
not track component credit even where the verifier is intermediate; verifier line closes for good.
Also reported: activation counts, invalid-output rate per config, and the F0 invalid-output rate (smoke: 67-80%).
