# CC-BOOST results log (prereg: CC_BOOST_RUBRIC_PREREG.md). Every iteration is reported, including null ones.

## Section 0 — regime
Thinking OFF Discovery F0: 15/50, 14/50 vs thinking ON 26/50 -> thinking ON (A2). Thinking-ON Validation F0: seed 1 20/50, seed 2 22/50.

## Stage 1 v1, iteration 1 (Discovery = CC_F0_orig_seed1 + CC_F0_fix_seed1, 86 landmark trajectories / 44 tasks; finished 2026-10-03 ~02:20 server time)
Validation = CC_T1_F0_val seeds 1+2: 97 landmark trajectories / 49 tasks, 39 wins. Read-out by boost/rescore.py.

| arm | admitted dimensions (round) | final val log-loss | val AUC |
|---|---|---|---|
| FIXED | error_rate, error_streak, docs_share, repeat_cell, apps_touched | 0.7097 | 0.495 |
| BOOST rep0 | task_depth_progress (r3), redundant_api_calling (r4) | 0.7640 | 0.466 |
| BOOST rep1 | task_api_progress | 0.7781 | 0.434 |
| UNTARGET rep0 | none (= intercept) | 0.6771 | 0.500 |
| UNTARGET rep1 | setup_cell_fraction, multi_app_login_count, max_same_api_cell_repetition | 0.7113 | 0.578 |

PRIMARY (A1c): mean over replicates of per-trajectory val log-loss, BOOST - UNTARGET = **+0.0768, 90% CI [+0.0339, +0.1224]**
(task-cluster bootstrap). Per replicate: rep0 +0.087 [+0.009, +0.174], rep1 +0.067 [+0.010, +0.125].
**Result: negative.** Residual targeting makes the pooled rubric significantly WORSE on new task families; no admitted rubric beats
intercept. Diagnosis (see A5): with ~2 runs per task the pooled objective learns between-task (task-family) variation, and residual
targeting concentrates the proposer on exactly the tasks whose family effects do not transfer (detector correlations flip sign).
Exploratory (not preregistered): the same final rubrics scored on WITHIN-task validation pairs (only 10 pairs / 10 tasks):
pair accuracy BOOST rep0 0.70 [0.55, 0.85], BOOST rep1 0.75 [0.60, 0.90], UNTARGET rep1 0.90 [0.70, 1.00], FIXED 0.50 — the
detectors carry some within-task signal that the pooled weights do not exploit; motivates A5, too few pairs to conclude anything.

## Stage 1 v2 iteration 1 / 2b (local; Codex judge)
Same Discovery / Validation as v1. Read-out by boost/rescore_v2.py (semantic dimensions judge-scored on validation, cached votes).

| arm | admitted (round) | final val log-loss | val AUC | val within-task pair acc (10 pairs, exploratory) |
|---|---|---|---|---|
| V2_PROG | none | 0.6771 | 0.500 | 0.5 |
| V2_PROG_B | none | 0.6771 | 0.500 | 0.5 |
| V2_FULL | stopped after round 1 (A4), nothing admitted | - | - | - |
| V2_FULL_B | sem core_data_not_yet_retrieved_by_cell_14 (r1), sem excessive_api_doc_lookups_in_late_cells (r6) | 0.8583 | 0.493 | 0.50 [0.35, 0.65] |
| V2_SEM_UNT | sem all_required_app_authentications_complete (r1), sem multiple_successful_task_relevant_api_calls (r3) | 0.7566 | 0.584 | 0.60 [0.45, 0.75] |
| V2_SEM | sem all_required_apps_authenticated_and_core_data_retrieved (r3) | 0.7041 | 0.596 | 0.60 |

(V2_SEM_UNT re-scored once more later: 0.7598 / AUC 0.584 / pair acc 0.55 — a few third votes were re-drawn; same conclusion.)
Paired task-cluster bootstrap on per-trajectory val log-loss (90% CI): V2_FULL_B - V2_PROG_B +0.181 [+0.047, +0.325] (worse);
SECONDARY targeting V2_SEM - V2_SEM_UNT -0.056 [-0.115, +0.006] (targeted slightly better, CI touches 0); V2_SEM - V2_PROG_B +0.027
[-0.065, +0.124]. No v2 arm beats intercept on validation log-loss; V2_SEM has the best ranking (AUC 0.596) but is miscalibrated.

