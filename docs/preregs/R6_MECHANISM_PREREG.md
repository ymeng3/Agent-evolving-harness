# r6 MECHANISM + GLOBAL-LOO COST — OVERNIGHT 2026-09-23. FROZEN BEFORE THE GPU RUNS.
CODE FACT (A1, read from source): r6's choose_fallback WRITES NO STATE. memory_update writes state['action_history'] every
step; choose_fallback reads it and returns 'look' (if the last action was not 'look') or an earlier admissible action.
retry_policy reads nothing. So "harm via fallback state writes" is ruled out at the code level.
LOG FACTS (A2, $0): in C, fallback fires ~12x per episode; episodes with 0 fires win 100% (n=19), 13+ fires win 0% (n=34)
(confounded by difficulty, not causal). C vs C\fallback (192 pairs): win 39.6 vs 46.4; 'look' actions 6.4 vs 0.1 per
episode; inadmissible actions sent to the env 0.0 vs 8.5 per episode. C\memory (= look-only fallback) 38.5% with 3.2
three-repeats/episode. First action divergence between C and C\fallback is at step ~3 (LLM sampling), so alignment-based
divergence analysis is uninformative; outcome discordance 15/96 (12 favour C\fallback).
HYPOTHESIS H_r6 (frozen): substituting 'look' (or a repeated old action) for the model's inadmissible action REMOVES the
"Nothing happens" failure signal and pollutes history with 'look'/repeats, so the model does not correct; harm accumulates
with the number of activations. Local one-shot effect ~0 (Probe L +12.5 +/- 14.7 is noise).
VARIANTS (96 games, seed 1, paired by slot with C and C\fallback seed 1):
  V1 one-shot fallback (fires once per episode, then off)    PREDICTION: Q(V1) - Q(C\fb) in [-3, +3] (harm scales with activations)
  V2 history-alternative only (never 'look')                 PREDICTION: Q(V2) <= Q(C\fb) (repeats cause loops; MECH07 signature)
  V3 no fallback + no memory (OFF/OFF factorial cell)        PREDICTION: Q(V3) - Q(C\fb) in [-3, +3] (memory only feeds the fallback)
  Existing cells: ON/ON = C (38.5 s1), OFF/ON = C\fb (44.8 s1... see files), ON/OFF = C\memory (38.5 s1).
  KILL for H_r6: V1 as harmful as C (Q(V1) <= Q(C) + 2) -> harm is not activation-count driven.
REPLAY EQUIVALENCE (A4): replay the FULL logged action sequences of 8 PV_r6_C games under C with BOS_REPLAY (zero LLM calls);
  PASS iff every replayed step's observation snippet equals the logged one and outcomes match 8/8.
COST AUDITS ($0, tonight): A3 paired-vs-independent variance ratio and discordance direction per seed; A5 offline
  decision-aware allocation simulation (sequential rule, conservative threshold, reported with its multiple-look caveat);
  shared-control check (C measured once per candidate: yes by cache). P2 AgentPRM coverage: distinct observation snippets
  and revisit rates (feasibility only).
AFTER ALL RESULTS ARE WRITTEN: the AutoDL instance is shut down automatically.
