# STATE-CONDITIONED STRUCTURED VARIATION — Ops-3 vs Ops-6. FROZEN 2026-09-16, BEFORE ANY GENERATION.
Generation-only. No ALFWorld rollout. No Credit signal enters any prompt (current-candidate credit does
not exist at proposal time; historical credit enters only in a later closed-loop generation).
## Ops-6 = Ops-3 verbatim + three evidence-consuming operators
Explore/Refine/Compose unchanged (Ops-3 = b2_prompts.OPERATORS, sha 9ef624d222ec16f8).
Repair <- execution/failure evidence | Contrast <- strong/weak pair | Induce <- population patterns.
Ops-6 menu sha 65847a5968646899. RIDER's zero-order/GA-mutation/GA-crossover are already covered by the
first three; its first-order+Lamarckian -> Repair, DE -> Contrast, EDA/ranked-EDA/long-term memory -> Induce.
No operator budget, no bandit: the proposer chooses o_t = LLM(S_t, O) directly.
## STAGE A — state-sensitivity smoke. 5 archive-derived states x 8 proposals = 40, Ops-6, free choice.
States (parent, evidence; all from MEASURED archive entries, shas in ops6_frozen_shas.json):
  S_failure       hit40_A_ctrl_21  + real hook_effects (retry on 37% of calls, parse changed 1.9k actions)
  S_contrast      hit40_A_ctrl_21  + STRONG A_ops_08 (+17.91) vs WEAK E1_T (+0.00)
  S_population    hit40_A_ctrl_21  + top-3 (+20.15/+17.91/+17.66) and bottom-3 (-11.94/-9.95/-8.21) by unit structure
  S_exhausted     ARM HR (+15.92)  + its six real descendants (+17.2..+10.4, mean +14.55, max gain <1.3 pp) — wording truthful
  S_compositional N04 (H, +5.22)   + N03 (R, +3.73) as a second validated entry
Expected modal operator: failure->Repair, contrast->Contrast, population->Induce, exhausted->Explore, compositional->Compose.
PRIMARY: does P(o | S) move with S. KILL if one operator takes >75% of all 40 proposals AND the modal
operator is identical across all five states (collapse, the failure mode seen for coverage-state/verbose/Transform).
PROMOTE to Stage B if >=3 of 5 states have distinct modal operators AND each of Repair/Contrast/Induce has
>=3 SUBSTANTIVE uses among 40 (mechanical AST rubric in ops6_prompts.compliance: Repair = a failure-implicated
hook added/removed/rewritten vs parent; Contrast = adds a unit in STRONG\WEAK absent from parent; Induce =
adds retry_policy or HISTORY_LENGTH when the parent lacks it; no LLM judge).
Secondary: op_in_menu rate, smoke PASS rate, distinct unit-set count, novel-family rate.
## STAGE B — Ops-3 vs Ops-6, 40 v 40, IDENTICAL full state (failure+contrast+population blocks), only the menu differs.
Verified: full-state prompts differ only by the menu string (sha ops6 dee7688eaccec51d / ops3 af17b1deca03183f).
PRIMARY: evidence-consistent transformation rate = substantive Repair+Contrast+Induce uses / 40 in Ops-6, vs the
same rubric applied to Ops-3 proposals (which can only satisfy it by accident). Secondary: structural diversity,
compositional (>=2-unit) rate, smoke PASS, H+R-like structure rate. Still no behavioural evaluation.
## COST AND LAUNCH TRIGGER
At the measured $0.0076-0.012/candidate: Stage A ~$0.30-0.48; Stage B ~$0.61-0.96. Both run under the
aggregate guard. **LAUNCH TRIGGER: only after job 2349465 (S_V1 confirmation) has finished**, because guard
headroom ($6.55) is below that job's own estimate ($6.63) and any concurrent spend would trip the guard mid-pass.
Driver: ops6_generate.py (Stage A default, --stage-b for Stage B, --dry-run makes zero calls). Sha assertions
on menus, all five state prompts and both Stage-B prompts run before the first call.
## NOT IN SCOPE (frozen): Prune (belongs to Credit/inheritance, not proposal), operator bandit/budget, CliffSearch-like
arm (added only if Stage B is positive), any credit-conditioned prompt, any behavioural rollout.
