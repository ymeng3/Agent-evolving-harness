## Findings

### Part 1: criteria for choosing what to measure

- **Rainforth, Foster, Ivanova, Bickford Smith 2024, *Stat. Sci.* 39(1), arXiv 2302.14545 [verified]**, with **Foster, Ivanova, Malik, Rainforth, ICML 2021, arXiv 2103.02438 (DAD) [verified]**
  - What it gives: expected information gain EIG(d) = I(θ; y | d), nested-MC and variational estimators, and amortized adaptive design policies.
  - Mapping: the design d is "which rubric dimension, or which (candidate, task) cell, to score next". Under a Gaussian/Laplace approximation, EIG = ½ log det(I + Σ^{1/2} F_new Σ^{1/2}). So EIG is a Fisher-information increment.
  - Caveat: aim it at the functional ψ (the candidate lift), not all of T*. Untargeted EIG rewards learning nuisance cells.

- **Fisher increment inside your AoS framework (my derivation, not a citation)**
  - A new channel with information G_r gives A' = A + P_T G_r P_T.
  - For a rank-one channel a·uu^T (u projected onto the tangent space), Sherman–Morrison gives:
    **ΔV_eff = a⟨u, H⟩² / (1 + a⟨u, A⁻¹u⟩)**, where H = A⁻¹P_TΓ is your efficient-influence direction.
  - So a dimension is worth adding only if its score direction lines up with H, the "gradient" of the target functional.
  - Generic dimensions ("be careful") load on the general-ability direction that won and G already pin down, so ⟨u, H⟩ ≈ 0. This is a formal account of why rubric v1/v2 failed.

- **Kallus & Mao, *JRSSB* 87(2) 2025, arXiv 2003.12408 [verified]**: the exact difference in semiparametric efficiency bounds for the ATE with and without surrogates, with no surrogacy assumption.
- **Angelopoulos, Duchi, Zrnic, PPI++, arXiv 2311.01453 [verified]**: power-tuned estimator mean_n(Y − λf) + λ·mean_N(f), with λ* ∝ Cov(Y, f)/Var(f). It is never worse than the classical estimator.
- **Athey, Chetty, Imbens, Kang, surrogate index, NBER w26463 / *REStud* 2026 [verified]**: the Prentice condition Y ⊥ W | S.
- Mapping for these three:
  - Used as an auxiliary outcome, a rubric dimension can only shrink the variance of the effect on won, by about (1 − ρ²_partial). It cannot create signal.
  - Used as a target, it must pass a surrogacy (Prentice) test on the Validation families.

- **Frazier, Powell, Dayanik 2009, *INFORMS J. Comput.* 21(4) [verified]**: knowledge gradient KG(x) = E[max μⁿ⁺¹ − max μⁿ | x], in closed form under correlated normal beliefs.
  - Mapping: value a measurement by how much it improves the promote/inherit decision. The correlations come from the low-rank loadings. This beats EIG when the loop's goal is to choose, not to estimate.

- **Garivier & Kaufmann, COLT 2016, arXiv 1602.04589 [verified]**: E[τ_δ] ≥ T*(μ) log(1/δ), with T*⁻¹ = sup_w inf_{λ∈Alt} Σ w_a KL(μ_a, λ_a); Track-and-Stop attains it.
- **Russo, *Oper. Res.* 68(6) 2020, arXiv 1602.08448 [verified]**: top-two sampling attains the optimal exponent for posterior convergence.
- Mapping for both:
  - For Gaussian (won, G, rubric) vectors, the per-sample KL is ½Δμᵀ Σ⁻¹ Δμ.
  - The drop in T* from adding a dimension is a decision-relevant "value of a new reward".
  - Top-two sampling gives a rule for allocating the 35-45 passes/day.

- **Peng, Long, Ding, *TPAMI* 2005 (mRMR) [verified]; Fleuret, *JMLR* 2004 (CMIM) [verified]; Brown, Pocock, Zhao, Luján, *JMLR* 13 2012 [verified]**
  - What they give: Brown et al. show these heuristics approximate conditional-likelihood maximization, with criterion I(X_k;Y) − βΣI(X_k;X_j) + γΣI(X_k;X_j|Y). JMI works best at small n.
  - Mapping: score a candidate dimension by I(r_new; Y | R_existing). At n ≈ 50, use the Gaussian form, −½ log(1 − ρ²_{Yr·R}), which is a partial IC.
  - Y must be the within-task paired contrast, not the level of won.

