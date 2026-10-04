# Literature novelty check: Boosted Intervention Trees (BIT) + hindsight self-proposer

Search date: 2026-10-04. Sources: arXiv 2023 to Oct 2026, lab blogs. "[verified]" means the arXiv id, title, and date were checked against the arXiv API or abstract page. Where a row describes method details, they come from the abstract or HTML page.

Components: (1) online detector+leaf intervention trees (note / block-once), additive ensemble; (2) residual memory tree (prefix tries, Beta posteriors, g/h, Newton-gain priority, sibling contrast); (3) same-model hindsight proposer with privileged feedback (failed-test text); (4) offline replay screening (within-task paired gain, IC, net value); (5) causal admission via branch-at-fire paired continuations, CI lower bound, tau = s*a, then validation arm; (6) boosting iterations.

## 1. Closest works

| Work | Shares | Lacks / differs | Status |
|---|---|---|---|
| **Self-Harness** (Zhang et al., 2606.09498, Jun 2026) | **Same model** as proposer ("not an external optimizer"). Weakness mining from traces, verifier-grounded failure clusters, minimal edits, accept-and-merge rounds (3, part of 1 and 6). **AppWorld** with Qwen3.5-35B-A3B (22.5 -> 52.2). Retained AppWorld edits "distinguish action-only tasks from information requests". | Edits are config/prompt/runtime-policy changes, not state-triggered detectors. Clusters are ranked by support/actionability, with no residual/Newton priority and no success-sibling contrast. Acceptance is a deterministic non-regression rule on full reruns: no causal effect estimate, no CI, no branch replay. No ablation of verifier evidence, so no self-blindness finding. | [verified] |
| **HASP** (Liu et al., 2605.17734) | Executable Python `should_activate(state)` predicates + MODIFY_ACTION / INJECT_CONTEXT interventions mined from failures (component 1, nearly identical form) | Admission by a GPT-4o teacher rubric score plus mock execution: no causal or statistical test. Not same-model, not AppWorld. No boosting/residuals. | [verified] |
| **HarnessEvolve** (Jiang et al., 2609.00829) | Privileged hindsight: the agent re-runs with ground-truth answers to make reference trajectories and aligns failures against them (3). Leakage gate (like our memorization flags, 4). Performance gate. | Gate is batch accuracy margin. No runtime triggers, no branch replay. Not AppWorld. | [verified] |
| **PSP: From Self-Distillation to Self-Practice** (Su et al., 2609.29051) | Privileged info via an analyzer that writes "action-oriented rules" from failed rollouts + a reference trajectory. AppWorld. Reports that without the reference the analyzer cannot infer the correct procedure (close to our self-blindness finding). | Analyzer is a different, larger model (Qwen3.6-27B teaching 4B/8B). Rules are per-task and used only in training-time sampling (RL). No harness, no admission. | [verified] |
| **HarnessFix** (Chen et al., 2606.06324) | Failed trajectories -> localized harness repairs. AppWorld 36.7 -> 42.2. | Regression-aware validation by reruns. No causal leaf values. | [verified] |
| **Harness-R1** (Shao et al., 2608.02276) | Failure batches -> executable harness patches validated by fresh reruns | A separately RL-trained 9B harness engineer (not self). Not AppWorld. | [verified] |
| **Meta-Harness** (Lee et al., 2603.28052) | Proposer reads raw traces of prior candidates and searches harness code (1, 6) | Strong coding-agent proposer, score-based selection, no causal admission | [verified] |
| **Dream-RSI** (Zheng et al., 2609.14858) | Logged discovery trees as an offline replay simulator for scoring candidate policies (4) | Evolves exploration policy for scientific discovery. Per the HTML: no prefix tries, Beta posteriors, g/h, or Newton gain, and no agent interventions. Our memory tree goes beyond it. | [verified] |
| **ASSAY / Not All Skills Help** (Wang et al., 2606.15390) | Per-skill causal effects via randomized masking, heterogeneity across tasks (CATE framing), AppWorld ReAct | Effects estimated at whole-episode level and transferred by kernel. No branching at the trigger state, no proposer. | [verified] |
| **Causal Agent Replay** (2606.08275), **CausalFlow** (2605.25338), **AgentSentry** (2602.22724), **Replay Gap** (2608.08239) | Re-execute from a logged intermediate state with do-interventions, paired same-policy controls, CIs (the core mechanics of 5) | Used for failure attribution, repair, or security, never to admit a learned harness rule or to estimate leaf value / dilution | all [verified] |
| **Real-Time Detection and Repair** (2608.02464) | Prefix monitors + rollback. Naming the failing check works best. | Monitors are ESN anomaly detectors, not LLM-proposed. No admission loop. | [verified] |
| **PrefixGuard** (2605.06455), **ProbGuard** (2508.00500), **AgentSpec** (2503.18666) | Prefix-observable monitors/enforcement (1) | Predict risk, or hand/LLM-written safety rules. No measured uplift. | [verified] |
| **Living-Harness** (2607.26598) | Episodic memory of "trigger conditions, failure patterns, recovery actions", posterior evidence for bounded updates | No causal admission. tau2/MultiWOZ. | [verified] |
| **DivSkill-SQL** (2605.21792) | Each new skill fit on the current ensemble's failures (residual/boosting, 6) | Text-to-SQL Pass@K, no interventions | [verified] |
| **ExpeL** (2308.10144), **AutoGuide** (2403.08978), **AutoManual** (2405.16247), **AWM** (2409.07429), **ACE** (2510.04618), **ReasoningBank** (2509.25140), **LEAP** (2402.05403) | Insights mined by contrasting success and failure on the same task (AutoGuide: context-conditioned guidelines, i.e. detector+note), playbooks on AppWorld (ACE, same model in all roles) | Admission is heuristic or none. No causal leaf value. | [verified] |
| **GEPA** (2507.19457), DSPy/MIPRO (2310.03714, 2406.11695), ProTeGi (2305.03495), TextGrad (2406.07496), Promptbreeder (2309.16797) | Reflective proposer reads traces | Global prompt edits, scored on minibatch averages | [verified] |
| **ADAS** (2408.08435), **Gödel Agent** (2410.04444), **DGM** (2505.22954), **STOP** (2310.02304), **AlphaEvolve** (2506.13131) | Scaffold self-improvement loops | Archive/evolutionary search scored on benchmark | [verified] |
| **Boosted Prompt Ensembles** (2304.05970), **PromptBoosting** (2212.09257) | Boosting with prompts on hard examples | Classification/QA outputs, not agent interventions | [verified] |
| **Self-Correction Bench** (2507.02778), **Self-Correction Illusion** (2606.05976), **SkillMentor** (2607.27360) | Models do not fix their own errors / need external blind-spot diagnosis | No agent-harness, privileged-feedback ablation | [verified] |
| **OPSD** (2601.18734), **PI Distillation** (2602.04942), **PI in OPSD** (2609.20612), **HINT-SD** (2605.17873, AppWorld) | Privileged self teaches unprivileged self | Weight updates only. No harness rules. | [verified] |
| **Evaluation reliability**: REUSE (2609.33180), Fragility (2608.18066), Harness Updating != Benefit (2605.30621), Theory of Reliable Self-Evolution (2609.08175) | Statistical admission / false-promotion control (5) | Score-level gating, no within-task / branch causal estimand | [verified] |

