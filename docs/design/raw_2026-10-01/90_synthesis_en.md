## A. Thesis

**Thesis.** On AppWorld the true outcome is free once a trajectory exists, so a rubric cannot be a better *label*: once `won` is observed, scores computed on the same run carry no further information (Kallus–Mao, all labels observed [verified]). This removes the surrogate/PPI reading all four frameworks share. A rubric can instead be a better *experiment*. Each dimension is an executable mechanism program (trigger, evidence, canonical fix, placebo, counter-evidence: the FailureMechanism schema made executable) that says **where** a deficit occurs and **what** minimal intervention tests it. Harness edits are deterministic (or seeded) hooks and AppWorld replays a logged code prefix exactly (claimed in `bos_appworld_v3.py`; audited in F0), so an edit and the incumbent produce identical trajectories until the edit first diverges, and the edit's entire effect is an advantage at that point. Hence (1) a dimension's value is the true improvement per evaluation pass it makes available, which factors as headroom (a causal directional derivative of success) × transfer × information per pass; (2) edits are tested only where they act, by replay-and-branch, which removes the 1/s² dilution that made every 50-task A/B here uninformative; and (3) only the true outcome under a known design decides inheritance, so the rubric steers and allocates but cannot bias.

**Title:** *Rubrics as Experiments: Localized Counterfactual Evaluation for Self-Evolving Agent Harnesses* (alt. *Measure Where It Acts*).

**Compared with component credit.** Per-component credit is a global contrast diluted by every run where the component is inert (1–7pp effects against ±8pp noise). Local per-mechanism experiments have costs computable in advance. One law explains the project's history: local counterfactuals credited trigger components but not every-step ones; generic dimensions produced dead hooks; and the Validation strip-answer pair, which differs on only 2/50 tasks, could never separate.

Your low-rank machinery becomes the design-and-pooling layer (targeted information of a dimension, c-optimal branching). It is gated rather than assumed, because the first-order speedup comes from coupling.

**Provenance.**
- **Backbone:** diagnostic-causal, because its object (interventionally validated mechanism programs) is the only one whose value survives when `won` is free; re-grounded by the efficiency reviewer's pivot (value = localized, design-based information).
- **Grafted from information:** decision targeting, hint-branching headroom, AIPW with anytime-valid CSs, α-investing.
- **Grafted from gradient-factor:** residual boosting and lifecycle rules.
- **Grafted from efficiency:** trigger-set c-optimal evaluation and design-based validity.
- **Dropped:** label/PPI value; Fisher information summed over one trajectory's channels; shared-factor surrogacy for acceptance; Tucker deficits; family clustering; completion as a rubric input; same-run IC screens; AKM intervals [verified] (V is independent of selection); "5× n_eff" claims; the online direction-IC race.

## B. Formal framework

