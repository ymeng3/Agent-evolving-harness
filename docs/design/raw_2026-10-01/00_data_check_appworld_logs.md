# Empirical check of AppWorld logs for the evolving-rubric / IC idea (read-only; data as of 2026-09-30 23:40)

**Bottom line.** A 50-task paired comparison can only detect about a 17pp change. The dense score G is not more stable than binary won, and a mean test on G has about the same power as one on won. What does help is a rank or sign test on G, the analogue of the quant IC, because it tolerates G's all-or-nothing jumps. The main failure is running out of the 30-step budget, not giving wrong answers.

## 1. What data exists

| Group | Runs | Same task list? |
|---|---|---|
| Validation 50 | ORACLE_SA_val seed1 (hand-written strip-answer patch) 26/50, mean G 0.676; V4T_val seed2 (discovered strip-answer patch) 23/50, mean G 0.569 | Yes, the only 50-task pair |
| Discovery 50 | CC_F0_fix seed1 (bare harness plus the unclosed-fence parse fix) 26/50, mean G 0.631 | Only one run. CC_F0_orig crashed (AppWorld save_logs ValueError) and wrote no results |
| Discovery smoke | SMOKE_box, CC_SMOKE_F0 (3 tasks, seed1), M3_ONBOARD_SMOKE (2 tasks) | Overlap CC_F0_fix |
| Single-task | 83 runs, 10 tasks (4815c06_1 and d6d8cb6_1 have 18 each), 26 patch families, seeds 1–4, only 5 wins. Includes RVOc vs RVOctl: 13 pairs on the same task and seed | Per task |

**Missing:**
- The per-task files behind the bare-27B numbers (18/50 and 19/50 on Discovery, 14/50 and 10/50 on Validation) are not on the box or in the local repo.
- There are no ALFWorld per-game results either.
- So no per-task contrast with a known effect was available. The two Validation patches differ in their trigger heuristic on only 2 of 50 tasks. The Validation pair is therefore close to a two-seed replicate of the same agent.

## 2–5. Key numbers

| Quantity | Value | What it means |
|---|---|---|
| **Between-task share of variance, won** (Validation pair) | 0.646; seed agreement 82%, kappa 0.64 | Task difficulty is the dominant "market factor" |
| Between-task share, G | 0.462 (Pearson 0.46, Spearman 0.54) | **G is less reproducible across runs than won** |
| Between-task share, time-to-success (score = won·(31−steps)/30) | 0.835 | Most reproducible metric, but see the budget row below |
| Won flip rate between seeds | 9/50; 8/48 on the tasks where both patches trigger the same way | About 1/3 of tasks are "live" (random); about 2/3 are deterministic |
| Same patch, same seed, repeated (MGT ×3 on d6d8cb6_1, seed 2) | G 0.9 / 0.7 / 0.7 | Fixing the seed does not reproduce a run, so pairing only removes the task effect |
| Single-task pool, G | Task accounts for 51% of variance (intraclass correlation 0.49); replicate-noise variance 0.035 (sd 0.19) | 46% of the spread in G between different patches on the same task is pure run noise |
| **Paired vs independent SE of the difference, won** | 0.101 → 0.060 (variance ratio 0.354, about 2.8× effective sample size) | Pairing on tasks works |
| Paired vs independent SE, G | 0.089 → 0.065 (ratio 0.54). RVOc vs RVOctl, G: ratio 0.25, n=13 | |
| **Minimum detectable effect, paired, n=50, 80% power** | won 16–17pp; G 17–18pp; unpaired won 28pp | Detecting 5pp needs about 530–560 paired task-runs per arm, about 11 full passes |
| Per-task correlation of the won difference with an aux difference (1−ρ²) | G 0.79 (0.37); maxG 0.81 (0.34); complete_task called 0.77 (0.40); G at step 25 0.64 (0.60); steps −0.40 (0.84); exec_error rate −0.10 (0.99) | **Not valid as control variates.** These features are measured after the patch acts, so their expected difference is unknown |
| Same, for features fixed before the run (CUPED-style) | number of goal checks −0.07; needs-answer 0.09; instruction length −0.18; trigger-disagree 0.21 | At most about 5% variance reduction; pairing has already removed what these could |
| default_code rate as a feature | Not logged in the Validation runs | Could not be tested there |
| **Cheap truncated evaluation** | G at step 10 is 0 on every task in all three 50-task runs. AUROC of G at step 15 for final won: 0.56–0.70; at step 25: 0.84–0.92 | Goal checks only pass late, so there is no cheap early proxy on AppWorld |
| **IC across tasks** (one run's signal vs the other run's won, Spearman) | won 0.65; G 0.53–0.60; steps −0.54 to −0.57; complete_task called 0.53–0.56 | The task factor predicts well across seeds and patches, which is what the low-rank model would exploit |
| **IC within a task across runs** (8 tasks, outcome = G; mean IC / t) | complete_task called +0.69 / 5.8; steps −0.55 / −3.0; exec_error −0.37 / −2.7; api_docs lookup share +0.08 / 0.4; G at step 20 +0.50 (only 4 tasks) | Candidate rubric dimensions are clearly ordered. These are same-run associations, not tested on a second seed |
| The literal "signal on seed 1 vs won on seed 2, across patches" IC | Only 1 task has ≥3 patches with 2 seeds each (Spearman 1.0 on near-tied G) | **Not feasible with this data** |
| Validation pair, randomization (sign-flip) p-values | won t 1.00, p 0.51; G t 1.64, p 0.11; G sign test p 0.33 | Consistent with no real difference between the two patches |
| **Planted effect** (30-step vs 25-step budget, other seed; true effect about +16pp won) | Won t 2.64 / 2.00; G t 3.34 / 1.47; **G sign test z 3.27 / 2.40**; Wilcoxon 3.02 / 1.74. Bootstrap power at n=50 (won, G, G sign): 0.77, 0.71, **0.89**; at n=25: 0.55, 0.55, 0.69 | Density alone does not help. A rank/sign test (the IC analogue) does, because G's noise is all-or-nothing jumps |
| Time-to-success score on the planted effect | t 0.83 / 1.34 | Most reproducible, least sensitive: stability and ability to tell candidates apart are different properties |
| **Failure breakdown** | 75–88% of failures never call complete_task within 30 steps. P(won given completed) 0.81–0.90; P(won given not completed) 0. Only 3–6 of 50 tasks per run are "completed but wrong" | The main capability gap is running out of steps, not answer format |
| Wins come late | Median 21–24 steps; 9–12 of 23–26 wins at step ≥25. ORACLE success by step 24 is 0.28, by step 30 it is 0.52 | Budget is binding. 7 of 9 seed flips are "one run completes (G=1), the other runs out (G=0)" |
| Partial credit in G | 41–50% of failures have G>0; 11–25% have G≥0.75; correlation of G with won 0.79–0.89 | G adds only modest information beyond won |
| Parse-fix run (Discovery) | 33/50 tasks had an unclosed-fence reply (83 steps). **11/50 tasks still had default-code steps (47 steps), and those won only 27%** | The default-action confound is reduced, not gone. The jump from 18–19 to 26 of 50 mixes the parse fix and the 900 s timeout fix |
| Most common failed goal check (54 single-task rows) | "answers match" 45 times, mostly from never completing; then task-specific email and order checks | |

