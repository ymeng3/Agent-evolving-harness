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
A1 (2026-10-03, before any run; from an independent code review). (a) Examples shown to the proposer contain at most one trajectory
per task in BOTH arms (BOOST was otherwise picking both seeds of one task). (b) "called complete_task" for the landmark = an actual
`apis.supervisor.complete_task(` call, not a docs lookup naming it. (c) Stage 1 runs 2 independent replicates (seed 0, 1) of BOOST
and UNTARGET; PRIMARY = mean over the 2 replicates of the per-trajectory validation log-loss difference BOOST - UNTARGET after
round 6, task-cluster bootstrap 90% CI. (d) Stage 2 test unit = task (per-task mean over an arm's edits), not (edit, task).
(e) The "record cells in state in post_exec, intervene only when the condition holds" recipe and the always-return-a-string rule are
in the common FORMAT for all three arms; only the guidance content differs. (f) Proposer: thinking ON, max_tokens 16000, all arms.
(g) Correction: detectors see the FIRST 200 chars of each output (that is what the logs keep), not a tail. (h) Harness hardening in
bos_appworld_v3 (a pre_call returning a non-string is ignored; a raising setup hook is recorded instead of crashing the task); no
effect on unpatched F0 runs.

A2 (2026-10-03). REGIME DECIDED by the section-0 rule: thinking OFF scored 15/50 and 14/50 on Discovery (mean 14.5 < 22) vs 26/50
ON -> thinking ON for every executor run (BOS_THINK_OFF=0). Discovery data for Stage 1 = CC_F0_orig_seed1 + CC_F0_fix_seed1 (both
thinking ON, timeout 900; they differ only in the parse fix, which changed nothing: 25 vs 26, McNemar p = 1). Validation = new
CC_T1_F0_val seeds 1, 2. Proposer reasoning_effort = medium for all arms (probe on the round-1 prompt: xhigh 11.8k/15.5k tokens and
20-29 min per proposal under load; medium 6.9k tokens, valid; low ran to the 16k cap). The validation read-out is computed post hoc with boost/rescore.py (admission never uses validation).
STAGE 1b ("closed loop v2", requested by the user; runs alongside v1, does not replace it):
  Candidate pool per round = PROGRAMMATIC features (enumerated from a fixed grammar over the first L cells: calls per app / per API,
  docs lookups, docs-for-unused-app, errors, error streaks, repeated cells, empty outputs, time to first action, pagination, loops;
  no LLM) + SEMANTIC criteria (the self-proposer writes 3 natural-language criteria per round from examples; no code).
  Scoring: programmatic = code; semantic = a blind judge (Codex gpt-5.6-luna, reasoning high) that sees ONE trajectory prefix + ONE
  criterion, returns {evidence_cell, present in {0,1}}; 3 independent votes, majority. It never sees outcomes, goal checks, other
  criteria, weights or other trajectories. (Pilot on 10 prefixes: pairwise vote agreement 8/10, majority vs a code proxy 8/10.)
  Selection = XGBoost second-order gain for adding standardized feature z to the current logistic model (g = p - y, h = p(1-p)):
  Gain(z) = (sum g z)^2 / (2 (sum h z^2 + lambda)), lambda = 1. Admission: NESTED grouped CV of the whole step "pick argmax-gain
  candidate from the pool on the training folds, refit, score the test fold" must improve CV log-loss by >= 0.005; then the
  full-data argmax is admitted. Arms: V2_FULL (programmatic + semantic from residual-targeted examples), V2_PROG (programmatic only,
  no LLM at all), V2_SEM (semantic only, targeted), V2_SEM_UNT (semantic only, random examples). Rounds 6. Same validation read-out
  and bootstrap as section 1; PRIMARY v2 contrast: V2_FULL vs V2_PROG (does the LLM-proposed, judge-scored layer add held-out signal
  beyond pure math features); SECONDARY: V2_SEM vs V2_SEM_UNT (targeting), V2_FULL vs v1 BOOST.

A3 (2026-10-03, after V2_PROG round 1-6 on the A2 discovery data: nothing admitted, nested gain -0.039; top in-sample gains were
task-identity API features rejected by task-grouped CV; FIXED also worse than intercept, 0.755 vs 0.704). Iteration step under section 3,
ONE change: more discovery data. Two more thinking-ON Discovery F0 passes (CC_T1_F0_disc seeds 2, 3) are queued; when they exist, every
Stage-1 arm (v1 and v2) is re-run as "iteration 2" on the 4 pooled discovery runs (n ~ 170 landmark trajectories), same settings.
The iteration-1 runs on 2 discovery runs are completed and reported as they are.

A4 (2026-10-03, after V2_FULL iteration-1 round 1: 3 semantic criteria judged (vote agreement 0.87-0.95), nothing admitted, nested gain
-0.039 again). Diagnosis: the per-app / per-API count features encode task TYPE, dominate in-sample gain (5.4 vs < 1 for every behaviour
feature or criterion) and make the in-fold argmax unstable (the top one was picked in 6/15 folds; alone it has nested gain +0.097, the
pool -0.039), so no behaviour or semantic dimension can ever be selected. Iteration 2b, ONE change vs iteration 1, same data: the
programmatic pool keeps only the 22 behaviour features (no per-app / per-API counts): arms V2_FULL_B and V2_PROG_B. V2_FULL iteration 1
was stopped after round 1 and is reported as is. V2_SEM and V2_SEM_UNT (no programmatic pool, unaffected) run as iteration 1.

A5 (2026-10-03 01:30 server time, written before any run it governs). Motivating observation (interim: v1 iteration-1 states copied
mid-run, re-scored on CC_T1_F0_val seed 1, the only validation run that exists): every admitted v1 dimension makes held-out log-loss
WORSE than intercept (BOOST rep0 round 4: 0.821, UNTARGET rep1 round 4: 0.785, FIXED: 0.723, intercept: 0.671; AUC 0.35-0.46), and the
admitted detectors' correlation with success flips sign from Discovery to Validation (task_depth_progress +0.24 -> -0.21,
setup_cell_fraction -0.32 -> +0.20) while their within-task correlation on Discovery is small. Diagnosis: with ~2 runs per task the
pooled objective can only learn BETWEEN-task variation (which task families are easy); that does not transfer to new families and
cannot guide a harness edit. Discovery iteration 1 has only 11 within-task pairs that differ in success (15 in G), from 86 trajectories
over 44 tasks.
Change (new arms; the pooled A3 iteration-2 arms still run unchanged on the same data, so PW vs pooled is ONE change):
  OBJECTIVE = within-task PAIRWISE, i.e. XGBoost rank:pairwise with query group = task. Rubric score s(x) = sum_k w_k z_k(x), no
  intercept; data = all ordered pairs (i, j) of the same task with won_i = 1, won_j = 0; loss = mean over pairs of -log sigma(s_i - s_j)
  (Bradley-Terry on trajectories; any task-level offset cancels). Gain of a standardized candidate z: d = z_i - z_j, m = current margin,
  g = sigma(m) - 1, h = sigma(m)(1 - sigma(m)), Gain = (sum g d)^2 / (2 (sum h d^2 + lambda)), lambda = 1. Admission: nested task-grouped
  CV (3 x 5 folds) of "pick argmax gain on training tasks' pairs, refit, score held-out tasks' pairs" lowers the mean held-out pair
  log-loss by >= 0.005 nats. Semantic arms: examples = the 3 most MISRANKED pairs by out-of-fold margin (distinct tasks; both attempts
  shown, labelled better / worse; 6 trajectories as before); PW_SEM_UNT = 3 random pairs (distinct tasks). Same proposer (Qwen3.8-27B,
  effort medium), same blind judge, P = 3, rounds 6. Arms: PW_PROG (full programmatic pool incl. per-app/API counts, which within a task
  are behaviour rather than task identity; no LLM), PW_FULL (programmatic + targeted semantic), PW_SEM, PW_SEM_UNT.
  Read-out: validation within-task pairs (needs >= 2 validation runs per task): mean pair log-loss and pair accuracy (= within-task
  AUC) vs the 0.693 / 0.5 null, task-cluster bootstrap 90% CI. PRIMARY: PW_FULL vs PW_PROG. SECONDARY: PW_SEM vs PW_SEM_UNT; every PW_*
  arm vs null; PW_* vs the pooled iteration-2 arms on validation pair accuracy.
