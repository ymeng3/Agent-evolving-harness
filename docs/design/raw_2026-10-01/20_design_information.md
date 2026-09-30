# Decision-Targeted Rubric Evolution: information and decision-theoretic angle

## 1. Thesis

A rubric dimension is an experiment run on logged trajectories. It is worth its reduction in the Bayes risk of the decisions the loop actually makes, per unit of A800 time. Those decisions are: keep or drop an edit at ±3pp, which mechanism to target next, and which (candidate, task) cells to run. The value is computed through the AoS efficient-information operator.

This sidesteps credit assignment. We never estimate every component's effect. We estimate only the few decision functionals that can change an action: the lift γ_c of frontier candidates and the headroom η_m of mechanisms. A component ablation is run only when its value of information is positive, meaning it could flip a keep/drop. Most components never reach that point.

## 2. Setup

- **Tasks and candidates.** Tasks t ∈ 𝒯 belong to families f(t). Target weights ω_t sum to 1 over the Validation families; the sealed test is used once, at the end. Round-r candidates are c ∈ 𝒞_r, and c = 0 is the incumbent. A run (c,t,s) yields a trajectory τ, won Y and G. Every comparison is paired, i.e. uses the same (t,s).
- **Channels** k = 0, 0′, 1…K:
  - Gold channel 0: z₀ = sign(Y − Y′).
  - Gold channel 0′: sign(G − G′). This is the sign channel that had power 0.89 against won's 0.77 in the planted check.
  - Rubric dimension k: a programmatic check or judge prompt s_k(τ), with z_k = sign(s_k(τ) − s_k(τ′)), or a pairwise judge verdict in the style of OnlineRubrics [verified].
- **Observation model (tie-aware Bradley-Terry-Luce).** P(z_k ≠ 0) = q_{cc′tk} is a discordance nuisance. P(z_k = +1 | z_k ≠ 0) = σ(Θ_{ctk} − Θ_{c′tk}).
- **Low rank.** Θ = Σ_{r≤R} u_r ⊗ v_r ⊗ w_r: candidate capability-shift × task demand × channel loading, with R ≈ 2–4. The loading w_k is channel k's nuisance. This is the AoS tensor T* with a BTL link and non-uniform sampling, so the one-step estimator, score whitening and IPW carry over unchanged.
- **Decision functional.** ψ_c = γ_c = Σ_t ω_t q_{ct}(2σ(Θ_{ct0} − Θ_{0t0}) − 1). This equals E[Y_ct − Y_0t], and Γ_c is its gradient.
- **Information.**
  - A_D = P_T(Σ_{k∈D∪{0,0′}} G̃_k)P_T, where G̃_k is channel k's Fisher operator Schur-complemented against (w_k, q_k).
  - Per-pair information scales with q·σ′, so ties carry none.
  - H_c = A_D⁻¹P_TΓ_c is the least-favourable direction, i.e. the natural gradient of ψ_c on the tangent space.
  - V_c(D) = ⟨P_TΓ_c, H_c⟩.
- **Allocation and estimator.** Cell (c,t) is run with a known probability π_ct ≥ π_min. The reported estimator is design-based augmented IPW (AIPW):

  ψ̂_c = Σ_t ω_t [m̂_ct + (R_ct/π_ct)(Y^Δ_ct − m̂_ct)]

  Here Y^Δ is the paired contrast, R_ct indicates the cell was run, and m̂ is the rubric-augmented low-rank prediction. m̂ is either predictable (fitted only on data from before the cell was sampled) or cross-fit by family. The variance is

  V(π, m̂) = V_full + Σ_t ω_t² · (1 − π_ct)/π_ct · E(Y^Δ_ct − m̂_ct)².

  With π ≡ 1 the rubric adds exactly nothing (Kallus & Mao [verified], Cor. 2.1). Its measurement value is that it lets π fall at a fixed decision risk. That includes transporting effects to families that are never run, such as Validation and sealed.

## 3. The criterion

**Admission score.** For a proposed dimension j given rubric D, at the planned allocation:

  ρ_j = 1 − E_w(Y^Δ − m̂_{D+j})² / E_w(Y^Δ − m̂_D)²,  with weights w_ct = ω_t² · (1 − π_ct)/π_ct · d_c

This is the fraction of the decision-relevant sampling variance that j explains beyond D. The decision weight d_c = φ(|μ_c − δ|/σ_c) uses δ = the nearer of ±3pp.

**Local form.** To first order this is the AoS information increment

  ΔV_{c,j} = ⟨h_c, A_D⁻¹h_c⟩ − ⟨h_c, (A_D + B_j)⁻¹h_c⟩,  with h_c = P_TΓ_c and B_j = P_T G̃_j P_T.