## 2. Verdict

**Overall combination: novel.** No paper combines state-triggered intervention trees, residual-prioritized case selection, same-model privileged hindsight proposal, and causal admission by branch-at-fire paired continuations with a CI rule. The space is crowded, though. June–Sept 2026 alone has about 8 harness self-evolution papers, several on AppWorld.

**Not novel (concede and cite):**
- Detector + note/block interventions as executable predicates: HASP, AutoGuide, AgentSpec, Living-Harness.
- Same-model harness self-improvement on AppWorld: Self-Harness. "No stronger teacher" is not a contribution by itself.
- Contrasting failed and successful trajectories: ExpeL, AutoGuide.
- Privileged/reference-informed hindsight: HarnessEvolve, PSP, OPSD family.
- Offline replay over logs: Dream-RSI.
- Counterfactual re-execution from an intermediate state: CAR, CausalFlow, AgentSentry, Replay Gap.
- Residual/boosting framing for prompts/skills: Boosted Prompt Ensembles, DivSkill-SQL.
- Skill heterogeneity / causal curation: ASSAY.
- "Models can't diagnose own errors" in general: Self-Correction Bench, SkillMentor, and PSP's no-reference ablation.

**Appears novel:**
1. **Branch-at-fire causal admission of a proposed harness rule.** Leaf value is the local effect *a* from paired continuations at the firing state. Admission requires the CI lower bound > 0, and a validation arm follows. No harness paper uses a causal, local, CI-based acceptance test. All use full-rerun score deltas or judge scores.
2. **The dilution law tau = s*a.** It links trigger rate and local effect to the full-run gain and explains why score-level gates are underpowered. I found no counterpart.
3. **Newton-gain residual prioritization** (g = p-1, h = p(1-p) over per-task prefix tries with Beta posteriors) to pick which failures and sibling successes the proposer sees. Dream-RSI does not contain this.
4. **Controlled self-blindness result.** With the same model and the same cases, outcome-only proposals fail to find the systematic misconception. Adding failed-test text plus sibling contrast recovers it. This is a clean information ablation of the proposer. Self-Harness has no such ablation. PSP's version uses a larger analyzer and reference trajectories, for training.
5. **Statistical framing:** pooled prediction learns task difficulty, while within-task IC/paired gain targets uplift (CATE). This is explicit and tested, but ASSAY is partially adjacent.