**Result: null/negative, same as v1.** The XGBoost-gain + nested-CV admission rule rejects every pure programmatic feature (no false
positive), but the semantic criteria it does admit are "how far along is the agent at cell 14" (progress / task-difficulty proxies) and
are worse than intercept on new task families. PRIMARY v2 contrast V2_FULL(_B) vs V2_PROG(_B): V2_FULL_B worse (0.858 vs 0.677).

## Harness track (diagnosis → harness fixes; prereg A7–A9)

Readout: boost/step3_readout.py (per-task mean over seeds, paired; sign-flip p; task bootstrap 90% CI). Thinking ON, 3072 tokens.

| arm | split | seeds | success | completed | docs share | vs F0old |
|---|---|---|---|---|---|---|
| F0old (T1 regime) | disc | 2–5 | 0.48 | – | – | – |
| V2 | disc | 1–2 | 0.58 | – | – | +10.0pp [+4.3, +15.7], p=0.007 |
| F0old (T1 regime) | val | 1–4 | 0.415 | 0.515 | 0.534 | – |
| V2 | val | 1–2 | 0.580 | 0.710 | 0.499 | **+16.5pp [+8.5, +25.0], p=0.002, tasks 18 better / 5 worse** |

V2 = last closed code block + ast validation + free re-asks (no silent fallback) + 8000-char docs output. default_code 139 → 0.
Step usage under V2 (val s1 + disc s1/2): 47/64 losses hit the 30-step budget (win rate 0.15 at 30 steps); winners use 21.3 steps
(10.9 docs), median first write at step 19 → the budget binds (MATH_FORMALIZATION §10; λ diagnostic A12).
| H1 | disc | 1 | **0.84** | 1.00 | 0.156 | vs V2 **+26.0pp [+13, +39], p=0.002, tasks 20 better / 5 worse** (1 seed) |
| H1 | disc | 1–2 | **0.83** | 1.00 | 0.175 | vs V2 **+25.0pp [+14, +37], p=0.001, tasks 18 better / 3 worse** (2 seeds) |

H1 = V2 + no mid-episode evaluate (rollback bug) + api_index/api_sig helpers + debounce + signature hints + prompt rewrite (several specs
per step, batching, stated budget). Mean steps 24 → 13, docs share 0.51 → 0.16; only 1/50 episodes reach 30 steps → the budget no
longer binds (λ ≈ 0, MATH §10), so remaining failures are semantic (diagnosis of the 8 losses: H1_disc_s1_failures.md).
The previous diagnosis (TAXONOMY R1: the original prompt's "always look up specs / one chunk per step" caused 55% docs cells) → prompt
rewrite: this is one full turn of the diagnose → fix loop. Component ablation queued (A14): H1 harness + original prompt.
| H1 | val | 1 | 0.64 | 1.00 | 0.156 | vs V2 +6.0pp [-4, +17], p=0.46, tasks 10 better / 7 worse (1 seed) |
| H1 | val | 1–2 | 0.68 | 1.00 | 0.155 | vs V2 +10.0pp [0.0, +21], p=0.15, tasks 11 better / 5 worse; vs F0old +26.5pp, p<0.001 (2 seeds) |

H1 val: every episode completes; all 18 losses are "completed but wrong". In the H1 val s1 log (baseline, before any D10 arm runs),
the frozen D10 detector (A15) would fire on 9/18 losses and 0/32 wins; 3 more losses pass an order id / sentence on action tasks that
D10's question-cue rule misclassifies as questions ("who/what/which" in relative clauses; a "?" inside a quoted note). D10 is NOT
changed (that would tune on validation); the refined cue rule is recorded as a candidate for a later, fresh test (A16).
Step-3 arms, D10 arms, H1origP ablation: pending.
