# Residual-alpha boosting: the rubric as a factor model of the part of candidate effects the current criteria miss

## 1. Thesis
A rubric is a factor model of the within-task paired contrast in success, and a new criterion is worth adding exactly when it explains the *alpha*: the part of candidates' true held-out effects that the current criteria miss. Self-evolution is then functional-gradient boosting on that residual: an LLM proposes factors from high-residual trajectories, a factor-zoo test admits them, and the harness proposer is steered along the admitted factor with the highest expected return per proposal.

**How this avoids component credit.** Credit is assigned to trajectory features, not to components, through the chain rule δ_c = Σ_k β_k Δf_{ck} + α_c.
- **Loadings are pooled.** Each loading β_k = ∂E[Y|S]/∂f_k is fitted once, on every trajectory pooled together, with task blocking.
- **Per-edit work is small.** A new edit needs only Δf_{ck}: its effect on a dense process feature, and only for the one criterion being pushed.
- **Unit credit is never estimated.** The per-unit outcome credit that failed on ALFWorld (±15pp noise against 1–7pp effects) drops out.
- **What an edit must do.** An edit survives if it moves an admitted criterion without producing negative alpha.

## 2. Setup
- **Runs.** Tasks t (family φ(t)), candidates c = edit sets (c₀ = incumbent), seeds s. Each run (c,t,s) gives a trajectory τ, won Y∈{0,1}, and G∈[0,1].
- **Criteria.** f_k: τ→ℝ, a programmatic check over logs, instantiated from a FailureMechanism record (trigger, observable_evidence, mechanism, counterevidence; `appworld/phase2/schema.py`). Rubric R={f_1..f_K}, S=(f_k(τ))_k.
- **Controls X.** Hook flags, the default-code/parse-fallback indicator, and family fixed effects.
- **Surrogate index.** h_R(S,X,t)=E[Y|S,X,t], with task effects a_t as the "market factor" (0.646 of the variance of won). It is cross-fitted by seed, and ε_R = Y − h_R is the functional gradient (squared loss; use Y−σ(F) for logistic).
- **Effect decomposition.** δ_c = E_t[Y(c,t)−Y(c₀,t)] = Δh_c + α_c, where α_c = E_t[ε_R(c,t)−ε_R(c₀,t)].
  - Prentice surrogacy of R ⟺ α≡0.
  - τ²_α(R)=Var_c(α_c) is the rubric's pricing error.
  - Per-candidate noise over n tasks: Var(α̂_c−α_c)=v_ε/n and Var(Δh̄_c−Δh_c)=v_h/n.
- **Where low rank and the AoS paper come in.**
  - If Y~Bern(σ(a_t+η_{ct})), then P(Y_c=1 | Y_c≠Y_{c'}) = σ(η_{ct}−η_{c't}). This is exactly BTL, and a_t cancels (Rasch conditional likelihood). Within-task comparison is therefore the likelihood form of cross-sectional demeaning.
  - Stack channel ℓ=0 (outcome) with channels ℓ=k (within-task sign of the difference in f_k) into a low-rank tensor T*[c, φ, ℓ].
  - The AoS paper's machinery then applies unchanged: the EIF and one-step estimator for ψ_c (the held-out advantage on the outcome channel), IPW for the non-uniform (c,t) sampling that allocation creates, and the channel update A → A + P_T G_k P_T.

## 3. The criterion
A criterion has two roles, a direction role and a measurement role, and each gets its own statistic.

**(a) Screen: direction role, zero GPU.** The screen is a partial rank IC with the current residual, in Fama–MacBeth form over tasks:

IC_t(f) = Spearman_{(c,s)∈t}(ε̂_R, f̃), where f̃ = f − Π̂(f | S,X,t);
t_FM = mean_t IC_t / (sd_t IC_t/√T), clustered by family.

- Π̂ uses double selection (Feng–Giglio–Xiu [verified]): LASSO Y on (S,X), LASSO f on (S,X), then control for the union.
- It is computed on a trajectory fold the proposer never saw.
- In the Gaussian limit it is the partial correlation ρ_{Yf·S,X}, with conditional MI −½log(1−ρ²).

**(b) Confirm: measurement role, as a reduction in risk.** The loop ranks candidates with a rubric-shrinkage estimator:

δ̂_c(λ) = Δh̄_c + λα̂_c, λ* = τ²_α/(τ²_α+v_ε/n), R(R) = v_h/n + λ*·v_ε/n.