A6 (2026-10-03 03:20 server time, before any iteration-2 / PW run; capacity plan, no change to any rule). Discovery for iteration 2 and
for all PW_* arms = the 4 thinking-ON passes CC_F0_orig_seed1, CC_F0_fix_seed1, CC_T1_F0_disc seeds 2, 3. Validation read-out = all
CC_T1_F0_val seeds 1-4 (the queue now runs val seeds 3, 4 before disc seeds 4, 5, because validation pairs gate every A5 read-out;
disc seeds 4, 5 are reserved for a possible iteration 3). The local judge sustains ~25 concurrent calls, so semantic arms are rationed:
run all four PW_* arms; the pooled iteration-2 comparison arms are V2_PROG_B and V2_SEM (local) and v1 BOOST + UNTARGET seed 0 only
(server). V2_FULL_B, V2_SEM_UNT and the seed-1 v1 replicates are NOT re-run in iteration 2 (their iteration-1 results stand as
reported). The PW-vs-pooled secondary uses V2_SEM and V2_PROG_B.
Data (continuation of A3, more runs of the same kind): queue 2 more thinking-ON Discovery F0 passes (CC_T1_F0_disc seeds 4, 5) and 2
more Validation passes (CC_T1_F0_val seeds 3, 4), after the already-queued val s2 and disc s2, s3. The state file records which
Discovery runs a PW_* arm used; validation pairs come from all CC_T1_F0_val seeds that exist at read-out time (also recorded).