**Strongest defensible ICML claim:** "Admission, not proposal, is the bottleneck. We treat harness evolution as boosting with causally estimated weak learners. Each LLM-proposed intervention's leaf value is measured by branch-at-fire paired continuations, then admitted by CI and confirmed on held-out tasks. A residual-driven memory chooses what the proposer sees. A same-model proposer is self-blind under outcome-only feedback, and privileged failed-test text plus sibling contrast is necessary and sufficient to rediscover a high-value rule (+15pp val, p=0.043, matching the hand-written rule)." Frame the work as a rigorous statistical method with a mechanistic finding, not as yet another harness optimizer.

## 3. Scoop risks

- **Self-Harness (2606.09498): highest risk.** It has the same model, AppWorld, a mine -> propose -> validate -> merge loop, verifier evidence, and a Qwen model family. Its retained AppWorld edits include "distinguish action-only tasks from information requests", which is essentially our rediscovered complete_task rule. Our "rediscovers a known high-value rule" result must be positioned as a controlled ablation, not a discovery, and should cite this. Differentiate on causal admission, intervention trees, residual selection, and the self-blindness ablation.
- **HASP (2605.17734):** it pre-empts the intervention representation (predicate + modify/inject). Do not claim the tree/leaf format as novel.
- **PSP (2609.29051):** it pre-empts "privileged info lets the model write the right rules / without it cannot." Differentiate: same model, harness-level reusable rule, test-text vs reference trajectory.
- **HarnessEvolve (2609.00829):** privileged reference trajectories + leakage gate.
- **CAR / CausalFlow:** if they extend to "admit repairs by do-replay", they would overlap component 5. Watch for v2s.

## 4. Must-cite (arXiv)

1. Self-Harness, 2606.09498
2. HASP, 2605.17734
3. HarnessEvolve, 2609.00829
4. PSP: From Self-Distillation to Self-Practice, 2609.29051
5. Dream-RSI, 2609.14858
6. Causal Agent Replay, 2606.08275 (and CausalFlow, 2605.25338)
7. Not All Skills Help (ASSAY), 2606.15390
8. Meta-Harness, 2603.28052, and HarnessFix, 2606.06324
9. ACE, 2510.04618; ExpeL, 2308.10144; AutoGuide, 2403.08978
10. OPSD, 2601.18734; Boosted Prompt Ensembles, 2304.05970; Self-Correction Bench, 2507.02778

Surveys for taxonomy: 2507.21046 (what/when/how/where), 2508.07407; 2607.13104 (Self-Improvements in Modern Agentic Systems) [verified].
