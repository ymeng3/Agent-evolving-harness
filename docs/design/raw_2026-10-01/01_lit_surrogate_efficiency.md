## Findings

**A. Surrogacy: when a cheap dimension can stand in for the real outcome**
- **Prentice (1989, Stat Med 8:431) [verified].** Criterion: Y ⟂ T | S, meaning the surrogate carries the whole treatment effect. How it maps: for candidate c vs base, regress `won` on (T, S_rubric) over paired tasks. The remaining T-coefficient is the part of the effect the rubric misses. 1 − β_{T|S}/β_T is the "proportion of effect explained". Use this to audit each dimension, not as an objective.
- **Chen, Geng & Jia (2007, JRSSB 69:919); VanderWeele (2013, Biometrics 69:561) [verified].** The surrogate paradox: T raises S, S is positively associated with Y, and yet T lowers Y. Ruling it out takes three things: no direct T→Y path outside S, E[Y|S] monotone within each arm, and no unmeasured S–Y confounding. How it maps: a Verification edit raises the verification score, and verification correlates with winning across tasks, but it uses up the step budget and wins drop. This is the mechanism behind the earlier dead-hook, generic-dimension failure.
- **Athey, Chetty, Imbens & Kang (NBER w26463 / [1603.09326](https://arxiv.org/abs/1603.09326); RESTud 2025) [verified].** Surrogate index h(S,X) = E[Y|S,X], fitted where Y is seen. Under surrogacy plus comparability, the ATE on h equals the ATE on Y. Several short-term signals are fused by regression, not by hand weights. How it maps: the rubric vector is the input and h is the scalar reward.
- **Zhang, Zhao, Dimakopoulou, Le & Kallus (2023, [2311.11922](https://arxiv.org/abs/2311.11922)) [verified].** On 200 Netflix A/B tests, a linear index was about 95% consistent with direct long-term decisions but reached only 65–79% recall of true launches. How it maps: validate the rubric at the decision level (sign agreement, recall of truly good candidates).

**B. How much an auxiliary signal is worth for estimation (the quantity you asked for)**
- **Kallus & Mao ([2003.12408](https://arxiv.org/abs/2003.12408); JRSSB 87:480, 2025) [verified].** Assumes only MAR labelling r(t,X), no surrogacy. Corollary 2.1: V_noS − V_S = E[Σ_t (1−r(t,X))/(e_t(X) r(t,X)) · Var(E[Y(t)|X,S(t)] | X)]. For adding one dimension S_{k+1}, ΔV = E[Σ_t odds_t · Var(μ_{k+1} − μ_k | X)]. That is the odds-weighted increase in explained variance, i.e. odds × residual variance × partial R². Two consequences:
  - (a) the gain is exactly 0 when r = 1;
  - (b) the gain grows with the share of units whose Y is missing.
- **PPI (Angelopoulos, Bates, Fannjiang, Jordan, Zrnic 2023, [2301.09633](https://arxiv.org/abs/2301.09633)); PPI++ (Angelopoulos, Duchi, Zrnic 2023, [2311.01453](https://arxiv.org/abs/2311.01453)) [verified].** Estimator θ̂ = Ȳ_n + λ(f̄_N − f̄_n), with λ* = Cov(Y,f)/((1+n/N)Var f). Then Var = (σ_Y²/n)(1 − ρ²/(1+n/N)), so n_eff = n/(1 − ρ²/(1+n/N)). With a vector f, ρ² becomes R², and one extra dimension is worth its partial R². This is the "1−ρ²" rule.
- **CUPED (Deng, Xu, Kohavi, Walker, WSDM 2013); Robins, Rotnitzky & Zhao (1994, JASA 89:846) [verified].** Control variates and AIPW multiply variance by (1−R²), but only with pre-treatment covariates. How it maps: paired evaluation (0.4×) is the one-covariate case. Adding base-harness `won`/G over several seeds, task family, and bare-model trajectory features as covariates is free.
- **Stratified PPI (Fisch et al., NeurIPS 2024, [2406.04291](https://arxiv.org/abs/2406.04291)) [verified].** A separate λ_k per stratum plus Neyman allocation, because judge quality varies by stratum. Strata here would be task family × capability.
- **Active inference (Zrnic & Candès, ICML 2024, [2403.03208](https://arxiv.org/abs/2403.03208)) [verified].** Label with probability π(x) ∝ √E[(Y−f(X))²|X], then IPW-correct. **AM-PPI (Brawand et al. 2026, [2605.08429](https://arxiv.org/abs/2605.08429)) [verified]** extends this to several predictors with different costs: π*_I(x) = u_I(x)/√(nμc). How it maps: which (candidate, task) cells get real A800 runs. This gives an information-gain rule for spending runs that comes from theory rather than a heuristic.
- **Judge as surrogate:**
  - Boyeau et al. (ICML 2025, [2403.07008](https://arxiv.org/abs/2403.07008)) [verified].
  - Chen, Lu, Li, Guo, Li (2026, [2601.05420](https://arxiv.org/abs/2601.05420)) [verified]: PPI-type and EIF estimators have strictly smaller asymptotic variance than Rogan–Gladen misclassification correction, under their stated conditions.
  - Landesberg & Narayan (2025, [2512.11150](https://arxiv.org/abs/2512.11150)) [verified]: naive judge confidence intervals had 0% coverage. Their fix is to calibrate on an oracle slice, run a transport audit for each policy, and refuse a claim when a policy fails the audit.
  - Chatzi et al. (NeurIPS 2024, [2402.17826](https://arxiv.org/abs/2402.17826)) [verified]: PPI for pairwise-preference rankings. This is the bridge to the BTL model in your AoS paper.

**C. The IC view: how well a proxy tracks true effects across candidates**
- **Tripuraneni, Richardson, D'Amour, Soriano, Yadlowsky (KDD 2024, [2309.07893](https://arxiv.org/abs/2309.07893)) [verified].** Proxy quality corr(Δ^N, Δ̂^P) = corr(Δ^N, Δ^P)/√(1 + Ξ^PP/Var Δ^P), i.e. alignment × signal-to-noise. This is exactly the quant IC. Composite weights solve a Sharpe program, max_w w′Cov(Δ^N, Δ^P)/√(w′(Λ+Ξ)w), with Λ denoised by a hierarchical model. A new dimension is worth adding if and only if it raises the maximal Sharpe.
- **Jeunen & Ustimenko (KDD 2024, [2402.03915](https://arxiv.org/abs/2402.03915)) [verified].** Weights w ∝ (Σ^A+Σ^B+εI)^{-1}(μ^A−μ^B), averaged over past experiments. A log-p-value loss penalises wrong-sign (type-III) errors. They report up to 78% more power than the North Star metric.
- **Bibaut, Chou, Ejdemyr, Kallus (KDD 2024, [2402.17637](https://arxiv.org/abs/2402.17637)) [verified].** When effects are weak, the covariance of estimated effects across experiments is biased by noise. JIVE and LIML (weak-IV tools) correct it. Your regime (true effects 1–7pp against ±8pp noise) is exactly the weak-experiment case. Use cross-covariances between split tasks or split seeds.
- **Grinold (1989, J. Portfolio Mgmt) [verified].** IR ≈ IC·√breadth. This is why MSE shows nothing while IC is significant. MSE is dominated by the irreducible Bernoulli variance of `won`. IC tests only covariance or ranking, and its t-statistic grows with √(number of independent contrasts). Here breadth = candidates × strata.

**D. Goodhart when the surrogate is optimised**
- **Gao, Schulman, Hilton (ICML 2023, [2210.10760](https://arxiv.org/abs/2210.10760)) [verified].** Gold score as a function of d = √KL:
  - best-of-n: R(d) = d(α − βd), with KL_BoN = log n − (n−1)/n;
  - RL: R(d) = d(α − β log d).

  Picking the best of n proposals by rubric score is best-of-n, so there is an optimal n* where d = α/(2β), estimable from pairs of proxy and gold scores.
- **Moskovitz et al. (ICLR 2024, [2310.04373](https://arxiv.org/abs/2310.04373)) [verified].** Composite reward models: correlation between components moves the point where over-optimisation starts. Their fix is Lagrange-multiplier caps per component instead of fixed weights.
- **Kwa, Thomas, Garriga-Alonso (NeurIPS 2024, [2407.14503](https://arxiv.org/abs/2407.14503)) [verified].** If the proxy error is heavy-tailed, KL regularisation does not prevent catastrophic Goodhart. Diagnostic: the tail of the residual Y − h(S) on the gold set.
- **Mahmoud, Rezaei, Wang, Gunjal, Liu, He (2026, [2605.12474](https://arxiv.org/abs/2605.12474)) [verified].** Hacking in rubric-based RL comes from two sources: verifier failure and rubric under-specification. Stronger verifiers reduce it but do not remove it.
- **Andrews, Kitagawa, McCloskey (QJE 2024, 139:305) [verified].** Winner's curse when selecting the best of many noisy estimates, with conditional and hybrid confidence intervals. This applies directly to the "inherit" step.

## Direct implications for the design

1. **"Is a new reward dimension useful" splits into two separate quantities.**
   - *Estimation value* (Kallus–Mao / PPI increment). This is exactly zero for runs whose Y is already observed. It is non-zero only where Y is missing: unrun proposals, the sealed-test families, and truncated runs. One cheap surrogate regime already exists: the first k steps of a trajectory as a short-term surrogate for the final `won`, which cuts the 30–40 min per pass.
   - *Decision value.* The gain in cross-candidate proxy quality (Sharpe/IC) for predicting the held-out paired effect.

   Correlation with `won` on the same run measures neither of these.
2. **Criterion for dimension j:** ΔSharpe_j = maxSharpe(D ∪ {j}) − maxSharpe(D). Estimate Λ by JIVE or split-half cross-covariance over the corpus of past candidate evaluations (ALFWorld plus AppWorld), with Δ^N = Validation paired effect. Get significance by bootstrapping or permuting over candidates. Add the Prentice residual test so paradoxical dimensions are rejected.
3. **Reward = surrogate index h(S,X)**, fitted rather than hand-weighted, and PPI++-corrected on a gold subset of real runs. Allocate real runs with the active-inference rule π ∝ residual sd.
4. **Free power now:** add pre-treatment base-run G/`won` from several seeds as CUPED covariates. Test on G, or on a composite learned as in Jeunen & Ustimenko. Keep `won` on Validation as the North Star and check that the signs agree.
5. **In the low-rank framework** (my own derivation, not from the literature):
   - A rubric channel with Fisher operator G_S gives V(G+G_S). To first order, ΔV_eff ≈ ⟨H, P_T G_S P_T H⟩, where H = A^{-1}P_TΓ is the least-favourable direction.
   - G_S should be Schur-complemented against the channel's own nuisance (its calibration and link).
   - So a dimension's value is its efficient information along the direction of the target functional. That is "information gain" made precise.
   - Generic dimensions ("be careful") with a large nuisance of their own contribute about 0, which is consistent with the earlier stall.
6. **Goodhart guards:**
   - cap the number of proposals compared per round (the best-of-n law);
   - cap each dimension separately;
   - repeat the transport audit for every new harness;
   - use winner's-curse-corrected confidence intervals for inherit decisions.

## Gaps nobody has filled

- **Learned surrogate that is then optimised.** No efficiency result covers adding a surrogate dimension that is learned on the same small gold set and then put under optimisation pressure.
- **Treatments generated from the surrogate.** PPI and surrogacy theory assume fixed treatments. A self-evolving loop generates its treatments from the surrogate itself, so h is not policy-invariant. The transport audit in Landesberg & Narayan is a test, not a theory.
- **Low-rank effect tensors.** There is no efficiency bound for a low-rank candidate × capability × family effect tensor with auxiliary channels. Joining the AoS information equation with Kallus–Mao surrogates is open.
- **Small, correlated corpora.** IC and proxy-quality methods assume hundreds of independent experiments. Nothing handles 30–80 correlated candidates that share edits; low-rank or hierarchical pooling could fill this.
- **Discrete search.** Over-optimisation laws exist for policy optimisation against a reward model. No analogue exists for discrete program search over harness edits.