A7 (2026-10-03, before any run it governs; after the strong-model failure diagnosis docs/design/diagnosis_2026-10-03/TAXONOMY.md).
Stage-1 status: every rubric-learning arm (v1, v2, PW; iterations 1, 2, 2b) is null or negative on validation. New track, at the user's
request, in three steps: (1) fix harness bugs found by the diagnosis -> new baseline F0'; (2) rubric dimensions designed from the
diagnosed error classes, validated on logs (fire more on failures; within-task; holds on validation); (3) rubric-triggered prompt
interventions, evaluated on validation against F0'.
Step 1 = BOS_HARNESS_V2=1 (bos_appworld_v3.py): take the LAST closed code block; never execute a missing / syntactically incomplete /
'...'-placeholder block — tell the model why and re-ask, up to 3 free retries per step and 12 per episode (free = no cell spent); when
exhausted, spend the step executing nothing and say so (no silent show_app_descriptions fallback); api_docs outputs kept to 8000 chars
in history (was 3000); BOS_MAX_TOKENS=3072 (was 1024). F0' = CC_V2_F0_disc seeds 1, 2 and CC_V2_F0_val seeds 1, 2 (thinking ON).
Read-out: F0' vs the existing thinking-ON F0 on the same task sets (disc: 6 seeds, val: 4 seeds), task-level paired difference and
sign-flip test; descriptive counts of free retries, no-exec steps, docs share, completion rate. This is a base-harness change, not a
rubric claim; every step-3 intervention is compared against F0', never against the old F0.

