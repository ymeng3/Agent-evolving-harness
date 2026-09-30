# The rubric as a validated, actionable mediator layer

## 1. Thesis
A rubric dimension earns its place only if it is a **mediator of the harness's own interventions**. That means two things: edits that move it also move success (trial-level surrogacy), and its deficit pattern predicts which module rescues a failure (actionability). Self-evolution then means shrinking the rubric's incompleteness τ² = Var η and raising actionability, with every step tested using the harness's edits as randomized interventions.

**How this sidesteps component credit.** Credit factorizes as credit(e) = β̂ᵀδ̂ˢ_e + η̂_e:
- The mediator effects δˢ_e are measured per component, and precisely.
- The transfer slopes β are pooled across all components.
- The Bernoulli noise that sinks per-component credit (MDE ≈ 17pp at n = 50) enters only through τ².
- No per-token credit is needed. Per-step credit is used only for trigger edits, via replay-to-first-activation-then-branch (a PAV advantage, Setlur et al. [verified]). Every-step components get credit through whole-trajectory mediator effects.

## 2. Setup
- **Runs.** Tasks t have family f(t). Candidates c are bos_appworld_v3 edit sets; c = 0 is the incumbent. BOS_EDITS_OFF toggles are designed interventions. A run (c, t, seed a) produces a trajectory τ and an outcome Y ∈ {won, G}.
- **Dimensions are programs.** Dimension j is an executable program over the step log, never an LLM score (the lesson from the PRM judge):
  - s_j(τ) = #{steps with trigger_j ∧ evidence_j} / #{steps with trigger_j}.
  - Each dimension carries its coverage, a claimed module m_j = (capability, impl, control point), and a counter-evidence predicate. This is the FailureMechanism schema made executable.
  - The LLM writes the programs; it does not score.
- **Trials.** A trial is i = (c, f). Its effects are δʸ_i = E[Y(c) − Y(0)] and δˢ_ij, estimated per seed by paired contrasts δ̂⁽ᵃ⁾_i. Task-level cells (c, t) serve localization.
- **(A1) Seed independence.** Runs at different seeds are independent given the cell. This is plausible because sampling is fresh on every run: even same-seed reruns give G = 0.9/0.7/0.7.
- **Projection (not assumed true).** δʸ_i = β_Rᵀδˢ_{i,R} + η_i, with τ²_R = E η_i².
  - PTE_R = 1 − τ²_R / Var δʸ is the Buyse–Molenberghs trial-level R² (Buyse et al. 2000 [unverified]), i.e. Prentice (1989) [verified] taken across interventions.
  - In IV terms, edits are instruments, dimensions are mediators, and τ²_R = 0 is the overidentifying restriction.
- **Low rank, via the AoS machinery.**
  - Θ ∈ ℝ^{C×T×(1+K)} stacks δʸ and the δˢ_j. It has low multilinear rank: edits act through few mechanisms, and tasks load on few capability demands.
  - Cells are sampled adaptively and non-uniformly. won enters as BTL on within-task discordant pairs, G as a sign/rank channel, and each dimension as a Gaussian channel.
  - The target is ψ = ⟨Γ, Θ⟩, e.g. a candidate's mean δʸ over Validation families.
  - The operator is A = P_T(G_Y + Σ_j G̃_j)P_T, where G̃_j is Schur-complemented against j's own nuisance (β_j, η). Then H = A⁻¹P_TΓ.
  - The one-step estimator with IPW gives each candidate's fast-evaluation confidence interval.

## 3. The criterion

**3a. Measurement: incremental surrogacy.**

  γ_j = E_i[r_ij η_i],  r_ij = δˢ_ij − Π_Rᵀδˢ_{i,R},  ΔPTE_j = γ_j² / (E r_j² · Var δʸ).