For a rank-one channel B_j = a_j g_j g_jᵀ, Sherman–Morrison gives

  **ΔV_{c,j} = a_j⟨g_j, H_c⟩² / (1 + a_j⟨g_j, A_D⁻¹g_j⟩).**

The three factors are: reliability × non-tie rate (a_j), squared alignment with the natural gradient of the decision functional, and redundancy with what D already measures. This is the "gradient" answer: a new reward is useful if and only if its score direction projects onto H_c.

**Decision value (knowledge gradient; Frazier, Powell & Dayanik [verified]).**

  VOI_j = Σ_{c ∈ frontier} σ̃_{cj} · f(−|μ_c − δ|/σ̃_{cj}),  with σ̃²_{cj} = ΔV_{cj}/n_c and f(z) = zΦ(z) + φ(z).

Candidates far from ±3pp get weight near 0, so information spent on them is wasted.

**Estimator, in two stages.**
1. **Screen.** Compute a plug-in ΔV̂ from the fitted model. This is offline and takes seconds.
2. **Confirm.** Compute a cross-fit ρ̂_j, with folds = task families and m̂ fitted on the other folds. This removes the in-sample optimism that makes generic dimensions look good, which is the Clark–West point [verified].
   - Standard errors come from a family-cluster bootstrap.
   - Weak-signal bias in ⟨g,H⟩² is removed with split-seed cross-products, following the JIVE logic of Bibaut et al. [verified]. This matters because true effects are 1–7pp against ±8pp noise.

**Admit j** if all three hold:
- (a) LCB₉₀(ρ̂_j) > τ_a = 0.05, under α-investing wealth (Foster & Stine [verified]) charged for every dimension ever proposed;
- (b) re-judge κ ≥ 0.6 for judge criteria;
- (c) the drift test below passes.

**Remove k** if the leave-one-out score ρ_{−k} has UCB < τ_d = 0.02 (hysteresis). It is computed only on the current frontier, because usefulness depends on the policy (Razin et al. [verified]).
- Crucially, ρ_k is also evaluated on candidates generated after k was admitted. If proposers game k, m̂ mispredicts them and ρ_k turns negative. This is the surrogate-paradox detector.
- Example: an edit that forces an early complete_task raises "completed" but lowers won.

**Merge j and k** when their loadings have cosine > 0.95 in the A_D⁻¹ metric.

**Equivalent readings.** In the Gaussian limit, ρ_j is the squared partial IC. −½log(1 − ρ_j) is the conditional mutual information. It also equals the Barillas–Shanken residual α²/σ² [verified] and AlphaGen's incremental combination-IC reward [verified]. Four literatures reduce to one number.

## 4. Loop

```
state: incumbent h0; rubric tree D (v3 schema: parent, trigger, evidence, mechanism,
       intervention module, counter-evidence); model M on logs L; α-wealth W
for round r:
  # rubric step (offline, no GPU)
  fit M (channels 0, 0', D); compute H_c and residual field
      e_ct = d_c * (Y^Δ_ct − m̂_D,ct)                      # decision-weighted
  sample paired won-vs-lost trajectories (same t,s) with prob ∝ |e_ct|
  if one family/state predicate holds >50% of Σe²: request CHILD criteria with
      that trigger (edge cases); else request general criteria
  LLM proposes ~20 criteria (programmatic checks on AppWorld state/logs preferred)
  screen ΔV̂ → top 8 → cross-fit ρ̂ → admit/remove/merge (§3); update W
  # direction step
  headroom η_k = violation rate on incumbent failures × flip rate
      (branch at the violation step with a minimal corrective hint, if replay exists)
      × posterior of realized γ of past proposals targeting k (HGM-style clade stats)
  pick targets by top-two Thompson sampling on η_k; ≤4 edits per target
      (best-of-n cap, Gao et al.)
  # measurement step
  while budget left:
     KG_ct = Σ_c' σ̃_{c',ct} f(−|μ_c'−δ|/σ̃_{c',ct})       # rank-one update of A_D
     sample cells with π_ct ∝ max(KG_ct, π_min); run; append to L
     update ψ̂_c (AIPW); keep if P(γ>3pp)≥0.9, drop if P(γ<−3pp)≥0.9, else uncertain
  # inherit
  keep → fresh-seed Validation confirmation (winner's curse, Andrews et al.) → h0
```

The gradient appears twice:
- H_c defines what a good dimension measures.
- e_ct is the functional gradient of V with respect to adding a channel.

Proposing criteria that explain e_ct is gradient boosting in which the weak learner is an LLM writing a checkable criterion. The rubric moves from general criteria toward edge cases on its own, following wherever the residual mass concentrates.