A8 (2026-10-03, before any step-3 run). Step-2 result (appworld/boost/rubric_check.py, docs/design/diagnosis_2026-10-03/rubric_check_step2.json):
diagnosis-designed online detectors fire more on failures on BOTH discovery (6 runs) and validation (4 runs, new families): docs_repeat
+0.30 / +0.40 (within-task +0.39 val), harness artifact +0.24 / +0.24, supervisor detour +0.21 / +0.11, no-code streak +0.12 / +0.09,
api misuse +0.11 / +0.04, per-item +0.10 / +0.05; docs_heavy fires on ~98% of episodes.
STEP 3 design. Base = HARNESS_V2 (A7), thinking ON, BOS_MAX_TOKENS=3072. Arms (v3 patches, appworld/patches_ccdiag/):
  E_RUBRIC = RUBRIC_NUDGES_v1: six edits, each triggered ONLINE by one validated rubric detector (D1 docs share, D8 docs repeat, D2 per-item,
             D4 api misuse, D6 supervisor detour, D7 budget), injecting a short targeted [harness note] into that step's prompt only.
  E_GENERIC = GENERIC_ADVICE_v1: the same advice content appended at EVERY step, not triggered (tests whether rubric-triggered timing matters).
Evaluation on VALIDATION seeds 1, 2 (tasks_challenge_val50), paired by task with F0' = CC_V2_F0_val seeds 1, 2.
PRIMARY: E_RUBRIC - F0' success, per-task mean over the 2 seeds, task-level sign-flip test (two-sided) and 90% bootstrap CI.
SECONDARY: E_RUBRIC - E_GENERIC (same test); E_GENERIC - F0'. Manipulation checks: per-step prompt-changed rate, docs share of cells,
per-item rate, completion (complete_task called) rate, mean cells used. Discovery is in-sample for the design (it produced the diagnosis),
so it is not used for any step-3 claim.

A9 (2026-10-03, before any H1 run; user chose "option B": build a standard base harness first, step-3 RUBRIC/GENERIC val runs cancelled).
ISOLATION AUDIT RESULT: the harness called world.evaluate() after EVERY step (to log per-step goal checks). Replaying the logged code of
9126bf0 in a fresh world: with per-step evaluate the read-back after a successful update_alarm returns the OLD value and the task scores
0/7; without it the read-back is correct and the same code scores 6/7. Replaying all 50 CC_F0_fix_seed1 trajectories (actions held fixed):
26/50 with per-step evaluate (= logged), 28/50 without (7574325, 9126bf0 flip) — a lower bound, since the agent also wastes cells reacting to
stale reads (e52623a, 09ac073). All earlier AppWorld numbers in this project (and the collaborator's) carry this artifact.
H1 = BOS_HARNESS_H1=1 (implies V2) + BOS_AW_INSTR=appworld/prompts/instructions_h1.txt, each element a standard practice: no mid-episode
evaluate (final evaluate only); api_index(app) / api_sig(app, api) helpers in the sandbox (compact signatures, just-in-time docs); the
step count shown after every output; read-only duplicate cells blocked as free re-asks (debounce, only when no state-changing cell ran since);
parameter / unknown-API errors answered with the API's real signature (helpful errors); prompt rules rewritten (look up specs when unsure,
several per step allowed, batch repeated work in loops, 30-step budget stated). F0_H1 = CC_H1_F0_disc seeds 1, 2 and CC_H1_F0_val seeds 1, 2.
Read-out: F0_H1 vs F0' (V2) vs old F0 on the same tasks (per-task mean over seeds, sign-flip, bootstrap), plus docs share, completion
rate, cells used, blocked duplicates, signature hints. Step 3 (rubric-triggered nudges vs generic) is then re-run on top of H1, with the
nudges that H1 already covers (duplicate docs, budget display) removed from RUBRIC_NUDGES so they are not counted twice.

A10 (2026-10-03, before it runs). Literature review on feedback delivery (docs/design/LIT_NUDGE_DELIVERY.md): content specificity and
grounding matter more than timing (Leins et al. 2026; AutoGuide; Reflexion; SWE-agent). Third step-3 arm on H1: E_GROUNDED =
RUBRIC_GROUNDED_H1 (same validated detectors D7 > D2 > D6 > D1; one note per step, cooldowns; each note quotes the observed evidence, names
one concrete next action with a code skeleton, one "why"; D1 hedged; D7 never says finish unless the changes are made). Validation seeds 1, 2,
paired with F0_H1. Secondary contrasts: E_GROUNDED - E_RUBRIC (content), E_RUBRIC - E_GENERIC (timing / targeting), E_GROUNDED - F0_H1.

