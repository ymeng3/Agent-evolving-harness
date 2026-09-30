# Literature scout: evolving rubrics, reward models and evaluators (2023–2026)

Tags: **[v]** = paper seen in a search result or page this session. **[v\*]** = paper seen, but the author list is from memory. **[u]** = not checked this session.

## Findings

**A. Rubric and checklist rewards: what keeps a criterion**
- **RaR**: Gunjal et al. 2025, arXiv 2507.17746 [v]. A rubric is a weighted checklist of atomic subgoals. Scores are combined either explicitly (weighted sum) or implicitly (the judge sees all items). Up to +31% relative gain on HealthBench over Likert judges. The only usefulness signal is the downstream score. *Map:* use explicit aggregation so each dimension's weight can be estimated.
- **RLCF**: Viswanathan et al. 2025, 2507.18624 [v]. Checklists written per instruction, scored by an LLM judge plus verifier programs. *Map:* prefer programmatic checks on AppWorld state and logs over judge items.
- **OnlineRubrics**: Rezaei et al. 2025, 2510.07284 [v]. New criteria come from pairwise contrasts between the current policy and a reference policy; up to +8% over static rubrics. *Map:* draw mechanism criteria from paired won-vs-lost trajectories (same task, same seed), not from single failures.
- **DR Tulu / RLER**: Shao, Asai et al. 2025, 2511.19399 [v] (ICML 2026 oral). The retention rule is explicit: drop rubrics whose reward has zero variance across rollouts, then keep the top K by standard deviation. *Map:* a cheap filter, but it measures spread only, not agreement with the outcome.
- **Auto-Rubric**: Xie et al. 2025, 2510.17314 [v]. Greedily maximizes the coding rate C(E_R) = ½ log det(I + E_Rᵀ E_R / (ε²|R|)) over rubric embeddings, i.e. marginal information gain; 70 preference pairs suffice. *Map:* this is D-optimal design, which ignores the target quantity. You want c-optimal (see Implications §2).
- **Reward hacking in rubric RL**: Mahmoud, Rezaei, Wang, Gunjal, Liu, He 2026, 2605.12474 [v]. Separates verifier failure from rubric-design failure using a panel of reference judges from other model families. Exploits cluster in three places: partially satisfied compound criteria, implicit content treated as explicit, and loose topical matching. *Map:* criteria must be atomic and falsifiable, checked by an independent reference evaluator.

**B. Theory: a useful reward is not the same as an accurate one**
- **Razin, Wang, Strauss, Wei, Lee, Arora** 2025, 2503.15477 [v] (NeurIPS). If the reward has low variance under the current policy, the objective is flat and optimization is slow, even when the reward model is perfectly accurate. Reward-model quality depends on the policy it guides. *Map:* this is the formal reason a rubric must keep evolving. A criterion's value has to be re-estimated on the current frontier of candidates.
- **PAV**: Setlur et al. 2024, 2410.08146 [v] (ICLR 2025). The step reward is an advantage, A^μ = Q^μ − V^μ, under a "prover" policy μ different from the base policy π. Theorem 3.1: improvement needs *distinguishability* (large Var A^μ) and *alignment* (large E[A^μ A^π]). *Map:* your replay-to-first-activation-then-branch-OFF procedure is a Monte Carlo estimate of A^μ. That explains why trigger edits rank correctly and every-step edits (no single step to branch at) do not. A blind promise judge estimates Q, not A.
- **CURE**: Wang, Yang, Tian, Shen, Wang 2025, 2506.03136 [v]. The unit-tester's reward is *reward precision*, P(R_correct > R_wrong). Theorem 3.1: precision aggregated over m tests goes to 1 iff μ = p_u(1−p₀₁) − (1−p_u)p₀₀ > 0, with bound ≥ 1 − exp(−μ²m/8). *Map:* treat each criterion as a test of candidates and estimate its μ on labelled pairs. A criterion with μ ≤ 0 harms ranking; the bound gives the m needed for a target ranking accuracy.
- **PPE**: Frick et al. 2024, 2410.14872 [v]. Proxy metrics are validated by their correlation with post-RLHF downstream outcome (r ≈ 0.77). *Map:* meta-evaluate the rubric against realized held-out gains.
- **Overoptimization**:
  - Gao, Schulman, Hilton 2022, 2210.10760 [v]: gold score has a closed form in the distance optimized against the proxy (e.g. d(α − βd) for best-of-n).
  - Coste et al. 2023, 2310.02743 [v]: uncertainty-weighted and worst-case ensemble objectives.
  - Eisenstein et al. 2023, 2312.09244 [v\*]: ensembles mitigate but do not eliminate hacking, because members share error modes.
  - WARM 2401.12187 [v].
  - *Map:* picking the best of N candidates by rubric score is best-of-n selection, so expect a winner's curse.