- **Splits.** D_P (proposal; the only split the proposer sees), D_E (test), V (validation), S (sealed, 39 tasks). One task per family everywhere: cluster by task/scenario, never family.
- **Runs.** Harness h with budget H = 30. A trajectory is τ = (σ₀, a₀, σ₁, …), where σ_k is the prefix (history, environment state, hook state). Y = `won` is primary; G and the completion step K (censored at H) are secondary. Q^h(σ) = E_h[Y|σ], and J(h) = Σ_t ω_t E_h[Y|t].
- **Divergence.** κ_e(τ) is the first step at which edit e's hooks, run in shadow mode on the logged prefix, would change the model's messages, decoding settings or executed code. Divergence rate s_e = P_h(κ_e<H); branch cost f_e = E[(H−κ_e)/H | κ_e<H] runs. Every-step edits have κ_e ≈ 0.
- **Dimension** j = (T_j, F_j, F̃_j, C_j): a prefix predicate T_j (trigger ∧ evidence) firing at κ_j; a canonical non-oracle fix F_j at κ_j (a prefix-derived hint or control-flow action); a token-matched placebo F̃_j; a counter-evidence predicate C_j. An edit is *gated* on j if a wrapper keeps its action-changing hooks inert before κ_j.
- **Headroom.** η_j = J(h⊕F_j) − J(h⊕F̃_j) = s_j·ā_j, where ā_j = E[Δ_j(σ_κ)|fire] and Δ_j = Q^{h⊕F_j} − Q^{h⊕F̃_j}. The deficit map {(s_j, ā_j)} runs from general deficits (large s_j) to edge cases (small s_j). It is identified by intervention: no rotation ambiguity, and no confounding with task difficulty.
- **Latent object (AoS).** Θ ∈ ℝ^{T×J×A} (task × trigger type × intervention a ∈ {∅, F_j, F̃_j, e₁, …}); θ_{tja} is the logit of prefix-averaged success when a is applied at j's first firing on task t. Θ has low multilinear rank (few fix types, few task demands), with a reference constraint at a = ∅.
- **Observations.** A branch yields (X, Y): X = e_t⊗e_j⊗e_a is placed at firing sites by a known design p(x) that depends on the prefix only, never on the logged outcome; Y ~ Bernoulli(σ(⟨Θ,X⟩)) comes from a fresh suffix; the logged incumbent suffix gives a free a = ∅ observation. This is your single-index GLM under known non-uniform sampling: G(p) = Σ_x p(x)I(η_x)X_x⊗X_x, A(p) = P_T G(p)P_T, H = A⁻¹P_TΓ, V(p) = ⟨P_TΓ,H⟩. Rubric scores are deterministic prefix features that enter through the design and the proposer, never the likelihood. Branches are conditionally independent, so information genuinely adds and cannot be double-counted within a trajectory.

## C. Criteria

**C0. Core criterion: value rate.** A dimension is effective iff it raises the expected true improvement per pass:

  Λ_j = τ_j η_j / n_j = (50/z²)·η_j·τ_j·IR_j²,  IR_j = τ_j ā_j/√(f_j v_j).

Here n_j = z² f_j v_j/(50 τ_j² ā_j²) is the number of passes to decide an edit along j (z = z_α+z_β); v_j is the per-site variance of the branch contrast; τ_j is the transfer, i.e. the per-site advantage proposer edits realize divided by the canonical fix's, with a hierarchical posterior from coupled edit tests (clade statistics as in HGM [verified]).

This is gradient (η) × actionability (τ) × information (IR²). It is the fundamental law IR = TC·IC·√BR (Grinold; Clarke et al. [verified]) made literal, with IC_loc = ā/√v, TC = τ and BR = 1/f. Λ (a fixed-power approximation) is used only for allocation.

**Rule.** j joins the rubric R iff it passes C1. It becomes a target when P(Λ_j > max_{k∈R}Λ_k) ≥ 0.1, via Thompson sampling. It is demoted to descriptive if UCB(Λ_j) stays below the rubric median for 2 rounds.

**C1. Fixable deficit (the "gradient").** η_j is the directional derivative of J along mechanism j, net of the "any interruption helps" effect. Estimate on D_E sites: η̂_j = N⁻¹Σ_i 1{κ_ij<H}(R_i/π_i)(Y_i^F − Y_i^F̃), with a task-clustered anytime-valid CS giving p_j.

- **Admit** iff (i) p_j ≤ α_j, with α-investing wealth charged for *every* proposed dimension (Foster–Stine [verified]); (ii) F_j is silent wherever C_j holds; and (iii) if firing sets overlap by more than 20%, the incremental headroom η_{j|k} = E[1{fire}(Q^{F_k∘F_j} − Q^{F_k})] has LCB > 0.
- **Merge** substitutes (both incremental headrooms ≈ 0), keeping the one with higher Λ.
- **Retire** j if UCB(η_j) < 1pp on the current incumbent, or if s_j < 2% (flat rewards teach nothing; Razin et al. [verified]).
- **Re-test** every 2 rounds (value is policy-dependent).

Generic dimensions have Δ ≈ 0 by construction. A fix that moves its mechanism but lowers success gives η < 0 and is rejected. This is exactly the archived fallback failure: mechanism metric passed, outcome −16.4pp.

**C2. Information per pass (the "information gain").** At equal candidate-specific cost, first-divergence coupling (P1) gives

  RE_j = v_pair/(s_j² f_j v_j),