## 5. Propositions

**P1 (aligned efficient information).**
- *Assumptions:* tie-aware low-rank BTL with channel nuisances (w_k, q_k), and regular non-uniform sampling under the AoS rank and incoherence conditions.
- *Claim:* ΔV_{c,j} has the form in §3, ΔV ≥ 0, and ΔV = 0 if and only if B_j H_c = 0.
- *Corollaries:*
  - (a) A channel that loads only on factors gold already identifies (task difficulty, generic "carefulness") has ΔV = 0. This is the formal reason rubric v1/v2 stalled.
  - (b) Value = alignment × tie-breaking.
  - (c) The Gaussian-limit identities in §3 hold.
  - (d) ρ is weakly submodular with ratio ≥ λ_min of the normalized channel-information matrix (Das & Kempe 2011 [unverified]), so greedy admission is (1 − e^{−γ})-optimal. Exact submodularity fails for suppressor pairs, e.g. "completed" × "answer-format-given-completed".
- *Proof idea:* Schur complement of the channel block in the AoS information equation, plus Sherman–Morrison. The new piece is profiling out the unknown loading w_j.
- *Feasibility:* 2–3 weeks.

**P2 (validity under an arbitrary rubric).**
- *Assumptions:* predictable π ≥ π_min and predictable or cross-fit m̂.
- *Claim:* ψ̂_c is unbiased, and the martingale CLT gives valid CIs for any rubric, including misspecified, gamed or paradoxical ones. See Zrnic & Candès [verified] and Kallus & Mao, which needs no surrogacy assumption.
- *Consequence:* a bad dimension wastes runs by widening the CIs. It cannot push the wrong-keep rate above α.
- *Feasibility:* 1–2 weeks; the argument is standard.

**P3 (admission consistency and exchange rate).**
- *Assumptions:* independence at the family level.
- *Claims:*
  - ρ̂_j is asymptotically normal and the bootstrap standard error is consistent.
  - α-investing controls the mFDR of admitted null dimensions.
  - The expected number of paired runs to resolve candidate c is ≈ (z₀.₉ + z_β)² V/|γ_c − δ|². This is the Gaussian Garivier–Kaufmann characteristic time [verified]. Admitting j multiplies the dominant sampling term by (1 − ρ_j), so "dimension j is worth ρ_j of the runs".
- *Numbers:* the per-run SD of paired won is ≈ 0.42 (from SE 0.060 at n = 50). Resolving γ = 10pp against the +3pp threshold therefore takes ≈ 160 runs (3.2 passes) with gold only. The target with ρ = 0.3 plus live-task allocation is ≈ 50–60 runs; this is a target, not a result.
- *Feasibility:* yes; it assembles known pieces.

**Not promised:** regret of the full loop, or Goodhart theory for discrete program search. Both are open.

## 6. Experiments

AppWorld only. Budget is in 50-task passes; assume ~110 passes per week for us.

**Prerequisite (week 1).** Close the remaining default-code path, which still affects 11 of 50 tasks. Log a default-code flag and use it as a stratum or nuisance.

**E0: calibration corpus (weeks 1–3, ~45 passes).**
- Design: 12 fixed candidates × (Discovery × 2 seeds + Validation × 1 seed).
- Candidates:
  - base, the parse fix, and 2 strip-answer patches;
  - step budgets of 30, 25 and 20 (planted, known effects);
  - 2 v3 mechanism edits;
  - a planted paradox (force complete_task by step 20);
  - a docs-reread cap, and a no-op.
- **Gate G0:** a rank-2/3 model beats the additive (candidate + task) model on held-out-seed deviance at p < 0.05. If not, set R = 1 and report P1(a) as a null. Either way, continue.

**E1: offline admission (weeks 3–6, 0 passes).**
- Pool of ~100 criteria:
  - 40 residual-guided (§4);
  - 20 failure-only LLM criteria (v2-style);
  - 15 hand-written programmatic checks;
  - 15 generic or random criteria;
  - 10 token-matched controls (same length and format, content permuted).
- **Gate G1:**
  - at least 3 dimensions with LCB(ρ) > 0.05;
  - generic, random and token-matched criteria admitted at a rate ≤ α;
  - Spearman(screen ΔV̂, realized held-out CI-width reduction) ≥ 0.5;
  - the pre-registered ordering holds: completion > steps > exec_error > api_docs ≈ 0;
  - the paradox plant trips the drift test.