- **ArmoRM** (Wang et al. 2024, 2406.12845 [v\*]): 19 absolute objectives with a prompt-conditioned gate. **DRMs** (2502.13131 [v]; authors not checked): PCA on embedding differences (chosen − rejected) gives orthogonal preference axes. *Map:* a low-rank factorization of paired trajectory-feature differences would give data-driven, non-redundant rubric axes.

**C. Discovering criteria from data**
- **ICAI**: Findeis et al. 2024, 2406.06560 [v] (ICLR 2025). Selects the principles that best reconstruct the annotations.
- **VibeCheck**: Dunlap, Mandal, Darrell, Steinhardt, Gonzalez 2024, 2410.12851 [v] (ICLR 2025). Keeps a trait only if it is well-defined (judges agree), differentiating (separates models) and user-aligned (predicts preference). *Map:* reliability × dispersion × alignment is the scorecard a new dimension should pass.
- **EvalTree**: Zeng et al. 2025, 2503.08893 [v]. A hierarchical capability tree whose weak nodes form the weakness profile; validated by larger gains from data collected on those weaknesses.
- **Skill-slices**: Moayeri et al. 2024, 2410.13826 [v]. Models within 0.4% overall differ by about ±18% on individual skills. *Map:* the aggregate metric hides structured differences, which is your MSE-vs-IC point.
- **AgentErrorTaxonomy / AgentDebug** (Zhu et al. 2025, 2509.25370 [v\*]): 17 error types across 5 modules. **Who&When** (Zhang et al. 2025, 2505.00212 [v], ICML): the best step-level failure attribution is 14.2% accurate. *Map:* LLM-based localization is unreliable, so every diagnosed mechanism needs counterfactual evidence.

**D. Process reward models for agents**
- AgentPRM (Xi et al. 2025, 2511.08325 [v]; TD + GAE) and AgentPRM (Choudhury 2025, 2502.10325 [v\*]; Monte Carlo rollout targets).
- Zhang et al. 2025, 2501.07301 [v]: Monte Carlo step labels are noisy and worse than judge or human labels.
- AgentProcessBench (2603.14465 [v]) and Plan-RewardBench (2604.08178 [v]): evaluators degrade sharply on long horizons.
- AgentRewardBench (Lù et al. 2025, 2504.08942 [v\*]): no single judge wins across benchmarks.
- *Map:* this is consistent with your null result. Step reward is credible only as an advantage under a grounded prover (PAV).