A11 (2026-10-03, before E_GROUNDED runs; E_RUBRIC / E_GENERIC unchanged). Re-reading rubric_check_step2.json: D1 (docs share) is NOT
predictive (fires on 97-100% of episodes; within-task diff 0.04 disc / 0.00 val), consistent with LOOP (2502.01600: RL on AppWorld
*increases* show_api_doc calls 1.6x). E_GROUNDED therefore replaces D1 with D8' (re-read of a spec already read within the visible
20-turn history window; D8 within-task +0.29 / +0.39). Prediction for E_RUBRIC's e1 (D1-triggered) is null-to-negative. Side finding:
HISTORY_LENGTH=20 drops early turns (specs, ids, tokens) after step 20 -- a candidate H2 harness fix (pinned working memory), to be
tested separately. Literature on failure -> check pipelines saved to docs/design/LIT_FAILURE_TO_RUBRIC.md.

A12 (2026-10-03). Diagnostic (not an arm, no claim): step-budget shadow price. V2 data: episodes reaching 30 steps win 15% and are
47/64 losses; winners use 21.3 steps (10.9 docs) with median first write at step 19, so the 30-step budget binds. Run F0_H1 with
BOS_AW_STEPS=45 on validation seed 1 (prompt states the real budget; no-op at 30). lambda_hat = (J(45) - J(30)) / 15 per step, paired by
task against F0_H1 val seed 1. Used only to convert "steps saved" by a dimension into expected value (MATH_FORMALIZATION §10).