- **Interpretation.** −2γ_j is the functional gradient of τ²_R along the new feature. It equals AlphaGen's incremental-IC reward (Yu et al. 2023 [verified]) and the Barillas–Shanken residual α² [verified].
- **Estimator.**
  - Every second moment is a symmetrized cross-seed moment: M̂_uv = |I|⁻¹ Σ_i ½(û⁽¹⁾_i v̂⁽²⁾_i + û⁽²⁾_i v̂⁽¹⁾_i). Under A1 it is unbiased, even for u = v. This removes both attenuation from noisy mediators and mechanical same-run correlation.
  - β̂, Π̂ and γ̂_j are split-sample/JIVE plug-ins (Bibaut et al. 2024 [verified]), cross-fitted over family folds.
  - Standard errors come from a family-cluster bootstrap, which also absorbs the shared incumbent runs.
  - Report both γᴮ (between-candidate, which drives ranking) and γᵂ (within-candidate, which drives localization).
- **Decision.** Admit j to the reward if γ̂_j / ŝe > z(α_j), with α-investing over every dimension ever proposed (Foster & Stine 2008 [verified]). Dimension j must also pass these gates:
  - cross-seed reliability ≥ 0.4;
  - coverage ≥ 10% of live cells;
  - dispersion > 0 on the current frontier (Razin et al. 2025 [verified]);
  - specificity: edits that do not claim j's mechanism move its counter-evidence predicate less than claiming edits do;
  - the same sign in at least 2/3 of families.
- **Reward.** h = β̂ᵀs is the surrogate index (Athey et al. [verified]). It is used only for screening and allocation; promotion always requires Y.
- **What it buys (P1).** V_R(n) = [n/σ²_Y + 1/(τ²_R + κ)]⁻¹, with κ = βᵀΣ_Sβ/n. The logs give σ²_Y ≈ 0.18 (paired SE 0.060 at n = 50). So:
  - τ_R = 3pp gives n_eff ≈ 5×, which cuts the MDE from 17pp to about 7.5pp;
  - τ_R = 6pp gives about 2×.

**3b. Direction: actionability.**
- **Rescue panel.** ρ_tm = P(won | incumbent + module m on failure t). Estimate it from full runs, or by replay-branch for trigger edits.
- **Targeting rule.** m̂_R(t) = argmax_m Ê[ρ_tm | s_R(t)], using low-rank completion of the task × module matrix.
- **Value of dimension j.** VOI_j = E_t[ρ_{t, m̂_{R∪j}} − ρ_{t, m̂_R}]. Modules are chosen on seed-1 rescues and scored on seed-2 rescues, so the estimate is not optimistic.
- **Screening proxy.** I(D_j; Z | D_R), where Z_t = (ρ_tm)_m is the rescue profile. When only one module rescues, Z is the identity of the rescuing edit.
- **Admission.** Admit j to the diagnosis set if VOI's lower confidence bound (LCB) is above 0.
- **Why generic dimensions fail.** Once the anchor dimension absorbs the general factor, "be careful"-type dimensions leave only noise in r_j, so γ ≈ 0. Their deficits also spread evenly over modules, so I ≈ 0. The result is dead hooks.

**3c. Remove, merge, decay.**
- **Remove** j if the upper CIs of both leave-one-out γ_j and VOI_j fall below ε. Re-estimate on the last two rounds, because a dimension's value depends on the current policy.
- **Merge** j and k if their disattenuated correlation M̂_jk / √(M̂_jj M̂_kk) exceeds 0.9 and they claim the same module.
- **Decay.** Run a Chow test of β_j before vs after j was admitted. A drop signals the surrogate paradox under selection (Chen–Geng–Jia 2007; VanderWeele 2013 [verified]; the McLean–Pontiff analogue [verified]). Demote j to diagnosis-only.