**E. Self-evolving agents (all keep the evaluator fixed)**
- **DGM**: Zhang, Hu, Lu, Lange, Clune 2025, 2505.22954 [v]. Documents objective hacking: an agent removed the hallucination-detection markers the evaluator relied on.
- **HGM**: Wang, Piękos, Nanbo, Laakom, Chen, Ostaszewski, Zhuge, Schmidhuber 2025, 2510.21614 [v].
  - CMP(a) = E[max utility over a's clade].
  - Estimator: pooled clade successes / (successes + failures).
  - Nodes to expand are chosen by Thompson sampling on Beta posteriors.
  - Weighted correlation with empirical CMP: 0.78 for HGM vs 0.29 for DGM.
- ADAS 2408.08435 [v], Gödel Agent 2410.04444 [v], SICA 2504.15228 [v], AlphaEvolve 2506.13131 [v] (evaluation cascades).
- Self-Rewarding 2401.10020 [v]; Meta-Rewarding 2407.19594 [v] (a meta-judge judges the judgments, which delays saturation).
- *Map:* none of these evolves the criteria. HGM's lesson transfers directly: value a criterion by the metaproductivity of the proposals it induces.

**F. Efficient and adaptive evaluation, and inference**
- **IRT-based subsampling**:
  - tinyBenchmarks (Maia Polo et al. 2024, 2402.14992 [v]): IRT / p-IRT / gp-IRT estimators, about 2% error with ≤100 items.
  - metabench (Kipnis et al., 2407.12844 [v\*]): items chosen by Fisher information; one factor explains 79%.
  - Fluid (Hofmann et al. 2025, 2509.11106 [v]): adaptive items chosen by Fisher information at the current ability estimate θ.
  - Truong, Tu, Liang, Li, Koyejo 2025, 2503.13335 [v]: amortized item calibration plus a conditional item generator.
  - Ruan, Maddison, Hashimoto 2024, 2405.10938 [v]: 3 principal components explain about 97% of the benchmark matrix.
- **Unbiased inference with cheap predictions**:
  - Active testing (Kossen, Farquhar, Gal, Rainforth 2021, 2103.05331 [v]): importance-weighted unbiased risk when test points are chosen actively.
  - PPI (Angelopoulos et al. 2023, Science [v]) and active statistical inference (Zrnic & Candès 2024, ICML [v]).
  - Surrogate index (Athey, Chetty, Imbens, Kang, NBER w26463 [v]): under Prentice surrogacy, the treatment effect on E[Y|S] equals the effect on Y, and the assumption is testable.
- **Evaluation noise**:
  - Signal & Noise (Heineman et al. 2025, 2508.13144 [v]): the ratio of spread across models to checkpoint noise predicts decision accuracy.
  - Madaan et al. 2024, 2406.10229 [v]: continuous metrics cut variance.
  - Miller 2024, 2411.00640 [v]: paired question-level differences and clustered standard errors.

**G. Task generation aimed at weaknesses**
- **AutoBencher**: Li, Kaiyom, Liu, Mai, Liang, Hashimoto 2024, 2407.08351 [v]. Maximizes novelty + difficulty + 10·separability, where novelty = 1 − RankCorr(v̂, v) and v̂ is the new dataset's accuracy vector predicted from old benchmarks.
- **Rainbow Teaming**: Samvelyan et al. 2024, 2402.16822 [v]. A MAP-Elites archive over a grid of descriptors.
- **Self-Challenging agents**: Zhou, Levine, Weston, Li, Sukhbaatar 2025, 2506.01716 [v]. Code-as-Task: each task comes with an instruction, a verifier, a solution and failure cases.

## Direct implications for the design

1. **A scorecard for each criterion (this is the IC idea in statistical terms).** For dimension k, take candidate pairs on task t, with rubric difference Δs_kt and outcome difference ΔY_t (G or won). Report three numbers:
   - **Alignment:** IC_k = the within-task rank correlation across candidates; ICIR = mean/sd over tasks, which acts as a t-statistic.
   - **Dispersion:** variance of the dimension on the current frontier (Razin, RLER, PAV's distinguishability).
   - **Reliability:** agreement across judges and seeds.

   Why IC shows significance where MSE does not: MSE is dominated by the task-difficulty factor, which is the first principal component of the low-rank candidate × task matrix. Within-task ranks remove that factor (the same mechanism as your 0.4× paired variance) and are robust to G's bounded, zero-inflated distribution. Grinold's IR ≈ IC·√breadth [u] then gives the number of tasks needed.

2. **Measure the gain in information about the decision, not information in general.** Adding dimension k adds a Fisher channel G_k. Its value is

   ΔV_k = ⟨P_TΓ, A⁻¹P_TΓ⟩ − ⟨P_TΓ, (A + P_T G_k P_T)⁻¹ P_TΓ⟩,

   where Γ targets held-out G(challenger) − G(incumbent). This is c-optimal design, conditional on the dimensions already in the rubric; Auto-Rubric's log det is the D-optimal alternative. A working proxy is the PPI variance factor 1 − ρ²_partial. It can be computed offline from logged trajectories.

3. **Keep the rubric's two roles separate.**
   - **Measurement:** the rubric acts as a surrogate for Y. Judge it by ΔV_k and check surrogacy on the Validation split.
   - **Direction:** the rubric localizes where to propose. Judge it by the paired gain of the proposals it triggers against a token-matched control, i.e. HGM-style metaproductivity with Beta–Thompson sampling over mechanisms.

   The rubric_abc stall fits this picture: the generic dimensions had dispersion but neither alignment nor productive proposals.

4. **Discover axes contrastively and in low rank.** Factorize paired won-vs-lost trajectory differences (as DRMs do), name the axes ICAI-style, then prune with the RLER standard-deviation rule, CURE's μ > 0 test and the VibeCheck triple.

5. **Guard against Goodhart.** Accept a candidate on an ensemble lower bound, keep AppWorld's programmatic goal checks as the gold outcome, and run a periodic cross-family reference judge.

6. **Spend evaluation passes adaptively.** Choose tasks for each candidate by Fisher information, with IPW debiasing. Generate new tasks from weak EvalTree nodes using AutoBencher-style novelty.

7. **Use step-level credit only where PAV applies** (trigger edits). Every-step edits need paired A/B comparisons over whole trajectories.

## Gaps nobody has filled

- **Valuing a new criterion against a specific target and given the existing criteria.** Current rules are marginal standard deviation (RLER), D-optimal log det (Auto-Rubric), or end-to-end retraining.
- **Criterion value that changes as the policy changes.** Razin shows the dependence, but nobody gives an update or retirement rule with guarantees (for example a drifting-arm bandit).
- **The surrogate paradox under selection.** There is no sequential test for when optimizing a rubric surrogate breaks surrogacy.
- **Evaluators that co-evolve at the harness (program) level.** DGM, HGM, ADAS, SICA and AlphaEvolve all fix the evaluator; OnlineRubrics and RLER evolve rubrics only for weight-level RL.
- **A low-rank candidate × task × criterion tensor observed through paired or partial-credit outcomes.** Nobody has combined IRT-style low rank with rubric dimensions this way.
- **Interventional checks of diagnosed mechanisms.** EvalTree, skill-slices and AgentDebug are descriptive or rely on low-accuracy LLM localization.