- **Ma et al., EDDI, ICML 2019, arXiv 1809.11142 [verified]; Covert et al., ICML 2023, arXiv 2301.00557 [verified]; Gadgil, Covert, Lee, ICLR 2024, arXiv 2306.03301 [verified]**: greedy conditional-MI feature acquisition with amortized estimators.
  - Mapping: decide, per trajectory, which rubric checks are worth paying the judge to run.

- **Tishby, Pereira, Bialek, arXiv physics/0004057 [verified]**: min I(X;Z) − βI(Z;Y).
  - Mapping: the rubric is a compressed code Z of the trajectory X that keeps information about Y (held-out success, or which edit fixes the failure).
  - This is conceptual only; it is hard to estimate at n ≈ 50. **Auto-Rubric (Xie et al., arXiv 2510.17314) [verified]** compresses a criteria pool with a coding-rate objective.

- **Rubric and LLM-evaluation work**
  - **Fluid Benchmarking, COLM 2025, arXiv 2509.11106 [verified; authors unverified]**: 2PL IRT with Fisher item selection, I_j(θ) = a_j² p_j(1 − p_j).
  - **Yazdani et al., "Rubric Rewards from Item Response Theory", arXiv 2609.35646 (28 Sep 2026) [verified]**: 2PL over criterion verdicts, discrimination and difficulty predicted from the criterion text, adaptive Fisher criterion selection, online EM. **This is the nearest competitor, posted two days ago.**
  - **Razin et al., NeurIPS 2025, arXiv 2503.15477 [verified]**: if reward variance under the policy is low, the objective is flat no matter how accurate the reward is.
  - **Tyagi et al., POW3R, arXiv 2605.20164 [verified]**: saturated or unreachable criteria teach nothing; weight criteria by rollout contrast.
  - **Rezaei et al., OnlineRubrics, arXiv 2510.07284 [verified]**: criteria elicited from pairwise comparisons, a natural link to your Bradley-Terry-Luce setup.
  - **Gunjal et al., Rubrics as Rewards, arXiv 2507.17746 [verified]**.
  - Evaluation noise: **Heineman et al., "Signal and Noise", NeurIPS 2025, arXiv 2508.13144 [verified]**; **Miller, arXiv 2411.00640 [verified]** (paired and clustered SEs; clustered SEs can exceed naive ones by more than 3x); **Kossen et al., "Active Testing", ICML 2021, arXiv 2103.05331 [verified]**.

### Part 2: quant analogues

- **What IC does and does not buy statistically**
  - On one cross-section, the t-statistic for a Pearson IC is r√(n−2)/√(1−r²). That is identical to the OLS slope t-statistic, so **IC gives no extra power over a slope test on the same demeaned data.**
  - The "tiny MSE" effect comes from R² = IC². For example, IC 0.05 gives R² of 0.25%, yet t ≈ IC·√N_eff ≈ 2.2 at N_eff = 2000.
  - What IC practice really provides:
    - Cross-sectional demeaning, which is blocking. For you, the common factor is task difficulty, which dwarfs the 1-7pp effects.
    - Rank-IC robustness to heavy tails and monotone transforms, at a cost of about 9/π² ≈ 0.91 efficiency under normality.
    - A focus on ordering, which is what selection needs.
- **Clark & West, *J. Econometrics* 138 2007 [verified]**: under a nested null, the larger model's MSPE is inflated by estimation noise. Their MSPE-adjusted statistic corrects this. This is the formal reason raw MSE comparisons look like "no difference".
- **Campbell & Thompson, *RFS* 21(4) 2008 [verified]** and **Gu, Kelly, Xiu, *RFS* 33(5) 2020 [verified]**: tiny out-of-sample R² can still mean large economic gains.
- **Fama & MacBeth, *JPE* 81(3) 1973 [verified]**: per-period slopes, t = mean/(sd/√T). Relatedly, ICIR = mean(IC)/sd(IC) and t = ICIR·√T.
  - Mapping: a "period" is a task; the "cross-section" is the candidates run on it.
- **Grinold, *JPM* 15(3) 1989 [verified]; Clarke, de Silva, Thorley, *FAJ* 58(5) 2002 [verified]**: IR ≈ TC·IC·√BR.
  - IC is the correlation between the rubric's diagnosis and the realized fix.
  - BR is the number of effectively independent bets, clustered by task family.
  - TC is the correlation between the intervention the rubric implies and what the proposer actually builds. **Dead-hook candidates are TC ≈ 0.**