A13 (2026-10-03). Branch-at-fire evaluation (MATH_FORMALIZATION sections 2/4: local estimate of a_k, efficiency RE_k = v_pair/(s_k^2 f_k v_k)).
Harness: H1 replay of a logged prefix is exact (no evaluate, hooks see replayed cells; smoke: a 20-step replay reproduces the win with 0 LLM
calls; the note is injected once at the first live step). Build: boost/branch_build.py on CC_H1_F0 disc+val logs (seeds 1, 2). States:
'endgame' (D7 firing, k = 27), 'budget20' (still running at step 20, no complete_task), 'first' (first D2 / D6 / D8' firing). Variants
none / plain (RUBRIC_NUDGES_H1 wording) / grounded (RUBRIC_GROUNDED_H1 wording or the counted progress note). Each run replays with the
episode's own AppWorld seed. Primary: endgame grounded - none and budget20 grounded - none, paired by state, task-level sign-flip and
bootstrap. Secondary: grounded - plain (content specificity at matched states); budget20 vs endgame (timing on the same episodes);
split by the logged outcome (harm in logged-won states = c(sigma) < 0). Readout: boost/branch_readout.py.

A14 (2026-10-03). H1 disc seed 1 = 0.84 (V2 0.58). Component ablation: CC_H1origP_{disc,val} seed 1 = H1 harness with the ORIGINAL
AppWorld prompt (helpers exist but are not mentioned). Contrasts: H1 - H1origP = prompt rewrite; H1origP - V2 = harness mechanics
(no evaluate, debounce, signature hints, step stamp). Queued ahead of the step-3 arms. With lambda ~ 0 under H1 (1/50 at the budget),
prediction for step-economy nudges (E_RUBRIC, E_GENERIC, E_GROUNDED, endgame branches) on H1: near-null; A12 (B45) is kept but low value.

A15 (2026-10-03, before any run). Round 2 of the diagnose -> rubric loop, on H1. Diagnosis of the 8 H1 disc s1 losses
(docs/design/diagnosis_2026-10-03/H1_disc_s1_failures.md): 4 (+1 secondary) = answer passed on an action task (order_id), 1 = silent
8000-char truncation hid the needed API (harness), 1 stock not checked before an irreversible order, 1 misread delivery target, 1
ground-truth convention (ba46d91, 336 vs 335; excluded from interpretation, not from the metric). New rubric dimension D10 "answer on an
action task" (no question cue in the task, and the answer is an id returned by the agent's own successful write, or a sentence > 8 words);
offline on disc s1 it fires on 5/8 losses and 0/42 wins (designed there, so disc is not a test). Arms on VALIDATION seeds 1, 2:
  E_ANSCHK  = H1 + ANSWER_CHECK_H1 (run-time check in the sandbox, blocks once with a grounded note; second call goes through);
  E_ANSGEN  = H1 + ANSWER_GENERIC_H1 (same rule as always-on advice every step) -- targeting contrast (MATH section 5);
  H1.1      = BOS_HARNESS_H11 (H1 + explicit truncation marker naming the cut APIs) -- harness fix.
Primary: E_ANSCHK - F0_H1 (val, 2 seeds, paired by task). Secondary: E_ANSCHK - E_ANSGEN; H1.1 - F0_H1. Manipulation check: rate of
non-null answers on action tasks; harm check: success on question tasks. Smoke (disc e7f15ba, replay to place_order): block path prints
the note and the agent then completes with no answer (won). Queued ahead of the step-economy arms (predicted null on H1, A14).

A16 (2026-10-03). Observation only, no change to any queued arm: on the H1 val s1 BASELINE log, frozen D10 fires on 9/18 losses, 0/32
wins. Candidate refinement (val-informed, therefore must be tested on data not used here): strip quoted strings before looking for '?',
and use question cues "tell me|let me know|how many|how much|what is/are/was|which one|give me|find out|answer" instead of bare
who/what/which. Not used in E_ANSCHK.

A17 (2026-10-03). A14 ablation result (disc s1): H1 harness + ORIGINAL prompt = 0.82 (docs share 0.51, 22 cells, completion 0.98) vs
H1 0.83 (2 seeds; +1pp, p=1.0) vs V2 0.58. The +25pp of H1 over V2 on disc comes from the harness mechanics, not the prompt rewrite;
the prompt rewrite only shortens episodes (22 -> 13 cells). This corrects the earlier attribution (RESULTS) and the §10 reading:
V2's budget exhaustion was mostly induced by the evaluate() rollback (writes undone -> re-dos), not by docs overhead.
Second ablation: CC_V2noEval_{disc,val} seed 1 = V2 + only the no-mid-episode-evaluate fix (BOS_NO_EVAL=1; no helpers, debounce, hints,
stamp; original prompt). Contrast V2noEval - V2 = the rollback fix; H1origP - V2noEval = debounce + signature hints + stamp + (unmentioned) helpers.

A18 (2026-10-04). H1origP val s1 = 0.84 vs H1 (H1 prompt) 0.68 (2 seeds): H1 - H1origP = -16pp [-26, -6], p=0.015 (tasks 3 better / 13
worse). Mechanism: the official complete_task spec says "Pass [answer] if and only if the task requests an answer ... If the task is not
a question ... the answer must be left to the default value, i.e., None". The original prompt ("Always look at API specifications before
calling an API") makes the agent read that spec in 18-24/50 episodes; under the H1 prompt it is read in 0/50 (all three H1 runs), and
api_index's compact signature cuts descriptions to 70 chars. Id/sentence answers on losses: H1 12 and 9 vs H1origP 2 vs V2 1. So the
prompt rewrite removed an information-gathering step whose value was invisible to the step-economy view (cf. LOOP: RL increases doc reads).
Decisions: new base H2 := H1 harness + original prompt (CC_H1origP); seed 2 on disc and val queued. H1.1 re-based on the original prompt
(CC_H11origP_val s1, s2; not yet run). D10 arms stay on H1 (high base rate of the error = high power for the targeting test, MATH §5).
Cancelled (never run): H1 RUBRIC / GENERIC / GROUNDED / B45 (base superseded; lambda ~ 0).