where v_pair = 0.18 is the per-task variance of the paired full-run contrast. Non-divergent runs contribute exactly zero by identity P1(a), not by the rejected assumption that "deterministic tasks have no effect".

In AoS form, j adds Schur-complemented information B_{j|N}, worth ΔV_j/c_j = [⟨h,A⁻¹h⟩ − ⟨h,(A+B_{j|N})⁻¹h⟩]/c_j for the decision functional ψ (h = P_TΓ; c_j = branch cost). For one site type this is a⟨u,H⟩²/(1+a⟨u,A⁻¹u⟩). It is zero unless j's sites align with the least-favourable direction H, and ½log(V_before/V_after) is the targeted information gain.

- **Estimation.** s_j, f_j from logs (no GPU); v_j from null branches; task-cluster bootstrap CIs.
- **Rule.** Test by coupling iff LCB(RE_j) > 1; otherwise use paired full runs.

Passes-to-decision at a given per-site advantage are independent of s_j (only the free log base scales as 1/s_j), versus 1/s_j² for the paired design: edge cases become testable.

**C3. Unbiasedness (Goodhart protection).** Only ψ_e = J(h⊕e) − J(h) on `won` decides inheritance:

  ψ̂_e = N⁻¹Σ_i 1{κ_ie<H}[m̂_i + (R_i/π_i)(Y_i^e − Y_i^∅ − m̂_i)],

where m̂ is a cross-fit low-rank working model; the estimator is unbiased for any m̂.

Validity rests on five audited assumptions: (A1) exact replay; (A2) divergence/gating; (A3) known, prefix-measurable π ≥ π_min, with π_min set by the power to detect harm; (A4) conditionally independent suffixes; (A5) stationary serving. None concerns the rubric, which only changes which edits exist and where branches go: it affects regret, not error rates (P3).

Guards: a task-level D_P/D_E split; 10% null branches for A–A drift; V confirmation on fresh branches with α-spending; the sealed test used once; a candidate's own rubric scores never used as outcomes.

## D. Loop

```
freeze h0: default-code fix, full-response logging, shadow replay rebuilding hook state, gate wrapper
B ← h0 base logs on D_E (≥150 runs) and V (≥100); W ← α-wealth
R ← 8 seed programs (docs thrashing, repeated API error, exec-error streak, no-progress loop, ...)
for round r = 1..6:
  U ← D_P failures with no admitted dim firing ≥8 steps before budget     # residual (functional gradient)
  J_new ← LLM(same-task won/lost contrasts from U) → executable dims (T, F, F~, C)
  screen on D_P logs ($0): s_j, f_j, overlap with R, within-task fire-vs-fail → top k
  for j in top-k ∪ stale(R): sequential F_j vs F~_j branches on D_E until CS decides or cap
      admit / merge / retire (C1); update W
  j* ~ Thompson(Λ);  E ← proposer(j*, D_P evidence) → ≤4 edits gated on T_j*   # best-of-n cap (Gao et al. [verified])
  for e in E: shadow-replay → κ_e    (dead hooks: s_e = 0 ⇒ ψ_e = 0, no GPU)
      branch at κ_e on D_E, π by cost-weighted Neyman / c-optimal design (P2); stop by CS
  e* ← top-two Thompson (Russo [verified]); confirm on V with fresh branches (α-spending)
  if pass: h ← h ⊕ e*;  B ← B with firing suffixes replaced by e*'s branches     # exact sample (P1d)
  audit: A–A null branches, replay spot-checks, +1 fresh base pass
```

Non-localized edits (κ ≈ 0) use task-paired full runs (F, statistic 2).

## E. Theory (ranked by value/effort)

**P1. Localized coupling and the dilution law** (1 wk; best value/effort). Under A1–A5:
- (a) ψ_e = E_h[1{κ_e<H}(Q^{h⊕e} − Q^h)(σ_{κ_e})]. This is the performance-difference lemma localized at a stopping time (Kakade–Langford [unverified]).
- (b) The coupled IPW estimator is unbiased, with Var = N⁻¹(E[1{fire}(v(σ)+Δ(σ)²)/π(σ)] − ψ²), v(σ) = Var(Y^e − Y^∅ | σ).
- (c) With m branches, RE = v_pair/(s² f v_site) when N·s ≥ m.
- (d) Base logs whose firing suffixes are replaced by e's branches form an exact i.i.d. sample of h⊕e.

