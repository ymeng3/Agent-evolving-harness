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
**Correction (A17):** the component ablation H1origP (H1 harness, ORIGINAL prompt) scores 0.82 on disc s1 (docs share 0.51, 22 cells,
completion 0.98): the disc gain is from the harness mechanics, not from the prompt rewrite (which only cuts episode length 22 → 13).
So V2's budget exhaustion was mostly induced by the evaluate() rollback, not by docs overhead. Isolating the rollback fix: V2noEval queued.
| H1 | val | 1 | 0.64 | 1.00 | 0.156 | vs V2 +6.0pp [-4, +17], p=0.46, tasks 10 better / 7 worse (1 seed) |
| H1origP | disc | 1 | 0.82 | 0.98 | 0.510 | vs H1 −1pp, p=1.0 (H1 harness + original prompt) |
| **H2** (= H1origP) | disc | 1–2 | **0.85** | 0.99 | 0.506 | vs V2 **+27pp [+18, +37], p<0.001, 18 better / 1 worse**; vs H1 +2pp, p=0.85 |
| V2noEval | disc | 1 | 0.70 | 0.72 | 0.514 | vs V2 +12pp [+3, +22], p=0.064; H1origP − V2noEval +12pp [+4, +20], p=0.067 (7 better / 1 worse) |
| V2noEval | val | 1 | 0.68 | 0.76 | 0.500 | vs V2 +10pp [0, +20], p=0.16; H1origP − V2noEval +16pp [+6, +28], p=0.039 (10 better / 2 worse) |
| **H2** (= H1origP) | val | 1–2 | **0.83** | 0.95 | 0.493 | vs F0old **+41.5pp [+32, +52], 32 better / 2 worse**; vs V2 **+25pp [+16, +34], p<0.001**; vs H1 **+15pp [+8, +22], p=0.003** |
| H1origP | val | 1 | **0.84** | 0.94 | 0.505 | vs H1 **+16pp [+6, +26], p=0.015**; vs V2 +26pp, p<0.001 |
| H1 | val | 1–2 | 0.68 | 1.00 | 0.155 | vs V2 +10.0pp [0.0, +21], p=0.15, tasks 11 better / 5 worse; vs F0old +26.5pp, p<0.001 (2 seeds) |

H1 val: every episode completes; all 18 losses are "completed but wrong". In the H1 val s1 log (baseline, before any D10 arm runs),
the frozen D10 detector (A15) would fire on 9/18 losses and 0/32 wins; 3 more losses pass an order id / sentence on action tasks that
D10's question-cue rule misclassifies as questions ("who/what/which" in relative clauses; a "?" inside a quoted note). D10 is NOT
changed (that would tune on validation); the refined cue rule is recorded as a candidate for a later, fresh test (A16).
**A18:** the H1 prompt rewrite HURTS on val: it removed "always look at API specs", so the agent never reads complete_task's spec
(0/50 vs 18–24/50), which states that action tasks take no answer → id/sentence answers on 9–12 losses vs 2. New base H2 = H1 harness +
original prompt. Disc decomposition of V2 → H2 (+24pp): the rollback fix alone +12pp; the remaining mechanics (step stamp, debounce, signature hints,
unmentioned helpers) another +12pp and lift completion 0.72 → 0.98 at the same 22–24 cells (step stamp = budget awareness is the prime
suspect). Same split on val: rollback fix +10pp, other mechanics +16pp (completion 0.76 → 0.94).

| E_ANSCHK (H1 + frozen D10) | val | 1 | 0.86 | (n/a*) | 0.165 | vs H1 s1 **+22pp [+10, +34], p=0.008, 13 better / 2 worse**; gate fired in 6 episodes, all won |

*the readout's "completed" regex looks for apis.supervisor.complete_task in the code, which the gate rewrites to _cc_complete.
Clean test (D10 frozen before any val data, A15). Only 6 of the +11 wins are direct gate hits; the rest is seed variance -> seed 2 pending.
| E_ANSGEN (H1 + same rule, always on) | val | 1 | 0.86 | 1.00 | 0.148 | vs H1 +22pp, p=0.014; **E_ANSCHK − E_ANSGEN 0.0pp [−10, +10], p=1.0** |

Targeting contrast (MATH §5): no difference. Consistent with §5: targeting only adds value where the advice harms non-trigger states
(c(σ) < 0); "answer only if asked" does not hurt question tasks, so always-on advice recovers the same failures.
Seed 2 of both pending (runs on vLLM with MTP spec decode from 2026-10-04 05:13; lossless, logged in queue history).
| H1.1origP | val | 1 | 0.66 | 0.90 | 0.505 | vs H2ctl −6pp [−16, +4], p=0.51 |
| H2ctl (H2 config re-run, same seed number, after server restart) | val | 1 | 0.72 | 0.96 | 0.476 | vs the two earlier H2 runs −11pp, p=0.044 |

**A20 resolution:** no server fault found (GPU only used by our vLLM, same vLLM config; val jobs take ~3100 s, the 3088 s of H2ctl is
normal). Most likely run-to-run sampling noise is larger than assumed: same-config val runs H2 0.84 / 0.82 / 0.72 (mean 0.793), H1
0.64 / 0.72 → per-run SD ≈ 7pp. H2ctl is counted as a third H2 run. Consequences: H1.1 is not shown to hurt (−6pp vs H2ctl, n.s.);
E_ANSCHK's +22pp was against the lower H1 run (vs H1 mean 0.68: ≈ +18pp), seed 2 pending. Key contrasts need ≥ 2–3 runs per arm.
Why H2ctl is lower: the extra losses are almost all "non-null answer on an action task" (H2 runs: 2, 3, **7** such losses; budget
2–3 and other 3–5 are stable). complete_task-spec reading is unchanged (18, 15, 18 / 50); all 7 ctl losses of this kind never read the
spec (answers: confirmation sentences or the order id 3146). So most of the ~7pp run-to-run variance of H2 comes from one stochastic
failure mode — exactly the D10 target. Expected side effect of the R3 answer gate: higher mean AND lower variance.
| **E_ANSCHK** (H1 + frozen D10) | val | 1–2 | **0.83** | (n/a*) | 0.174 | vs H1 (2 runs) **+15pp [+5, +25], p=0.033, 13 better / 5 worse**; gate fired 6 + 8 times, **14/14 of those episodes won**; vs H2 (3 runs) +3.7pp, p=0.55 |

D10 confirmed on 2 seeds (clean, frozen before val). Precision of the trigger is 14/14. H1 + D10 reaches the H2 level (0.83 vs 0.79)
with ~40% fewer steps (14.4 vs 23.8 cells) -> same success at much lower inference cost.
E_ANSGEN s2, H1.1origP s2, E_R3, E_R3ans: pending.
