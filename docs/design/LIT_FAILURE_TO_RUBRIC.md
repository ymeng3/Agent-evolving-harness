# Literature: agent failure taxonomies → automatic checks → closed-loop rules (2026-10-03)

Source: literature subagent. [v] means the arXiv abstract or HTML was opened in that session. Effect sizes are as stated in the abstracts.

## (a) Failure taxonomies
- **MAST** (Cemri et al. 2025, 2503.13657, NeurIPS'25 D&B) [v]
  - 14 failure modes from 1600+ traces, labelled by an LLM judge (κ=0.77).
  - Most frequent: step repetition 17%, reasoning-action mismatch 14%, no clarification 12%, disobeying the spec 11%, unaware of termination 10%, premature termination 8%, missing or incorrect verification 7% each.
  - Prompt fixes gave only +9.4% / +15.6%.
- **AgentErrorTaxonomy / AgentDebug** (Zhu et al. 2025, 2509.25370) [v]
  - Error types: memory, reflection, planning, action, system.
  - AgentDebug finds the *earliest critical error* by counterfactual, then reruns with targeted feedback.
  - Up to +26% relative on ALFWorld, GAIA and WebShop. Errors cluster at steps 6–15.
- **TRAIL** (2505.08638) [v]: the best LLM localizes errors in whole traces only 11% of the time. This argues for narrow per-step detectors over a holistic judge.
- **Who&When** (ICML'25, 2505.00212) [v]: decisive-step attribution reaches only 14.2%.
- **AgentRx** (2602.02475) [v]
  - Builds global constraints (tool schema, policy) and per-step dynamic constraints, and checks them programmatically or with an LLM.
  - +75% step localization. Closest to our design.
- **AppWorld** (2407.18901) [v]
  - GPT-4o failures: guessing facts instead of looking them up, API misuse (hallucinated arguments or fields), partial instruction following.
  - Agents also forget state and repeat work until the budget runs out.
- **Failure as a Process** (2607.09510) [v]
  - Half of decisive errors happen by step 7, and the first visible error comes about 10 steps later.
  - 58% of decisive errors are epistemic.
  - Successful runs respond to error signals 92% of the time, failed runs 37%.
- **LOOP** (RL on AppWorld, 2502.01600) [v]. After RL the agent shows:
  - 1.6× **more** `show_api_doc` calls;
  - 30× fewer "assume" and 6× fewer "dummy";
  - 6× fewer multi-cell turns;
  - 3× fewer give-ups after a failed call.

  **Doc lookups as such should not be penalized.**

## (b) Failure analysis → automatic checks
- **HarnessFix** (2606.06324) [v]
  - Maps failures to 7 harness layers and applies scoped repairs plus regression checks.
  - **AppWorld +5.9–9.3%**, paired sign test p<0.001. This matches our V2/H1 finding that harness bugs are a first-order effect.
- **Real-time watchdog** (2608.02464) [v]
  - CUSUM monitor fitted on healthy runs; AUROC 0.75–0.89; fires 4.6 steps early.
  - **Rollback plus an explicitly named check recovers 45% of failures, versus 16% for resampling.** Success goes from 52% to 73%.
- **PrefixGuard** (2605.06455) [v]: proposes a metric set of AUPRC, recall, false-alarm rate on successes, and lead time.
- **AgentSpec** (ICSE'26, 2503.18666) [v]: a trigger / predicate / enforcement DSL, where enforcement is block, ask, or reflect.
- **Learned scorers**:
  - AgentPRM (2511.08325);
  - AgentPRM-MC (2502.10325);
  - ToolRM (2510.26167);
  - Rubrics-as-Rewards (2507.17746): decomposed binary criteria beat Likert scores, by +31% on HealthBench.

## (c) Closed loop: diagnose → rule → apply
| Method | Rule form | Effect | What helped |
|---|---|---|---|
| ExpeL (2308.10144) | Global insights | Improves with experience | Success/failure pairs |
| AutoGuide (2403.08978) | Conditional "if X, then Y" | Beats ExpeL | **State-triggered beats global** |
| AWM (2409.07429) | Induced workflows | +51% relative on WebArena | Procedural routines |
| AutoManual (2405.16247) | Case-conditioned rules | 97.4% on ALFWorld | Rules tied to concrete failures |
| ACE (2510.04618) | Itemized playbook, delta updates | AppWorld test-challenge TGC 41.5→57.3 | Detailed API-pattern bullets; avoids context collapse |
| ReasoningBank (2509.25140) | Preventive lessons | Beats memories of successes only | What not to do |

## Implications for our next rubric dimensions
1. **D1 redefined: redundant docs, not docs in general.** Fire on a lookup of an API whose doc was already read, a doc read not followed by a call to that API within 2 steps, or doc share above x% after step 10. LOOP shows that more docs correlate with success.
2. **Harness-integrity counters** (truncation, fallback): treat these as harness fixes, which V2/H1 already does.
3. **Per-item cells (D2)**: unchanged. Inject a loop template (AWM).
4. **Pre-execution schema check** against api_docs (AgentRx global constraints): precision close to 1. H1 currently only adds a hint after the error.
5. **Unprovenanced literals**: an email, ID or name that appears in neither the task nor any observation, or the words "assume", "dummy" or "placeholder" (LOOP, AppWorld "does not interact").
6. **Deliberation without action**: two or more steps with no executable state progress.
7. **Ignored error signal**: an identical retry or an unrelated action after an exception or 4xx (the 92% vs 37% gap).
8. **Budget-progress mismatch**: 60% or more of the budget used with no write call.
9. **Completion without verification**: complete_task with no read-back.

**Validation protocol**
- Use matched prefixes or per-step hazard to control for trajectory length.
- Test within task across seeds.
- Report the PrefixGuard metrics.
- Hand-label about 30 traces per detector to estimate precision.
- Freeze thresholds before testing on held-out task families.
- **Randomize nudge vs. no nudge at the moment a detector fires** (as the watchdog paper does). A detector that discriminates is not necessarily a nudge that helps; see MATH_FORMALIZATION_v1 §4.
