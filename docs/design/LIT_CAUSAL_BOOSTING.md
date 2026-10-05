# Literature: causal / decision boosting vs. BIT

2026-10-05. [verified] = title/authors/venue checked on arXiv or publisher page. LLM-harness neighbours: see `LIT_NOVELTY_BIT.md`.

## (a) Short answer

**Partly.** Boosting with treatment-effect trees exists: causal boosting (Powers et al. 2018), uplift boosting (Sołtys & Jaroszewicz 2018; UTBoost 2024; Ibragimov & Vakhrushev KDD 2024), and boosting for treatment selection (Kang et al. 2014). Functional-gradient boosting of *policies* also exists: NPPG (Kersting & Driessens 2008), boosted FQI, GBRL (ICML 2025), and Brukhim–Hazan–Singh (NeurIPS 2022). Tree *policies* with doubly robust leaves have regret guarantees (Athey & Wager 2021; Zhou–Athey–Wager 2023). None combines: (1) treatment-assignment trees whose round objective is J itself (dJ = η·s_k·a_k), whereas causal boosting fits CATE residuals; (2) LLM-proposed predicates over an open program/state space instead of exhaustive splits on fixed covariates; (3) leaves from paired, exactly replayed continuations at the firing state, whereas prior work uses propensities or one-arm-per-unit RCTs, and TRPO-vine/VinePPO/CAR branch from states but never value a rule; (4) sequential agent prefix states with first-fire semantics (DTR uses a few fixed stages); (5) LCB admission plus active sampling over states; (6) low-rank pooling across interventions (done for panels in synthetic interventions, never for policies).

Closest: **causal boosting**, **policy trees**, **NPPG/GBRL**, **CAR**.

## (b) Related work

| # | Work | Family | Shares | Differs | |
|---|---|---|---|---|---|
| 1 | Powers et al., *Stat Med* 37(11) 2018, arXiv 1707.00102 | causal boosting | Boosted causal trees on effect residuals | CATE not J; fixed X; one arm per unit | [verified] |
| 2 | Wager & Athey, *JASA* 2018, 1510.04342 | causal forest | Honest leaves = local effects, CIs | Bagging, no policy objective | [verified] |
| 3 | Athey, Tibshirani, Wager, *AoS* 2019, 1610.01271 | GRF | Leaves solve local moment equations | Estimates τ(x) only | [verified] |
| 4 | Nie & Wager, *Biometrika* 2021, 1712.04912 | R-learner | τ-loss, boostable | Static, observational | [verified] |
| 5 | Hahn, Murray, Carvalho, *Bayesian Anal.* 2020, 1706.09523 | BCF | Separate effect vs. prognostic priors (our r/c vs. V) | CATE only | [verified] |
| 6 | Rzepakowski & Jaroszewicz, *KAIS* 32 2012 | uplift tree | Divergence splits, multi-treatment | Exhaustive splits, static | [verified] |
| 7 | Sołtys & Jaroszewicz 2018, 1807.07909; Sołtys et al. *DMKD* 2015 | uplift boosting/ensembles | Boosting/bagging on uplift | Reweighting, no policy value | [verified] |
| 8 | Gao et al., UTBoost, PRICAI 2024, 2312.02573; Ibragimov & Vakhrushev, KDD 2024 | uplift GBDT | GBDT, causal objective | Tabular, RCT | [verified] |
| 9 | Kang, Janes, Huang, *Biometrics* 70(3) 2014 | boosting for treatment selection | Upweights misclassified-by-benefit units | One decision, parametric | [verified] |
| 10 | Athey & Wager, *Econometrica* 2021, 1702.02896 | policy learning | argmax AIPW value over Π; regret bound | Single-shot, no boosting | [verified] |
| 11 | Zhou, Athey, Wager, *Oper. Res.* 2023, 1810.04778 | multi-action policy trees | Trees as treatment rules, minimax regret | Exhaustive search, not additive | [verified] |
| 12 | Kallus, ICML 2017, 1608.08925; Bertsimas et al., *IJOO* 2019 | prescriptive trees | Partition into best-treatment regimes | Single tree, static | [verified] |
| 13 | Kersting & Driessens, ICML 2008 (NPPG) | functional PG boosting | Policy = sum of trees along functional gradient of J | No causal leaf CIs, no LLM splits | [verified] |
| 14 | Fuhrer, Tessler, Dalal, GBRL, ICML 2025, 2407.08250 | GBT in RL | Trees fit PG targets | Actor-critic, numeric | [verified] |
| 15 | Brukhim, Hazan, Singh, NeurIPS 2022, 2108.09767 | boosting for RL | RL to weak learners, Frank-Wolfe | Theory only | [verified] |
| 16 | Tosatto et al., ICML 2017 (B-FQI); Bagnell et al. NIPS 2006 (MMPBoost) | boosted value / imitation | Additive residual fitting | Value/imitation | [verified] |
| 17 | Tao, Wang, Almirall, *AoAS* 12(3) 2018; Murphy, *JRSS-B* 65 2003 | DTR | AIPW-purity trees; A-learning = advantage only | Few stages, backward induction | [verified] |
| 18 | Schulman et al. TRPO (vine), ICML 2015, 1502.05477; Kazemnejad et al. VinePPO, ICML 2025, 2410.01679; Ecoffet et al. Go-Explore, *Nature* 590 2021 | branching rollouts | MC from reset states | Advantages for gradients, not rule value | [verified] |
| 19 | Shah, CAR, 2606.08275; Bonagiri et al., CausalFlow, 2605.25338 | agent counterfactual replay | do-interventions + replay, CIs | Attribution, not improvement | [verified] |
| 20 | Chen et al., CPO, 2602.01711 | causal prompt opt. | DML prompt effects, heterogeneity | Observational, global prompts | [verified] |
| 21 | Jesson et al., Causal-BALD, NeurIPS 2021, 2111.02275; Kato et al. 2401.03756; Russo 1602.08448 | active CATE / BAI | Effect-uncertainty acquisition; top-two TS | Units/arms, not replay states | [verified] |
| 22 | Agarwal, Shah, Shen, synthetic interventions, 2006.07691; Agarwal et al. COLT 2023, 2109.15154; Athey et al. *JASA* 2021, 1710.10251 | low-rank causal | Low-rank tensor over interventions | Panels, no policy loop | [verified] |
| 23 | Thomas et al. HCPI, ICML 2015; Jin, Yang, Wang, ICML 2021, 2012.15085 | safe / pessimistic improvement | Lower-bound acceptance; pessimism optimal | IS, not paired branches | [verified] |