Setting λ=1 gives the plain paired outcome and λ=0 the pure surrogate. With Y observed and no restriction, S adds nothing (Kallus–Mao [verified]). The gain comes only from the restriction α≈0, learned across candidates, so λ is always estimated and never assumed.

**Definition.** Effectiveness is ΔR(f|R) = R(R) − R(R∪f). To first order:

ΔR ≈ (1−λ*)²·Δτ²_α − (1−λ*²)·Δv/n,
Δτ²_α = Cov_c(α_c,d_c)² / Var_c(d_c), d_c = E_t[f̃(c,t)−f̃(c₀,t)],

where Δv = γ²Var(Δf̃ | c) is the run noise the new term brings into h.
- **Admission condition.** f is effective iff Δτ²_α/(Δv/n) > (1+λ*)/(1−λ*). In words, f must explain signal across candidates faster than it adds run-to-run luck.
- **IC reading.** Δτ²_α/τ²_α = Corr_c(α,d)², the incremental cross-candidate IC².
- **Same quantity in two frameworks.** Δτ²_α is the same Schur complement as the Barillas–Shanken identity α_f²/σ²(ε_f) [verified] and the Sherman–Morrison increment a⟨u,H⟩²/(1+a⟨u,A⁻¹u⟩) in the AoS information equation.

**Estimator.** Split the seeds into two halves (j=1,2) so run noise is independent between them.
- Ĉ = ½[ĉov_c(α̂⁽¹⁾,d̂⁽²⁾)+ĉov_c(α̂⁽²⁾,d̂⁽¹⁾)]
- V̂ = ĉov_c(d̂⁽¹⁾,d̂⁽²⁾)
- τ̂²_α = ĉov_c(α̂⁽¹⁾,α̂⁽²⁾)
- v̂ comes from within-candidate task-level variance.

Covariances taken across halves are unbiased, which is the weak-experiment JIVE logic of Bibaut et al. [verified]. Standard errors use a delete-a-cluster jackknife over candidates, where candidates sharing an edit are deleted together.

**Decision rule.**
- **Admit for direction** if p(t_FM) ≤ α_j under α-investing (Foster–Stine [verified]) over *every* criterion ever proposed, the criterion fires on ≥5% of failing runs, and it never reads goal-check outputs.
- **Admit for measurement** if:
  - a one-sided test of Ĉ passes at 5%;
  - sign(Ĉ)=sign(γ̂);
  - the 80% jackknife lower bound of ΔR̂ is > 0.

  Testing the numerator alone stays valid when V is small (Anderson–Rubin logic [unverified]).
- **Direction-only until confirmed.** A criterion stays direction-only until ≥12 candidates have moved it (|d̂_c|>2se). The loop's own candidates then serve as the confirming data.

**Removal and merging** (rolling window of 3 rounds):
- **Backward:** re-screen f_k given all the others, and drop it after two consecutive |t|<1.5.
- **Spanned:** if R²(f_k|others)>0.9, merge the pair and keep the member with the larger confirm t. A factor is redundant iff its alpha on the others is 0.
- **Saturated:** if Var(f_k) on the current frontier ≈ 0, remove it from the reward and keep it as a regression monitor. A flat reward teaches nothing (Razin et al. [verified]).
- **Decayed or paradoxical:** if β̂_post/β̂_pre<0.5 or Ĉ flips sign, retire the criterion and re-audit any inherit decision that relied on it. This is the rubric analogue of McLean–Pontiff decay [verified].

## 4. Loop
```
R ← seed checks: completed_within_budget, steps_used, exec_error_rate,
    redundant_docs_lookups, default_code_steps
D ← paired runs: incumbent + BOS_EDITS_OFF ablations
for round r = 1..8:
  fit ĥ_R (task FE, seed cross-fit); ε̂ ← Y − ĥ_R                 # gradient
  P ← same-task won/lost pairs matched on ĥ_R, largest |ε̂|  (proposal fold)
  8 LLM calls on P → FailureMechanism + python check f_m
  each f_m: drop dead/leaky/spanned; screen on test fold; α-investing
  each admitted k: score_k = β̂_k · headroom_k · TC_k     # chain rule: E[ΔY | push k]
      headroom_k = E[(f̄_k^won − f_k)_+ | failing runs];  TC_k ~ Beta (Thompson)
  k* ← argmax sampled score
  proposer ← (k*, evidence runs)   [control arm: token-matched text]
  ≤4 edits (best-of-n cap, Gao et al. [verified])
  Discovery eval, paired with incumbent; π_t ∝ sd_t(paired contrast),
      20% uniform floor, IPW; always include tasks where f_{k*} fires
  TC_{k*} ← success iff d̂_c(f_{k*}) > 1 se            # dense feature, cheap
  confirm tests for direction-only criteria that now have movers
  top candidate by δ̂_c(λ̂) → Validation × 2 seeds
  inherit iff AKM hybrid lower bound (paired won; G-sign co-primary) > 0  [verified]
  removal/merge pass
```
Boosting moves from general to edge-case criteria on its own:
- **Early:** the first criteria are broad (budget efficiency).
- **Later:** later criteria fire on small subsets. The √breadth law makes them costlier to admit, which is the correct price.