**E2: decision replay (weeks 5–8, ~40 confirmation passes).**
- Subsample the corpus and replay keep/drop decisions.
- Rubric arms:
  - gold only;
  - gold plus the sign channel;
  - plus fixed rubric v2;
  - plus an LLM-judge score channel;
  - plus a PRM channel (AgentPRM-style);
  - Auto-Rubric log-det selection (untargeted EIG);
  - RLER std filter;
  - IRT-rubric (Yazdani et al., the nearest competitor);
  - ours.
- Each rubric arm is crossed with three allocations: uniform, Neyman on live tasks, and KG.
- **Gate G2 (primary claim):**
  - ≥25% fewer passes-to-decision than gold-only uniform at ≤10% wrong-side error;
  - ≥10pp of that saving attributable to the rubric rather than to allocation;
  - coverage ≥ 0.88 on the planted effects.

**E3: online loop (weeks 8–14, ~560 passes).**
- Four arms of 140 passes each:
  - (A) full framework;
  - (B) ours for measurement, but the proposer sees a token-matched diagnosis (isolates direction value);
  - (C) fixed rubric v2;
  - (D) no rubric, uniform allocation (Loop-1 replica).
- Endpoints:
  - decided candidates per pass;
  - direction IC: realized proposal γ against predicted η_k, with ICIR over rounds;
  - sealed-test lift of the final incumbent, 3 seeds (secondary; powered only for ≥7pp).
- **Gate G3:** A > B on direction IC with P ≥ 0.9, and A ≥ 1.5× D on decisions per pass.

**Optional:** replicate E1/E2 offline on the ALFWorld Loop-1 corpus. This needs the per-game logs, which the empirical check did not find.

**Headline plots:**
1. ΔV̂ screen against realized variance reduction, coloured by proposal source.
2. Passes-to-decision against wrong-side rate, for every baseline.
3. ρ_k over rounds: admission, decay and removal, including the paradox plant.
4. Realized γ against headroom, ours vs token-matched.

**Total:** ≈ 690 passes, with ~40% held in reserve.

## 7. The IC question

On the same demeaned data, the IC t-statistic equals the slope t-statistic, so IC adds no power by itself. It helps in three other ways:
- **Blocking.** Cross-sectional demeaning blocks on task difficulty; pairing already cuts variance to 0.35×.
- **Robustness to G's noise.** Rank and sign statistics tolerate G's all-or-nothing jumps. Here that is part of the likelihood rather than a trick: channel 0′ is a BTL sign comparison.
- **Incremental IC is the admission score.** It is exactly ρ_j.

MSE looks flat for two reasons. R² = IC² sits beneath the irreducible Bernoulli variance. And nested MSPE comparisons are biased against the larger model (Clark–West).

Grinold's IR ≈ TC·IC·√BR [verified] maps directly:
- IC = measurement value ρ;
- TC = direction value (E3, arm B);
- BR = the number of independent live families.

Report ICIR by Fama–MacBeth, clustered by family.

## 8. Failure modes, and fit with the empirical check

- **No interaction structure (G0 fails).** The model-based gain disappears, and the paper rests on P2, allocation and direction. Pairing already removes the task main effect and pre-run covariates add under 5%, so any gain must come from task×candidate interaction. Only 2 patches currently share the same 50 tasks, so E0 is mandatory.
- **Correlated channels within a run.** Channels computed on the same trajectory make the plug-in Fisher information too large. Use a joint (sandwich) per-pair information in the screen, and trust only the cross-fit ρ̂.
- **Too many ties.** About two thirds of tasks are deterministic. If rubric channels also tie on them, a_j is tiny.
- **Goodhart and decay.** Loadings drift once proposers target a dimension. Frontier-only removal plus P2 handles this, but expect churn.
- **Completion is almost won and is gameable.** P(won | completed) is 0.81–0.90. The paradox plant tests exactly this.
- **Direction value may be unmeasurable** at this budget. In that case, claim measurement and allocation only.
- **Remaining confounds.** Default-code steps still affect 22% of tasks. The Discovery jump to 26/50 mixes the parse fix with the 900 s timeout fix. Stratify on both.
- **Consistent with the empirical check:**
  - The minimum detectable effect is ≈17pp at n = 50, so validating each dimension by a downstream A/B is impossible; hence the offline cross-fit ρ.
  - There is no early proxy (G = 0 at step 10), so value has to come from structure and allocation, not truncation.
  - The binding gap is the 30-step budget. The first dimensions admitted should therefore be about efficiency (wasted exploration, docs re-reads). If the residual-guided proposer does not surface them, treat that as a red flag.

The frozen keep/drop rule this plugs into is in `C:/Projects/Cleanup_Archives_2026-08-27/Local_Latex_Files/Local_Latex_Files/Agent-evolving-harness/docs/preregs/CREDIT_REGIME_QUAL.md` (P2).