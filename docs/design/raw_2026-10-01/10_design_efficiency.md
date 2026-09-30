# Rubric dimensions as auxiliary information channels: a targeted efficiency criterion for self-evolving rubrics

## 1. Thesis
A rubric dimension is a cheap extra observation channel on the same latent capability tensor that produces the expensive outcome. It is worth exactly the reduction ΔV_k it makes in the efficiency bound of the *decision functional* (a candidate's held-out lift, or a capability deficit). That reduction equals the squared alignment between the dimension's *innovation* and the functional's least-favourable direction H, divided by its partial noise. The rubric is used only to reduce variance, inside a cross-fitted one-step estimator whose gold sample is randomized by design. A wrong rubric therefore costs precision, never bias.

**How this avoids credit assignment.** Nothing is estimated per token or per component. There are two targets:
- the candidate-level held-out lift ψ_c, which decides inheritance;
- a low-dimensional deficit map, which sets the direction of new proposals.

Components appear only as covariates on the candidate mode. A component contrast is just another Γ. Its bound V_eff(Γ_edit)/n tells you *in advance* whether that credit question can be answered at your budget. For every-step components it usually cannot, which matches POSTMORTEM_LOOP1.

## 2. Setup
- **Runs.** Tasks t ∈ T_D ∪ T_V ∪ T_test, each with a family f(t). Candidates c are edit sets with parent p(c).
  - A run (c,t,ω) produces a trajectory τ, a primary outcome Y ∈ {won, G}, and rubric scores S(τ) ∈ R^K.
  - Rubric scores are either programmatic checks on the logs or atomic judge items written in FailureMechanism form.
  - Channels are k = 0 (Y) and k = 1..K (rubric).
- **Latent tensor.** Θ* ∈ R^{C×F×(1+K)}, with E[Z_k|c,t] = g_k(Θ*_{c,f(t),k} + β_{t,k}).
  - The task nuisance β is removed by pairing.
  - Θ* has Tucker form 𝒢×₁U×₂V×₃Λ with r₃ ≤ 5 capability factors (Planning…Verification).
  - Row λ_k of Λ is dimension k's capability loading.
- **Observations.** Both kinds fit the AoS form.
  - (a) Graded runs: X = e_c⊗e_f⊗e_k. The within-run noise covariance Σ across channels is estimated from seed replicates.
  - (b) Pairwise judge comparisons of τ_c against τ_{p(c)} on criterion k, same task and seed. These follow BTL with X = (e_c−e_{p(c)})⊗e_f⊗e_k and I(η) = σ(η)(1−σ(η)). This is the AoS model with one extra mode for criteria.
- **Sampling.** We control the design over (candidate, task, channel, gold). The propensities are therefore known, and the AoS inverse-probability-weighting (IPW) results apply exactly.
- **Targets.** ψ = ⟨Γ,Θ*⟩.
  - Lift: Γ_c = (e_c−e_{p(c)})⊗w_V⊗e_0.
  - Deficit: Γ_{f,j}.
  - Moving from general ability to an edge case only changes w_V, from uniform weights to weight on a single family.
- **Bound.** For a set of channels D:
  - ⟨G_D U,W⟩ = E[d_D(U)ᵀΣ_DD⁻¹d_D(W)], with d_k(U) = g_k′⟨U,X_k⟩;
  - A_D = P_T G_D P_T, H_D = A_D⁻¹P_TΓ, V_D = ⟨P_TΓ,H_D⟩.

## 3. The criterion
**Information increment (P1).** Adding channel k adds the efficient information B_{k|D} = P_T E[σ_{k|D}⁻¹ ν_k⊗ν_k] P_T, after a Schur complement against k's own loading λ_k.
- The innovation is ν_k = d_k − Σ_{kD}Σ_DD⁻¹d_D.
- The partial noise variance is σ_{k|D} = Σ_kk − Σ_{kD}Σ_DD⁻¹Σ_{Dk}.

Then

ΔV_k = ⟨P_TΓ, A_D⁻¹P_TΓ⟩ − ⟨P_TΓ,(A_D+B_{k|D})⁻¹P_TΓ⟩ ≈ ⟨H_D, B_{k|D}H_D⟩,

and for a rank-one channel, ΔV_k = a⟨u,H_D⟩²/(1+a⟨u,A_D⁻¹u⟩).

How to read this:
- **Gradient.** H_D is the Riesz representer of ψ in the information metric, so ⟨u,H_D⟩ measures how well the dimension aligns with that gradient.
- **Information gain.** ½log(V_D/V_{D∪k}) is the expected information gain targeted at ψ.
- **Noise coupling.** If S = Y + noise, then ν_k = 0, even though S correlates strongly with Y within a run.
  - So same-run correlation is not evidence of value. In the empirical check it is ρ ≈ 0.8 for G and for complete_task.
  - Generic dimensions ("be careful") load on the general factor that Y already pins down, so ⟨u,H_D⟩ ≈ 0.
- **Worked example.** Let S = completed and Y = completed×correct, where answers are correct with probability q. Suppose edits change only the completion rate p.
  - The effective-sample multiplier is then (1−pq)/(q(1−p)) ≈ 1.44 at the logged values p ≈ 0.6, q ≈ 0.85.
  - This holds *only if* edits leave q unchanged. The audit below tests exactly that.

**Workhorse closed form.** This is the candidate-level, linear-Gaussian version, and it is what we actually compute.
- L_c is the true Validation lift.
- Z_c ∈ R^{1+K} is the vector of paired lifts on Discovery. Discovery Y is channel 0.
- The gold value L̂_c = L_c + e_c is observed with known probability π_c.
- Partial residuals: Z̃_{k·D} = Z_k − B_D Z_D and L̃ = L − a_D Z_D.

Then

I_k := Cov(L̃,Z̃_{k·D})²/Var(Z̃_{k·D}) = σ_L²(1−R²_D)ρ²_{Lk·D},  ΔV_k = E[(1−π)/π]·I_k.

This is Kallus & Mao, Cor. 2.1 [verified].
- I_k does not depend on the design; the odds (1−π)/π are the loop's design choice.
- I_k is also the drop in the posterior variance Var(L_c|Z_c), which is what drives decisions about individual candidates.
- Split Var(Z̃) = λ + ξ into between-candidate signal λ and seed-replicate noise ξ. Then ρ² = alignment²·λ/(λ+ξ).
- This is the proxy-quality measure of Tripuraneni et al. [verified], and it equals the Barillas–Shanken residual α²/σ²(ε) [verified].

**Estimator.**
- Cross-fit (â, B̂) on other lineages.
- Ĉ_k = Σ_gold(R_c/π_c) L̃̂_c Z̃̂_{k·D,c} / Σ(R_c/π_c). Both sides are partialled out, so the estimator is Neyman-orthogonal (Feng–Giglio–Xiu double selection [verified]).
- σ̂²_{k·D} uses all candidates.
- Validation noise and Discovery noise come from disjoint tasks. So there is no weak-signal covariance bias, the problem that Bibaut et al. [verified] correct for.
- Debiased square: Î_k = (Ĉ_k² − ŝe_k²)/σ̂²_{k·D}. The standard error comes from a jackknife clustered by lineage, because candidates share edits.
- Confidence interval: Fisher-z on ρ_{Lk·D}.

**Admission.** Admit dimension k only if all three hold:
1. t_k = Ĉ_k/ŝe_k clears an α-investing threshold (Foster–Stine [verified]) applied over *all* proposed dimensions. This controls the marginal false discovery rate (mFDR).
2. Î_k/(σ_L²(1−R²_D)) ≥ κ_k, where κ_k = (judge cost per run) / (run cost).
3. It passes the Prentice / surrogate-paradox audit [Prentice verified; VanderWeele verified]:
   - the sign of its coefficient agrees in at least 2/3 of the Validation family groups;
   - the test of E[L−h(Z)] = 0 does not reject.

**Removal and merging.**
- Each round, compute the leave-one-out value I_{j|R∖j} for every dimension j in the rubric R.
- Retire j if the upper end of its CI stays below κ_j for two rounds in a row. A dimension's value drifts as the frontier of candidates moves (Razin et al. [verified]).
- Near-duplicates need no separate merge rule: each gets I ≈ 0 given the other, and the cheaper one is kept.
- Greedy admission by Î/cost is (1−e^{−γ})-optimal under weak submodularity (Das & Kempe 2011 [unverified]).

## 4. Loop
```
state: incumbent c*, run corpus, rubric R, index h, design log {π}
for round r:
  fit Θ̂ on channels R (AoS one-step); deficit map ψ̂_{f,j} ± CI for c*
  (f,j) ← argmax LCB(deficit) × task share
  # propose dimensions = functional-gradient step on V
  r_c = L̂_c − h(Z_c) on gold candidates
  proposer sees same-task/seed pairs of over- vs under-predicted candidates
      + won-vs-lost pairs in (f,j); returns atomic checks (trigger/evidence/counterevidence)
  score each new S_k on ALL logged τ (judge calls, 0 runs); admit/retire (§3)
  refit h: ridge-shrunk linear index on Z_R
  # propose harness edits
  n ≤ n* edits aimed at (f,j)                        # best-of-n law (Gao et al.)
  Discovery: live tasks first (Neyman n_t ∝ sd_t; deterministic tasks reused);
      pairwise judge vs parent only on TIED tasks (Y has ~0 Fisher info); win-rate = one more channel of Z_c
  gold: Validation run w.p. π_c ∝ sd(L|Z_c)·P(L_c>0|Z_c)/√cost, π_c ≥ 0.1   # Zrnic–Candès; AM-PPI
  ψ̂_c = h(Z_c) + (R_c/π_c)(L̂_c − h(Z_c))            # cross-fitted
  promote only with gold and winner's-curse-corrected LCB(L_c) > 0   # Andrews–Kitagawa–McCloskey
  audit gold residuals (mean, sign); if rejected: λ_PPI ← 0, flag dims
```
Proposing dimensions from residuals combines AlphaGen's increment-IC reward [verified] with the contrastive elicitation of OnlineRubrics [verified], here aimed at a specific target. The "downstream proposal gain" from the frozen v3 plan becomes a separate gate on direction (TC).

## 5. What can be proven
**P1. Information increment (2 weeks).** The identity in §3, with two corollaries.
- (i) No free lunch. Suppose the primary channel is variation-independent of the rubric channels and Y is observed on every run. Then ΔV_k ≡ 0 (Zellner SUR [unverified]; Kallus–Mao with r ≡ 1).
  - So any gain must come from shared low-rank structure (which is testable) or from Y being missing by design.
- (ii) The identity reduces to Kallus–Mao, and to PPI's factor 1−ρ²/(1+n/N).
- Proof: block Schur complement plus Woodbury on T. Realistic.

**P2. Goodhart-safe inference (3 weeks).** Assume known π_c ≥ π_min and cross-fitting.
- ψ̂^DR is unbiased for *any* index h, including one that has been hacked.
- It satisfies a CLT with variance V_gold − odds·(2Cov(L,h) − Var h) when π is constant. With PPI++ tuning this is never above V_gold, and it reaches V_eff(R) when the working model holds.
- It stays valid when candidates are generated adaptively, because the gold coin is flipped after c is fixed (martingale CLT).
- Proof reuses the AoS one-step and IPW theorems. Realistic.

**P3. Estimation value equals decision value (1 week).** Suppose (L_c, h(Z_c)) is jointly Gaussian over n exchangeable proposals and π is constant. Then E[L_{argmax h}] − E[L] = σ_L ρ_R e_n, where e_n ≈ √(2log n) and ρ_R² = (V_gold−V_R)/(odds·σ_L²).
- So admitting k raises the expected gain per round by σ_L e_n(ρ_{R∪k}−ρ_R), which is monotone in ΔV_k. This is Grinold's IR ≈ IC√breadth [verified], restated for selection.
- Corollary: heavy-tailed residuals L−h break the result (Kwa et al. [verified]). The tail index of the residuals is the diagnostic.
- Realistic. The case where the surrogate is learned and then optimized against remains an open limitation.

## 6. Experiments (about 450 passes, roughly 25–30 days of the shared box at 15–20 passes/day)

| Phase | Weeks | Passes | Content |
|---|---|---|---|
| A | 1–3 | ~40 | Finish the default-code fix. 3-seed replicates of the bare and incumbent harnesses on D and V, which give Σ̂ and the map of live tasks. 6 planted candidates with known sign (step budget 30→25 and 30→27, doc truncation, temperature, no completion hint) × 2 seeds × (D, V) |
| B | 3–7 | ~110 | 36 candidates × (2 Discovery seeds + 1 Validation run). About 25 programmatic and LLM-proposed dimensions, scored offline |
| C | 7–9 | 0 | Offline comparison with gold subsampled at π = 0.3 (details below) |
| D | 9–13 | ~270 | Live loop: 3 arms × 8 rounds. TC = paired gain of the induced proposals over the token-matched arm |
| E | 13–14 | ~30 | Sealed test: the final harness of each of the 3 arms plus the incumbent, 3 seeds |

**Phase C comparisons.**
- Evaluators: Discovery won/G with CUPED covariates; a fixed hand-written rubric; a holistic LLM judge; PRM promise/progress; random criteria.
- Admission rules: ours; same-run correlation with won; RLER top-std [verified]; Auto-Rubric log-det [verified].

**Phase D arms.**
- The ΔV rubric.
- No rubric (paired G sign test, Neyman allocation).
- Token-matched random criteria.

**Gates (pre-registered).**
- **G0 (week 3).** Both must hold, otherwise drop the measurement claim and keep allocation plus P1(i):
  - on the planted candidates, at least one dimension has t_k > 2 beyond Discovery Y/G;
  - judge comparisons on tied tasks match the planted sign at least 60% of the time.
- **G1 (week 8).** DR coverage of at least 90% on the planted effects, and V_{Y-only}/V_R ≥ 1.5. Kill the approach if V_{Y-only}/V_R < 1.2.
- **G2 (week 8).** Split the candidates in two. The Spearman correlation between Î_k on one half and the realized I_k on the other is at least 0.4, over at least 20 dimensions. Our admission rule also beats same-run correlation and random admission.
- **G3 (week 13, secondary).** Pass if either holds:
  - the ΔV arm is at least as good as no-rubric on Validation plus test (paired G sign test, one-sided p < 0.1);
  - it ties while using at least 30% fewer passes.

**Headline plots.**
1. Predicted vs realized variance reduction, per dimension.
2. Decision accuracy vs passes, per evaluator.
3. A scorecard per dimension: alignment, reliability, noise coupling.
4. Loop progress, with IC on the frontier and the retirement events.
5. Coverage of DR vs naive surrogate intervals. Naive coverage was 0% in Landesberg & Narayan [verified].

## 7. The IC question
In this setting IC is the right statistic for a precise reason. For a contrast functional, the efficiency gain from a new dimension is odds·σ_L²(1−R²_D)·(partial IC)². Here IC means the correlation across candidates between the rubric-predicted lift and the realized held-out lift, corrected for noise.

MSE on levels is dominated by directions orthogonal to H: the task factor (0.65 of won's variance is between tasks) and Bernoulli noise. So differences in MSE look tiny even when the partial IC is large enough to matter (compare Clark & West [verified]). Rank and sign versions are also robust to G's all-or-nothing jumps. On the planted effect, the sign test on G had power 0.89, against 0.71 for the mean test on G.

Caveats:
- The t-statistic of a Pearson IC equals the t-statistic of the slope on demeaned data, so IC adds no power beyond what blocking already gives.
- Weak effects shrink the IC across candidates unless the two noise sources are disjoint (different tasks or different seeds).
- "Breadth" counts independent lineage×family contrasts, not tasks.

## 8. Failure modes, and how they relate to the empirical check
1. **No dimension has innovation.** Same-run correlation is not the criterion.
   - Completion's ~1.44× gain holds only if edits leave answer accuracy unchanged.
   - The promising dimensions are those that carry noise Y lacks: step efficiency on completed runs, wasted exploration, and progress on tasks where both runs fail. Budget exhaustion accounts for 75–88% of failures.
   - If G0 fails, what remains is P1(i) plus allocation. The 2/3 of tasks that are deterministic give about a 3× saving. That makes for a smaller paper.
2. **Too few gold candidates.** With 36 candidates and π = 0.3, only a partial ρ of roughly 0.45 or more is detectable. Mitigations:
   - more breadth from families (C×F low rank);
   - planted candidates to widen Var L;
   - pooling the ALFWorld logs.
3. **Surrogate paradox.** For example, a Verification edit raises the verification score but burns steps. P2 keeps the estimate unbiased, the variance gain disappears, and the audit flags the dimension.
4. **Adaptivity.** IC on the frontier decays as the proposer optimizes toward h, as in McLean–Pontiff. P2 covers the gold correction but not this drift, which retirement handles empirically.
5. **No cheap truncated proxy.** G is 0 at step 10, so savings must come from sparse gold, judging on tied tasks, and allocating runs to live tasks.
6. **Default-code confound.** Default-code steps still affect 22% of tasks. A parse-fallback indicator goes into D so that no dimension gets credit for it.
7. **Nearest competitor.** The IRT rubric rewards of Yazdani et al. [verified] use Fisher information for a single quality score. We add four things:
   - value targeted at a decision functional (c-optimal design);
   - the Schur complement that removes noise coupling;
   - unbiasedness that comes from the design itself;
   - rubric and harness evolving together.

Sources I read:
- `C:/Projects/Cleanup_Archives_2026-08-27/Local_Latex_Files/Local_Latex_Files/AoS_LowrankLLMEvaluation/AoS_LowrankLLMEvaluation/aos_LowrankLLMEvaluation.tex` (Sec. 4: information equation, bound; Sec. 6.2: IPW)
- `C:/Projects/Cleanup_Archives_2026-08-27/Local_Latex_Files/Local_Latex_Files/Agent-evolving-harness/appworld/phase2/schema.py` (FailureMechanism fields)