## 4. Loop
```
R ← {S1 exec-error recovery latency, S2 redundant api_docs lookups, S3 wasted-step share,
     S4 complete_task by step 25 (anchor, never a target), S5 default-code steps (control)}
for round = 1..6:
  D = L + S_sparse  (incumbent tasks × dims deficits; robust low-rank)
  general ← top factors of L;  edge ← big |S_sparse| ∪ top |Y − h(s)|
  pairs ← same-task won-vs-lost contrasts ordered by signed η̂, plus mis-targeted rescues
  J ← LLM(pairs, FailureMechanism schema) → 10 dim programs          # $0 GPU
  for j in J: gates; γ̂_j, VOI_j; α-investing; merge/remove/decay
  targets ← top (j,m) by β̂_j · deficit_j · P̂(m rescues | deficit_j)
  cands ← proposer(targets, trajectories), n ≤ 8     # best-of-n cap (Gao et al. [verified])
  run Discovery tasks with π_t ∝ predicted contrast sd (IPW-logged)
  ψ̂_c ← AoS one-step (Y + h); extra runs by top-two Thompson (Russo 2020 [verified])
  confirm top-2 on Validation (2 seeds, Y only); inherit via hybrid CI (Andrews et al. [verified])
  bank ← bank ∪ new trials                            # each new edit = new instrument
  probe rescues at argmax_t P̂(fail_t)·H[Z | s(t)] on unused tasks outside Validation and sealed test
```
IPW keeps estimates on acquired tasks unbiased (Zrnic & Candès [verified]). Tasks the incumbent always wins keep a small sampling probability π, so harm stays detectable.

## 5. What can be proven

**P1: information gain equals incremental surrogacy.**
- *Setting:* Gaussian working model.
- *Result:* to first order, V_R − V_{R∪j} ≈ V_R²(Δτ²_j − β_j²Σ_jj/n) / (τ²_R + κ)², where Δτ²_j = γ_j² / E r_j². The gain is positive only if the residual j explains exceeds j's own noise. Noisy judge dimensions fail exactly here.
- *AoS form:* ΔV_eff = a⟨u_j,H⟩² / (1 + a⟨u_j,A⁻¹u_j⟩), with ⟨u_j,H⟩ ∝ γ_j. So information gain along the efficient-influence direction and causal surrogacy gain are the same number.
- *Proof:* Schur complement plus Sherman–Morrison on the tangent space.
- *Effort:* about 1 week for the Gaussian case and about 4 weeks for the BTL/low-rank case.

**P2: validity when the rubric is misspecified.**
- *Assumptions:* A1, i.i.d. family clusters, bounded fourth moments, λ_min(Σ_RR) ≥ c.
- *Result:* √F(γ̂_j − γ_j) ⇒ N(0, v_j), where γ_j is the projection parameter whether or not surrogacy holds. The bootstrap is consistent, and α-investing controls mFDR. The same-seed estimator, by contrast, is biased by the within-run noise covariance.
- *Proof:* cross-seed products are unbiased U-statistics; then the delta method.
- *Effort:* about 2 weeks.

**P3: actionability.**
- *Bound:* for utilities in [0,1], VOI_j ≤ √(½ I(D_j; Z | D_R)), by Pinsker and Jensen.
- *Decomposition:* if implementation fidelity and efficacy depend on the diagnosis only through the target module, then E[ΔY] = Σ_m P(target m) · P(fires | m) · E[ΔY | fires, m].
- *Identification:* the shuffled-diagnosis token-matched control breaks only the first factor, so comparing against it isolates the rubric's contribution.
- *Effort:* about 1 week.

**Not realistic by January:** a regret bound for the closed loop while h steers candidate generation. The decay test is the empirical substitute.

## 6. Experiments (AppWorld; uses about 400 of the available 50-task passes)

**Phase 0 (weeks 1–2, ~40 passes).**
- Fix the remaining default-code path (11/50 tasks) and log trigger/evidence fields.
- Incumbent × 4 seeds on Discovery and Validation (8 passes).
- 12 single-edit toggles × 2 seeds (24 passes).
- Rescue panel v0: 25 failures × 8 modules (~8 passes).

**G0 (frozen before data):**
- mediator-effect CI half-width ≤ 1/3 of won's (MECH_EVIDENCE H1);
- at least 3 dimensions with reliability ≥ 0.4;
- seed-rubric PTE LCB > 0.

If all three fail, kill the measurement route.

**Phase 1 (weeks 3–9, ~150 passes).** Six rounds of the loop.

**G1 (week 7), on temporally held-out candidates:**
- τ̂²(evolved) < τ̂²(seed), with LCB > 0;
- at least 2 dimensions with γ LCB > 0;
- sign agreement of at least 70% between predicted and realized Validation δʸ (Zhang et al. 2023 [verified]);
- at least one dimension with VOI LCB > 0.