## What this means for the design

1. **The noise floor rules out validating each new rubric dimension by downstream success on 50 tasks.** The minimum detectable effect is about 17pp against expected dimension effects of a few pp. A dimension's value has to be measured more cheaply per unit of information.
2. **Measure a new reward dimension by how well it separates candidates within a task, not by level or MSE fit.** Use its per-task IC across candidates, scored against the outcome on a *different* seed (mean IC and IC-to-volatility ratio), plus its incremental IC after regressing out the existing dimensions. On real logs this already ranks dimensions sensibly: completion ≫ steps > exec errors ≫ api_docs lookups (about 0). Reproducibility alone is misleading: the time-to-success score is the most stable metric and the least sensitive one.
3. **Use rank or sign statistics on G as the primary test, and paired won as secondary.** The quant-IC intuition holds here because G's noise is heavy-tailed jumps, not because G is dense. A mean test on G has about the same power as a mean test on won.
4. **Allocate evaluation adaptively.** About 2/3 of tasks are deterministic under the current agent. Re-running only the live tasks (Neyman or active allocation, with inverse-probability weighting, which is the non-uniform-sampling setting of your AoS paper) could cut cost by roughly 3×. Truncated runs are not a usable cheap proxy, because G is zero before about step 15–20.
5. **Low rank is plausible, but its benefit must come from task-by-patch interaction.** Pairing already removes the task main effect, and the pre-run covariates add under 5%. Estimating a rank needs at least 5–10 patches on the same tasks; today there are only 2 on the same 50 tasks.
6. **Point the rubric at the binding constraint.** That is reaching completion within 30 steps (efficiency, wasted exploration). The strip-answer edits only address 3–6 tasks per 50.
7. **Before crediting any parse or fallback edit, fix the remaining default-code path or at least stratify by it.** It still affects 22% of tasks.

**Caveats:**
- There is effectively one 50-task pair (a near-replicate), one Discovery run, and 83 mixed-purpose single-task runs.
- The planted effect is a step-budget cut. It removes late wins specifically, which may favour sign tests.
- Within-task IC uses same-run features, so part of the association is mechanical.

Everything is in `/root/autodl-tmp/cc/tmp/ic_check/` on the server: the scripts `inv.py`, `peek.py`, `peek2.py`, `ana.py`, `ana2.py`, `ana3.py` and their outputs `ana_out.txt`, `ana2_out.txt`, `ana3_out.txt`. Local copies of the scripts are in `C:/Users/Owner/AppData/Local/Temp/claude/C--Projects-Cleanup-Archives-2026-08-27-Local-Latex-Files-Local-Latex-Files-Agent-evolving-harness/57e9c937-6acb-4624-9f6e-81989b534107/scratchpad/`. No eval jobs were started, vLLM was not touched, and nothing under the collaborator's tree was modified.