*Proof:* induction on the prefix law, the tower property at κ, and IPW algebra.
*Corollary:* every-step components have s ≈ 1, so RE ≈ 1; trigger components have small s, so RE is large. Matches ALFWorld local CF: fallback 3/3, retry 6/7 correct; history/temperature failed.

**P3. Goodhart-safe acceptance under an evolving rubric** (1–2 wks). If the rubric, the edits and π are predictable with respect to past data and D_P, the AIPW increments are martingale differences. Anytime-valid CSs (Howard et al. 2021; Waudby-Smith et al. 2024 [unverified]) then give P(inherit e with ψ_e ≤ 0) ≤ α_r for *any* rubric, and α-investing gives mFDR ≤ α over proposed dimensions. *Proof:* Ville's inequality plus standard α-investing.

**P2. Value of a dimension as targeted information; c-optimal branching** (4–5 wks; the signature theorem, in your AoS setting). Take the logistic single-index model with design p and costs c.
- (i) V(p) is convex.
- (ii) j enlarges the tangent space by its loadings N_j. Its efficient contribution is the Schur complement B_{j|N} = G^{(j)}_{TT} − G^{(j)}_{TN}(G^{(j)}_{NN})⁻¹G^{(j)}_{NT}. So ΔV_j ≥ 0, with equality iff B_{j|N}H = 0. In particular ΔV_j = 0 without rank coupling (Kallus–Mao's no-free-lunch inside the model); this replaces the frameworks' rank-one update on a fixed P_T.
- (iii) The cost-constrained c-optimal design satisfies I(η_x)⟨X_x,H⟩²/c(x) ≤ V(p*)/C, with equality on its support (Elfving/Kiefer–Wolfowitz type [unverified]). In the coupled case this reduces to cost-weighted Neyman allocation.
- (iv) With predictable p_r ≥ p_min, your IPW one-step CLT survives (martingale extension).

If time is short, prove (i)–(iii) for fixed designs and leave (iv) as a remark.

**Corrections adopted.**
- Information adds only across conditionally independent observations.
- Partial IC, conditional MI, AlphaGen's ΔIC and Barillas–Shanken α² are monotone transforms of one partial regression, not one number.
- E[max of n N(0,1)] is 0.85/1.16/1.42 for n = 3/5/8, not √(2 log n).
- The sign test targets a different estimand.
- 0.354 = 1 − 0.646 is an identity.
- IPW variance scales as 1/π.
- Few clusters need a wild cluster bootstrap.

## F. IC vs MSE

**What transfers.**
- **Blocking.** Pairing is cross-sectional demeaning (variance ratio 0.354).
- **Rank/sign robustness to all-or-nothing jumps.** On the planted budget cut, power was 0.89 for G-sign, against 0.71 for mean G and 0.77 for `won`.
- **Breadth.** t ≈ IC√N_eff, so IC 0.1 needs about 900 effective contrasts for t = 3.
- **Incremental IC as an admission rule** (AlphaGen, Barillas–Shanken [verified]). Here it becomes incremental headroom.

**What does not.**
- **No free power.** A Pearson IC's t equals the slope's t on the same demeaned data.
- **Density is not the reason.** G is less reproducible than `won` (between-task share 0.462 vs 0.646), and mean-G power ≈ `won`.
- **Same-run IC is mechanical.** complete_task scores +0.69, but P(won | not completed) = 0.
- **Cross-candidate IC needs many candidates.** With 36, the detectable partial r ≈ 0.46.
- **The sign test changes the estimand.** It estimates P(ΔG>0) − P(ΔG<0), not the mean, and its edge rests on one planted monotone effect.

**Why MSE looks flat.** A localized effect s·ā is diluted by s and buried in noise from runs where the edit cannot act. Nested MSE comparisons also favour the smaller model (Clark–West [verified]). The IC that works blocks on the finest nuisance and measures the signal where it lives. Coupling blocks on the entire prefix and drops non-divergent runs. Per unit cost it gives z² ≈ IC_loc²·BR, against (sā)²/v_pair for the full-run test.

**Statistics to use.**
1. Localized edits: the coupled AIPW mean on `won`, plus an exact McNemar test on discordant branch pairs.
2. Non-localized edits: task-paired `won` with a sign-flip randomization test. G-sign is a named secondary; accept only if the mean `won` difference has the same sign.
3. Screening: within-task cross-run fire-vs-fail contrasts, Fama–MacBeth over tasks, task-clustered.

**Numbers.**
- The paired MDE at n = 50 is about 17pp (SE 0.060), and 5pp needs about 11 passes.
- With v_site ≈ 0.4 (not yet measured), s = 0.3 and f = 0.5, RE ≈ 10, so about 5pp resolves in one pass-equivalent of branches.
- The Validation pair has s = 0.04, a 25-fold dilution, which explains p = 0.51. Replaying its complete_task steps compares them exactly at no GPU cost.

## G. Experiments (≈300 passes; assumes ~15–20/day for us)

**F0 (week 1; no GPU; logs plus CPU replay on the box).**
- (a) Shadow-replay the 24 Phase-2 candidates (patches_v3) and the 8 seed dimensions on all logs: divergence rates, κ, predicted RE. Already visible: 4/24 are post_exec-only, whose return values the harness discards, so they are no-ops; 8/24 diverge only at complete_task, if at all.
- (b) Replay fidelity on the 3×50 logged runs.
- (c) Completion replay: score the complete_task-gated candidates and the strip-answer pair by executing the edited cell on the replayed state.
- **Gates:** fidelity ≥ 95% of steps and ≥ 98% of outcomes; coupled SE ≤ ⅓ of the paired SE (0.060); ≥ 3 seed dimensions fire on ≥ 20% of budget-exhausted failures with ≥ 8 steps left. If (b) fails → fallback I(b).

**E1 (week 2, ~10 passes).** Build the h0 base with full responses logged; run 30 sites × 4 null branches to estimate v_site and A–A drift; measure the slack ceiling by continuing 40 budget-exhausted failures for 10 more steps. **Gates:** A–A CI within ±3pp; v_site ≤ 0.5; slack ceiling reported (expected ≥ 15%).

**E2 (weeks 3–4, ~25 passes).** Calibration on planted gated effects (budget cut or extension at triggers, 3–10pp overall) plus 4 real edits. Truth is the pooled estimate. Baselines: task-paired full runs (`won`; G-sign), unpaired runs, and Loop-1 fixed-n leave-one-out. Metric: passes-to-decision at ≤ 10% wrong-side error. **Gates:** median realized RE ≥ ½ of predicted; 90%-CI coverage ≥ 0.85 over ≥ 40 null and planted tests.

**E3 (weeks 5–7, ~40 passes).** Headroom ledger for about 30 dimensions: 8 seed, about 15 residual-guided, 4 generic and 3 token-matched.
- Admission baselines [verified]: same-run correlation with `won`, RLER std, Auto-Rubric log-det, the LLM-judge rubric (rubric_aw), AgentPRM promise, and Yazdani et al.'s IRT rubric if released.
- **Gates:** ≥ 3 dimensions admitted; generic and token-matched dimensions admitted at a rate ≤ α.

**E4 (weeks 7–9, ~55 passes).** Direction trial with 3 arms × 24 edits, all evaluated by coupling: A rubric-targeted; B same gate with a token-matched shuffled diagnosis; C no rubric (the Phase-2 failure-conditioned proposer). The MDE for the A–B mean lift is about 3pp. **Gate:** A > B on hit rate or mean lift (one-sided p < 0.05). Otherwise claim localization value only.

**E5 (weeks 9–12, ~150 passes).** Closed loop, 3 arms × 6 rounds with equal passes: the full method, a fixed seed rubric, and a Loop-1 replica (no rubric, paired full runs). This is a secondary endpoint (MDE ≈ 7pp).

**E6 (week 13, ~24 passes).** Final incumbents on fresh V × 3 seeds and on the sealed set × 3 seeds.

**Headline figures.**
1. Dilution law: predicted vs realized RE per edit or dimension (log–log), with an inset of passes-to-decision vs |effect|.
2. Headroom ledger: recoverable failure mass by dimension across rounds, from general to edge case, admitted vs rejected.
3. Edit-lift distributions by arm, and true success vs cumulative passes.

## H. Timeline (Sep 30 → deadline ≈ late Jan)

| Weeks | Work | Decision |
|---|---|---|
| W1 | Infra; F0 | D0 (Oct 6): coupling go/no-go |
| W2 | Freeze h0; base; E1 | D1 (Oct 13): mid-trajectory vs completion-only scope |
| W3–4 | E2; write P1 | D2 (Oct 27): does the dilution law hold? |
| W5–7 | E3; write P3; start P2 | D3 (Nov 17): ≥ 3 dimensions admitted? |
| W7–9 | E4 | D4 (Dec 1): direction value? (sets the loop arms) |
| W9–12 | E5; low-rank m̂ gate (rank-r vs additive held-out deviance on non-planted branches) | D5 (Dec 15): keep or drop the P2 experiments |
| W13 | E6 (runs unattended over the holidays) | — |
| W14–16 | Writing, P2, ablations | Experiments frozen Jan 7 |

## I. Risks and fallback

1. **Replay or context infidelity.** Logs keep only resp[-600:], and replay feeds code-only assistant turns and skips v3 post_exec hooks. Fix before the base; F0b audits.
2. **Few localized edits.** If useful edits act at every step, RE ≈ 1. Report their share and route them to paired runs.
3. **"Lost" failures.** Wins come late (median 21–24 steps), and 75–88% of failures exhaust the budget. If the slack ceiling is small, the headroom lies in early planning, so target early-firing dimensions.
4. **Shared-box drift** (timeouts, default-code steps): null branches, one fresh base pass per round.
5. **Base overfitting:** D_P/D_E split, fresh-branch V confirmation, sealed set used once.
6. **Novelty.** Prefix rollouts exist (PAV [verified]; Math-Shepherd [unverified]), and so do IRT rubrics (Yazdani et al. [verified]). What is new: first-divergence coupling for program-level harness search, with a proven dilution law; rubric weights that are interventional headroom; and a co-evolving evaluator (DGM, HGM and ADAS keep theirs fixed [verified]).
7. **Thin evidence.** Unmeasured so far: v_site, replay exactness, the share of localized edits, and low-rank structure (only 2 patches share the same 50 tasks).

**Fallbacks.**
- (a) Coupling works but direction is null: "Measure Where It Acts", built from P1 + P3, E1–E2, and a re-analysis of Loop-1, local CF and the Validation pair.
- (b) Coupling fails: a noise-budget/design paper at workshop level.
- (c) Headroom is null: the evaluation paper, plus an analysis of where failures are recoverable.

## J. Open questions

1. Can logging change now (full responses, and shadow replay that rebuilds hook state)? Is AppWorld replay exact (IDs, timestamps, random_seed)?
2. May rubric-targeted edits be *required* to be gated, with no setup or every-step behaviour before the trigger?
3. May an LLM write canonical fixes from the prefix? May a reported-only oracle-ceiling arm read goal checks?
4. How many passes per day can we count on? Can CPU replays run alongside the collaborator's jobs?
5. May D_E and V add sibling variants (_2/_3), clustered by scenario? Should P2 be the headline theorem or go in an appendix?

Repo facts checked (2026-09-30):
- C:/Projects/Cleanup_Archives_2026-08-27/Local_Latex_Files/Local_Latex_Files/Agent-evolving-harness/appworld/bos_appworld_v3.py (L96–105 replay, L166–174 post_exec/logging)
- C:/Projects/Cleanup_Archives_2026-08-27/Local_Latex_Files/Local_Latex_Files/Agent-evolving-harness/appworld/patches_v3/
- C:/Projects/Cleanup_Archives_2026-08-27/Local_Latex_Files/Local_Latex_Files/Agent-evolving-harness/docs/preregs/CREDIT_REGIME_QUAL.md
- C:/Projects/Cleanup_Archives_2026-08-27/Local_Latex_Files/Local_Latex_Files/Agent-evolving-harness/README.md