## (c) Frameworks and equations to borrow

1. **Performance-difference lemma / CPI** (Kakade & Langford 2002). J(h') − J(h) = E_{τ∼h'} Σ_t A^h(σ_t, a'_t). For the mixture h_η = (1−η)h + η(h⊕k), the CPI bound gives J(h_η) − J(h) = η·E_{σ∼d^h}[A_k(σ)] + O(η²). Under first-fire semantics E_{d^h}[A_k] = s_k·a_k, so dJ/dη|₀ = s_k a_k. The O(η²) term covers repeated firing.
2. **Functional gradient boosting** (Friedman 2001; Mason et al. 1999; NPPG). f_m = f_{m−1} + ν·h_m with h_m = argmax_h ⟨∇J(f_{m−1}), h⟩. With the d^h-weighted inner product the best tree maximises Σ_{σ fires} d^h(σ)A(σ) = s·a. The LLM is an approximate argmax oracle (weak-learner edge, Brukhim et al.).
3. **Policy learning regret** (Athey & Wager). π̂ = argmax_{π∈Π} n⁻¹ Σ_i (2π(X_i)−1)Γ_i, with AIPW score Γ_i = μ̂₁−μ̂₀ + W(Y−μ̂₁)/ê − (1−W)(Y−μ̂₀)/(1−ê). Regret is O_P(κ(Π)·√(V*/n)). With paired branches, Γ = Y⁽¹⁾ − Y⁽⁰⁾ exactly (no ê, μ̂). Π is the finite set of LLM-proposed trees, so κ is roughly √log|Π|; count proposals for multiplicity.
4. **R-learner loss** for the pooled model: τ̂ = argmin Σ[(Y−m̂(σ)) − (W−ê(σ))τ(σ)]² + Λ(τ). With W randomised at ê = 1/2 inside each pair, this reduces to Σ(D_i − τ(σ_i))² with D = Y⁽¹⁾ − Y⁽⁰⁾. Plug in τ(σ,k) = u(σ)ᵀw_k (rank-1/low-rank, as in the synthetic-interventions factorisation E[Y⁽ᵈ⁾] = Σ_l u_l v_l λ_{d,l}) and A_k = (1−V)r_k − V c_k.
5. **Uplift / transformed outcome** (Athey–Imbens, as used by Powers' PTO): Y* = Y(W−e)/(e(1−e)), E[Y*|σ] = τ(σ). Report Qini/uplift curves over the firing population. The Rzepakowski divergence gain is a split score for detector proposals.
6. **LCB admission** (HCPI; Jin et al.). Admit k iff LCB_δ(s_k a_k) > 0, with δ split over proposals (Bonferroni or alpha-spending). Pessimism gives suboptimality ≤ 2E_{π*}[Γ_width].
7. **Active sampling**: top-two Thompson sampling, or Causal-BALD-style acquisition on Var[A_k(σ)]·d^h(σ).

## (d) Must-cite

1. Powers et al., *Stat Med* 2018 (arXiv 1707.00102).
2. Athey & Wager, *Econometrica* 2021 (1702.02896).
3. Zhou, Athey, Wager, *Oper. Res.* 2023 (1810.04778).
4. Nie & Wager, *Biometrika* 2021 (1712.04912).
5. Wager & Athey, causal forests, *JASA* 2018 (1510.04342) and Athey, Tibshirani, Wager, GRF, *AoS* 2019 (1610.01271).
6. Friedman, *AoS* 29(5) 2001.
7. Kersting & Driessens, NPPG, ICML 2008.
8. Kakade & Langford, CPI, ICML 2002.
9. Rzepakowski & Jaroszewicz, *KAIS* 2012, and Sołtys & Jaroszewicz, uplift boosting (1807.07909).
10. Thomas et al., HCPI, ICML 2015.
11. Agarwal, Shah, Shen, synthetic interventions (2006.07691).
12. Shah, Causal Agent Replay (2606.08275), plus VinePPO (2410.01679) for branch-from-state MC.

Note: KDD 2024 uplift-GBDT verified via listing (ACM page 403); TRPO vine is in the body, not abstract.