## 5. What can be proven
**P1 (risk-optimal admission).**
- *Assumptions:*
  - a Gaussian local model for (α̂_c, Δh̄_c);
  - candidates exchangeable given their edits;
  - run noise independent across seed halves;
  - h_R fitted on a separate fold.
- *Claims:*
  - (i) The R and ΔR formulas above hold, and ΔR<0 whenever Cov(α,d)=0. A criterion that explains only luck therefore strictly hurts measurement, however large its same-run IC.
  - (ii) Ĉ and V̂ are unbiased, and Ĉ/se→N(0,1) under H₀ as m→∞, with no condition on V.
  - (iii) The Schur-complement equivalences with Barillas–Shanken and Sherman–Morrison hold.
- *Proof:* empirical-Bayes algebra, block inversion, and a U-statistic CLT. About 2–3 weeks.

**P2 (under transport, a nonzero screen is necessary).**
- *Assumption:* E[Y|S,f,X,t,c] = h(S,X,t)+γf̃ for all c.
- *Claims:*
  - Then α_c=γd_c, so Cov_c(α,d)≠0 ⇒ γ≠0 ⇒ partial IC≠0.
  - The screen estimates γ with variance O(1/T) over T≈100 task clusters, versus O(1/m) for the confirm stage. That justifies screening first and confirming second.
  - Corollary: if each admitted criterion explains ≥κ of the current τ²_α, then τ²_α(K) ≤ (1−κ)^K·τ²_α(0), the greedy boosting rate (Friedman 2001 [unverified]).
- *When transport fails* (the surrogate paradox), the sign check and λ̂→1 detect it, and the estimator falls back to the outcome. About 1 week.

**P3 (online validity).**
- *Assumptions:* disjoint proposal and test folds, and uniformly valid double-selection t-statistics (Belloni–Chernozhukov–Hansen [unverified]; FGX).
- *Claim:* α-investing controls mFDR ≤ α over the unbounded, adaptively generated stream of LLM criteria.
- *Proof:* composition of known results. About 1 week.

No regret bound is claimed; that would not be realistic in 4 months.

## 6. Experiments (≈540 passes at ~20/day for our share, plus 30% slack)
**E0 (weeks 1–2, ~12 passes).**
- Close the remaining default-code path.
- Log per-step features.
- Run bare 27B and the incumbent on Discovery and Validation × 2 seeds; this regenerates the missing per-task files.

**E1: measurement (weeks 2–6, ~140 passes).**
- *Corpus:* 24 candidates, run on Discovery and Validation × 2 seeds, plus a third seed for 10 of them:
  - ~10 BOS_EDITS_OFF ablations;
  - planted effects: step budget 20/25/30 and tool-output truncation;
  - 3 no-op nulls;
  - discovered patches.
- *Comparison:* decision accuracy on the planted effects, plus split-seed agreement, for:
  - paired won;
  - mean G;
  - G sign test;
  - fixed hand rubric;
  - rubric admitted naively (same-run correlation with won, or RLER std);
  - AgentPRM-style LLM progress judge;
  - random criteria;
  - ours.
- *Offline:* AUROC of step-10/15 process features for final won, against 0.56–0.70 for G@15.
- **Gate G1 (week 6, pre-registered):**
  - (a) ≥3 LLM criteria pass both screen and confirm;
  - (b) the shrinkage estimator gives n_eff ≥1.5× paired won, with ≥90% coverage on planted effects;
  - (c) naively admitted criteria pass confirm less often than ours.

  If (b) fails, drop the measurement role. If (a) fails, stop and publish the screen-versus-confirm negative result.