If G1 fails, keep only the direction route.

**Phase 2 (weeks 8–12, ~180 passes). Proposal-gain trial:** 6 arms × 12 candidates × 2 Validation seeds. The arms:
- A: evolving causal rubric;
- B: fixed seed rubric;
- C: no rubric;
- D: generic LLM-judge rubric (rubric_aw v1/v2);
- E: random admission from the same proposal pool;
- F: token-matched shuffled diagnosis.

An AgentPRM-style judge competes offline on PTE and VOI.
- *Primary endpoint:* mean paired δʸ over **all** proposed candidates, which is immune to the winner's curse. Compare A−F and A−B.
- *Secondary:* the P3 decomposition and a G sign test.
- *G2:* A−F LCB > 0.

**Phase 3 (weeks 13–14, ~25 passes).** Arms A, B, C and F on the sealed test with 3 seeds, reporting hybrid CIs. Optionally, replicate P2 at $0 on the ALFWorld archival bank (17 interventions × 134 games × 3 seeds), if its per-game logs can be recovered.

**Headline plots:**
1. PTE and τ̂² vs round, per arm.
2. MDE vs number of runs, Y-only vs rubric-assisted.
3. Predicted vs realized δʸ.
4. Confusion matrix of claimed module vs actual rescuer.
5. Proposal gain split into targeting × activation × efficacy.
6. The L + S deficit map, general vs edge-case.
7. β before vs after admission.

## 7. The IC question
Yes, provided IC is computed on **intervention effects** across trials, with the dimension and the outcome taken from different seeds. That statistic is γ_j. An IC between a feature and won from the same run is mostly mechanical.

The gain comes from blocking and robustness, not from G being dense:
- **Blocking.** Within-task contrasts remove the task-difficulty factor, which carries 0.65 of won's variance.
- **Robustness.** The G sign test had power 0.89 against 0.77 for won, because G's noise comes as all-or-nothing jumps.
- IC has no power advantage over a slope t-test on the same demeaned data.
- Clark & West [verified] explains why nested MSE comparisons look flat.

IR ≈ TC·IC·√BR (Grinold; Clarke et al. [verified]) maps onto the rubric:
- IC is γ (measurement).
- TC is VOI × hook activation; dead hooks mean TC ≈ 0.
- BR is the number of independent (candidate, family) trials.

## 8. Failure modes and relation to the empirical check
1. **Power.** Observed IC ≈ ρ√(rel_S · rel_Y), with rel_Y ≈ 0.1 per trial. So ρ = 0.5 needs about 600 trials for t = 3, against roughly 40–60 candidates × 15 families.
   - Mitigations: trigger edits with heterogeneous effects raise rel_Y; α-investing admits dimensions early; the final claim pools everything.
   - Worst case, the paper becomes "how many trials a rubric needs".
2. **Surrogate paradox.** Completion is the most tempting dimension (within-task IC +0.69). But an edit that forces complete_task near step 30 raises S4 while lowering P(won | completed), currently 0.81–0.90. So S4 stays an anchor, guarded by its counter-evidence predicate and the decay test.
3. **Weak edit library.** If nothing rescues, VOI ≈ 0 and the direction route cannot be measured.
4. **Generic proposals persist.** The screen rejects them, which itself shows the screen works.
5. **Default-code confound.** S5 is a control in every regression.
6. **Competitor.** Yazdani et al. (2609.35646) [verified] use IRT discrimination to build a scalar score. They have no interventions and no actionability.

**Relation to the empirical check:**
- The 17pp MDE rules out validating each dimension on downstream success. Hence the pooled cross-seed moments.
- Post-treatment features are invalid as control variates, but they are valid as surrogates that are tested by intervention.
- There is no early-G proxy, so the savings must come from mediator precision.
- Only 2 patches share the same 50 tasks, so building the trial bank comes first. Estimating the rank needs about 10 edits.
- Running out of step budget dominates the failures, so the seed dimensions are step-efficiency mechanisms. Tasks completed with a wrong answer (3–6 of 50) are the expected sparse edge cases.