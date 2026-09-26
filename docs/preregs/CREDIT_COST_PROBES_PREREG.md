# EVOLUTIONARY CREDIT — COST AUDIT + CHEAP-SIGNAL PROBES. v0 2026-09-23 (audits C/D computed; probes frozen before data).
Q1 Where is full component LOO wasteful?   Q2 Which cheaper trajectory structure predicts global component credit?
GROUND TRUTH throughout: gamma_i^global = Q(C) - Q(C\e_i) from existing paired LOO passes (P1b r4/r6 2 seeds, P1b naive
r3/r5, MECH07 lattice 3 seeds, host ctrl21 lattice, Loop-1 and Loop-2 finalist probes).
AUDIT C (sequential stopping headroom) — DONE 2026-09-23, $0: earliest n at which the full-budget decision (delta=3pp/90%)
  is already reached in >=90% of shuffles: UNCERTAIN contrasts stabilise at 8-32 episodes (7/9); KEEP/DROP contrasts need
  most of the budget (r4 retry 96/192, r3n retry 96/96, r6 fallback 192/192, ctrl21 retry >134; exception MECH07 fallback
  64/402). Reading: adaptive stopping saves on units that end 'uncertain'; it does not make actionable units cheap.
AUDIT D (effective information) — DONE, $0: P(Y_C != Y_{C\e}) median 17.4% (range 14-28%) over 14 contrasts, i.e. ~83% of
  paired episodes end identically and carry no information about gamma. This is the headroom for trigger-conditioning
  and prefix replay, but only if "identical outcome" can be predicted before paying for the ablated episode.
AUDIT A (trigger sparsity) and AUDIT B (prefix-reuse fraction) — need per-step trigger logs; harness now records per step:
  prompt_changed, parse_changed, first action + admissibility, retry attempts, retry changed action, fallback used, LLM calls.
  Record-only change (bos_alfworld.py, 13 changed lines, syntax ok; behaviour unchanged by construction: only dict writes).
  Computed on the first new passes (see PROBE runs). Metrics: p_trig(e), p_behaviour-change(e), first-trigger position as a
  fraction of episode LLM calls (= reusable-prefix fraction), per component.
PROBE V (verifier structure, VICT-style, ~$0 on top of the probe passes): ALFWorld goals are PDDL; atoms derived from
  task_type + pddl_params (inReceptacle(obj,recep), isHot/isCool/isClean/isSliced(obj), toggled). Witnesses = observation
  text after an action ("You put/heat/cool/clean/slice ..."). Trace component -> action -> atom: for each component
  activation (retry changed the action; fallback used; parse changed), did the resulting action establish an atom (+),
  destroy one (-), or neither (0). Profile per component: (activations, +, -, 0). PREDICTION (frozen): sign of (+ - -)
  agrees with sign of gamma^global for units with |gamma| >= 5pp in >= 75% of cases, AND it separates the two fallbacks
  (r6 harmful, L2 c4 beneficial). KILL: either fails.
PROBE L (local counterfactual, C3-style, GPU): deterministic prefix replay (TextWorld is deterministic given actions; hooks'
  state is rebuilt by replaying memory_update over the prefix) -> at the first activation state of e_i branch ON (C) vs OFF
  (C\e_i), continue to terminal. 8 activation states per component x 2 branches, components: r6 fallback (gamma -6.8), L2 c4
  fallback (+16.7), r4 retry (+13.0), r4 HISTORY (~0). gamma^local = mean(Y_on - Y_off). PREDICTION: rank order of gamma^local
  matches gamma^global (Spearman > 0.7 over the 4) and cost per component <= 30% of a full 96-game LOO. KILL: either fails.
PROBE P (progress/value): DEFERRED until V and L are read.
RUNS REQUIRED (GPU): (1) re-measure C for r6, L2 c4, r4 with step logs, 1 seed x 96 (3 passes) -> Audits A/B + Probe V data;
  (2) Probe L branches: 4 components x 8 states x 2 = 64 partial episodes (prefix free). Estimated ~3-4 GPU-h total.