**E2: evolution (weeks 6–13, ~360 passes).**
- *Arms:* no rubric (raw failures), fixed seed rubric, evolving rubric with naive admission, and ours.
- *Scale:* 2 loop replicates × 8 rounds × (4 Discovery candidates + ~1.5 Validation confirms), plus a token-matched-control arm (1 replicate).
- *Pairing:* common random numbers across arms.
- **Gate G2 (after round 4):**
  - TC for ours ≥0.5, versus ≤0.3 for the token-matched control;
  - Validation won, ours minus no-rubric, ≥+4pp, with the sign agreeing on G.

  If it fails, write the E1 paper.

**E3 (week 14, ~30 passes).** Run each arm's final harness on the sealed test × 3 seeds, with AKM confidence intervals.

**Optional second environment:** an offline replication of E1 only.

**Headline plots.**
1. Screen t against confirm t for every proposed criterion, ours versus naive.
2. τ̂²_α and firing breadth by round (the boosting curve).
3. Minimum detectable effect against passes, for each measurement method.
4. Validation success against cumulative passes, plus sealed-test bars.
5. β̂ before versus after admission (decay).

## 7. The IC question
- **No free power.** On a single cross-section, the Pearson IC t-statistic, r√(n−2)/√(1−r²), *is* the OLS slope t-statistic. "Tiny MSE difference, significant IC" is just R²=IC²: an IC of 0.1 explains 1% of variance, yet t≈IC·√N.
- **What is genuinely gained:**
  1. **Blocking.** Demeaning removes the task factor. The ratio of paired to unpaired variance is 1−(between-task share): 0.354=1−0.646 for won and 0.54≈1−0.462 for G, exactly as observed.
  2. **Rank robustness.** G's noise consists of all-or-nothing jumps. The Pitman ARE of rank and sign tests over the t-test exceeds 1 under that kind of contamination: observed power at n=50 was 0.89 versus 0.71. Under normality, Spearman and Wilcoxon lose about 5–9% and the sign test about 36%.
  3. **Breadth.** IR≈IC·√BR (Grinold [verified]), where BR counts effectively independent task×candidate contrasts, clustered by family. Reaching t=3 at IC 0.1 needs about 900 of them.
  4. **Ordering.** Selection needs only ranks, and BTL on discordant within-task pairs is the likelihood form of within-task IC.
- **Where IC enters this framework:**
  - in the screen, as the partial rank IC with the residual;
  - in the confirm stage, as the split-seed cross-candidate IC between α and d.
- **What to avoid.** Avoid same-run IC with won, because it mixes signal with luck (P1(i)).
- **Transfer coefficient.** The full law is IC·TC·√BR, and dead-hook proposals have TC≈0. That is why TC is estimated online and enters score_k.

## 8. Failure modes
1. **Transport fails** (for example, Verification edits burn the step budget). It is detected by the sign flip and λ̂→1, and the estimator falls back to the outcome.
2. **Too few candidates.** With m≈24–60 the confirm stage is underpowered. Planted effects, low-rank pooling across families, and direction-only admission mitigate this. If E1 confirms nothing, the measurement claim dies.
3. **One binding factor.** 75–88% of failures never call complete_task, so boosting may stall after the budget-efficiency criteria. The result would then be that the method finds the binding constraint and rejects answer-format criteria (3–6 tasks/50). That is publishable, but the edge-case story would weaken.
4. **Mechanical association.** Completion ≈ won, so the same-run IC of +0.69 is partly mechanical. Completion stays direction-only unless it passes confirm.
5. **Default-code confound** (11/50 tasks). It is a mandatory control and stratifier; otherwise any parse criterion will appear to "explain" alpha.
6. **Novelty risk.** Yazdani et al. 2609.35646 [verified] select IRT rubric criteria by Fisher information for a scalar score. We value criteria by the decision-level alpha they explain and evolve them at the harness level, and the paper must say so explicitly.

**How this uses the empirical check:**
- **Two-stage admission.** An MDE of 17pp at n=50 makes validating each criterion by downstream success infeasible, which is why admission has two stages.
- **Seed rubric.** The observed ordering complete_task ≫ steps > exec_error ≫ docs lookups becomes the seed rubric. Whether it holds on a second seed has not been tested.
- **Truncated runs.** Truncated-G proxies are ruled out (G@10 = 0), so any value from truncated runs must come from process criteria; E1 tests this.
- **Allocation.** About 2/3 of tasks behave deterministically, so allocation uses π_t ∝ sd_t with IPW (roughly 3× cheaper). That is exactly the non-uniform sampling setting of the AoS paper.