- **Feng, Giglio, Xiu, *JF* 75 2020 [verified]**: double-selection LASSO (Belloni-Chernozhukov-Hansen 2014 [unverified]).
  - Method: LASSO the outcome on existing factors, LASSO the new factor's exposure on existing factors, then run OLS on the union. Inference on the new factor stays uniformly valid despite selection mistakes.
  - Finding: most new factors turn out redundant.
  - Mapping: an exact template for testing an increment over a high-dimensional set of existing dimensions. It is a Neyman-orthogonal score, so it sits in your own area.
- **Barillas & Shanken, *RFS* 30(4) 2017 and *JF* 2018 [verified]**
  - What they give: only mutual spanning between models matters; test assets are irrelevant; the Bayes factor follows from the GRS F-statistic; posterior probabilities over all factor subsets.
  - Underlying identity (GRS 1989 [unverified]): Sh²(F∪f) − Sh²(F) = α_f²/σ²(ε_f). This is the same Schur complement as the Fisher increment in Part 1.
  - Mapping: residualize the new dimension on the existing ones; its value is (residual effect)² / (residual variance).
- **Kozak, Nagel, Santosh, *JFE* 135 2020 [verified]**: shrink harder along low-eigenvalue principal components. This is the low-rank prior applied to rubric weights.
- **Harvey, Liu, Zhu, *RFS* 29(1) 2016 [verified]**: require t > 3 after multiple-testing correction.
- **Foster & Stine, *JRSSB* 70 2008, α-investing [verified]**: online mFDR control for a stream of hypotheses. It fits admitting rubric dimensions one at a time.
- **McLean & Pontiff, *JF* 2016 [verified]**: returns are 26% lower out of sample and 58% lower after publication. Expect a similar "rubric decay" once a dimension starts steering proposals.
- **LLM and RL alpha mining**
  - **AlphaGen (Yu et al., KDD 2023, arXiv 2306.12964) [verified]**: the reward is the *increment in the combination model's IC* when the new alpha joins the pool. This target beats both single-alpha IC and mutual IC.
  - **AlphaAgent (Tang et al., KDD 2025, arXiv 2502.16789) [verified]**: an AST-similarity originality penalty, LLM-judged alignment between hypothesis and factor, and complexity control against decay.
  - **Alpha-GPT (Wang et al., arXiv 2308.00016) [verified]**: idea-to-formula generation plus genetic-programming refinement; little admission math.
  - **R&D-Agent(Q) (Li et al., NeurIPS 2025, arXiv 2505.15155) [verified]**: a hypothesis, code, backtest, feedback loop scored by IC and ICIR. It is the closest architectural twin to your loop.

## Direct implications for the design

1. **One admission statistic with three equivalent readings:** ΔV_eff(ψ) by Sherman–Morrison, the Barillas–Shanken residual alpha², and the Gaussian conditional MI (partial IC). All three can be computed offline from the paired logs you already have (won, G, trajectories), so screening dimensions costs no GPU passes.
2. **Outcome:** use the within-task demeaned paired contrast, with G primary and won secondary. Compute rank IC across candidates within each task, aggregate with Fama-MacBeth / ICIR across tasks, and cluster by family.
3. **Incremental test:** run double selection with these controls: existing dimensions, hook flags, family fixed effects, and a parse-fallback indicator. The last one neutralizes the fallback-credit confound.
4. **Threshold:** apply α-investing or BHY over every dimension ever proposed, not just the ones kept.
5. **Second gate is TC:** measure downstream proposal gain against a token-matched control, as in your frozen v3 plan. A dimension's worth is IC × TC × √BR.
6. **Budget:** t ≈ IC·√N_eff, so IC 0.1 needs about 900 effective contrasts for t = 3. Use top-two or Track-and-Stop to allocate passes. Use Fisher-adaptive (IRT) criterion selection to cut judge cost, and drop criteria that almost always pass or almost always fail.
7. **Robustness:** apply a decay haircut measured on the Validation families, plus an originality penalty against existing dimensions.

## Gaps nobody has filled

- No work values a new evaluation dimension by how much it reduces the efficiency bound of a decision functional under low-rank (tangent-space) structure. The IRT rubric paper (Yazdani et al.) uses Fisher information only for a scalar quality score.
- No work separates a dimension's measurement value (IC) from its actionability (TC) when a proposer drives the search without gradients. Razin et al. and POW3R cover only gradient-based RL.
- No work applies online false-discovery control to LLM-generated rubric dimensions.
- No work estimates how much a rubric dimension's predictive power decays once it is used for selection.
- Pairwise rubric elicitation (OnlineRubrics) has no efficiency theory. Your Bradley-Terry-Luce machinery fits that gap directly.