# CLOSED-LOOP EVOLUTION — PREREG v1 (2026-09-16). USER DECISIONS APPLIED. FROZEN ON APPROVAL. NOTHING LAUNCHED.

Status: draft for the user's review. Becomes frozen only after review, by writing its sha into the
ledger. Every number below is either a measured anchor (cited) or a proposal marked [DECIDE].

## 0. THE QUESTION, IN ONE LINE
Does behavioural evolutionary credit + selective inheritance let useful structure accumulate across
rounds, where whole-candidate fitness either discards or inherits compound updates wholesale?

## 1. DATA — three disjoint pools, the clean one single-use
The 134-game `valid_unseen` manifest (sha 5a24f0700f672b93) has been the evaluation pool for the
ENTIRE project and is SPENT as a sealed set. `valid_seen` (140 playable) has never been opened.
`train` (3553 playable) has never been used.
  VALIDATION   = 134 games from `train`, hash-fixed: the 134 lowest sha256(game path). Same size as
                 every cost anchor in the ledger, so per-pass costs transfer directly. Used for all
                 in-loop evaluation: candidate scores, Credit probes, commit decisions, proposer
                 evidence (traces of the current frontier on this slice).
  SEALED       = all 140 `valid_seen` games. SINGLE-USE. Evaluated only for F_0 and each arm's F_T.
                 Never opened during evolution; no arm, prompt, or decision may read it.
  F_0 on both slices must be measured before the loop (3 seeds each).
REQUIRED CODE CHANGE (engineering, not method): `MANIFEST` is hard-coded in bos_alfworld.py. Add
`MANIFEST = os.environ.get("BOS_MANIFEST", <current default>)`; default behaviour unchanged, verified
by a freeze echo (an F0 pass on the default manifest reproduces the registered numbers before any
loop run). Slice lists written to `slices/{validation_train134,sealed_validseen140}.txt` with shas.

## 2. ARMS — TWO. Everything shared except inheritance and what memory carries.
  NAIVE  S_t -> C_t (K=4) -> Q(C_t) on validation -> commit the best WHOLE candidate under the rule, else keep F_t.
         Memory: candidate-level history only (candidate, intent, score, failure traces) — the ordinary
         evolution history a proposer needs. NO component credit / dependency / interaction records.
  OURS   S_t -> C_t (K=4, same machinery) -> Q(C_t) -> frozen Credit V1 on the best candidate -> S_t* ->
         commit S_t* under the SAME rule, else keep F_t. Relational memory M_t = {(unit, gamma, closure,
         intent, context, outcome)} exposed as TEXT in the next round's proposal state (retrieve + condition;
         no learned value predictor).
  HEADLINE COMPARISON = whole-update fitness + whole inheritance  vs  component evidence + selective
  inheritance + reuse. A SYSTEM-level comparison. It does NOT isolate Credit from memory; Semantic and
  Credit-only arms are DEFERRED to a decomposition batch that runs only if this headline is positive.
  COMPARISON TYPE = PROPOSAL-MATCHED, NOT EQUAL-COMPUTE: both arms get K=4 proposals/round and identical
  candidate validation; Ours additionally pays its Credit probes. Total rollouts / tokens / $ per arm are
  RECORDED so a matched-budget robustness run can follow if Ours is positive. This may not be written as
  "equal-compute superiority".
Shared: F_0; proposer backend; the Test-C evidence-routed dedicated-operator variation with structured
artifact; K; T; validation slice and seed; commit rule; sealed slice and seeds; round-1 proposal bank.

## 3. ROUND STRUCTURE — T = 5, K = 4, S = 1. FIXED. NO CONDITIONAL EXTENSION.
The conditional "extend to T=5 if a parent changed" rule was considered and REJECTED: it makes the
horizon depend on the outcome. T=5 is fixed from the start; Q(F_3) is a PRE-SPECIFIED SECONDARY
reporting point (early horizon), Q(F_5) is PRIMARY. The question memory is meant to answer is whether
the advantage grows with accumulated evidence, so the trajectory F_0..F_5 on validation is reported.
Round t, per arm:
  1. STATE S_t = (F_t source, F_t validation traces/hook_effects, arm memory M_t).
  2. VARIATION: K=4 compound candidates by evidence-routed dedicated operators (frozen router: repeated
     inadmissible responses -> Repair; two validated structures in the archive -> Compose; lineage
     saturated -> Explore; else Induce). DESIGN_INTENT/MECHANISM/EVIDENCE_USED/PATCH; STATIC+smoke gate.
  3. ROUND-1 BANK SHARED across both arms (t=1 isolates inheritance). t>=2: each arm proposes from its
     own (F_t, M_t); divergence is the phenomenon.
  4. VALIDATION: each candidate 1 seed (seed 1) on the 134-game train slice. Identical in both arms.
     FIXED, MATCHED. No adaptive acquisition anywhere in this experiment.
  5. INHERITANCE: Naive commits the best whole candidate; Ours runs Credit V1 on the best candidate
     (Stage 0 free; LOO 1 seed; 1 additivity probe; bounded repair; already-measured configs reused,
     never re-measured) and commits S_t*.
  6. COMMIT RULE, UNCHANGED, BOTH ARMS: point estimate Q(X)-Q(F_t) > 0 AND game-bootstrap LCB95 > -2 pp.
  7. MEMORY: Naive stores (C, Q, intent, traces); Ours also stores component records.
Sealed seeds 4/5/6 for F_0 and both F_5. Validation seed 1 throughout.

## 4. ENDPOINTS
PRIMARY   Delta_loop = Q_sealed(F_5^Ours) - Q_sealed(F_5^Naive), 3 seeds x 140 games, game-bootstrap
          CI95 PAIRED on the same games and seeds.
SECONDARY (pre-specified) Q_sealed(F_0) as the common origin; validation trajectory Q_val(F_0..F_5) per
          arm; Q_val(F_3) as the early-horizon reporting point.
PROMOTE   Delta_loop > 0 with CI95 excluding 0; "substantial" if >= 5.3 pp.
KILL      Delta_loop <= 0 or CI includes 0 -> the closed-loop headline fails; Credit remains a case-study
          result; diagnose the bottleneck; do NOT rescue with S=2.
THREE MECHANISM COUNTERS, recorded every round, explain the gap, never decide it:
  N_salvage    rounds where the best whole candidate FAILED the commit rule but S* PASSED it
  N_hitchhiker negative-gamma units removed before inheritance
  N_reuse      later proposals whose EVIDENCE_USED substantively cites a prior relational-credit record
               (mechanical check: the cited unit appears in M_t AND is changed in the patch)
SEALED DISCIPLINE: valid_seen is opened exactly once, for F_0, F_5^Naive, F_5^Ours. NO per-round sealed
evaluation. Evolution curves are drawn on the validation slice only.

## 5. BUDGET — recomputed for 2 arms, T=5, K=4, S=1, from measured 134-game anchors
Tiers (output length drives per-pass cost ~7x): no-retry $0.55 | typical $1.50 | retry-bearing p90 $2.30.
  Naive: 20 validation passes.  Ours: 20 + 5 x (LOO 4 + additivity 1 + repair 0-2) = 45-55 passes.
  Fixed: freeze-echo F0 1 + F0 validation 3 + F0 sealed 3x(140/134) + F_5 x 2 arms x 3 seeds x (140/134) = 13.4
  Generation ~$1.
  **T=5: 78-88 passes -> ~$119-134 (typical) / ~$181-204 (p90).**
    T=3: 52-58 passes -> ~$80-89 (typical) / ~$122-135 (p90).
Current: credit $98.96, guard headroom $13.00. **T=5 needs a top-up of ~$100 (typical) to ~$150 (p90)
and a guard raise by baseline shift to cover the full projection under one trip point.**

## 6. WHAT IS DELIBERATELY NOT IN THIS LOOP
No active/adaptive validation allocation (matched fixed budget in every arm; efficiency is a
follow-up "sealed performance vs validation cost" curve only if the headline is positive). No
random-subset search baseline (deferred ablation). No tree search. No reference trajectories. No
Credit V2 changes (probe cache and Stage-2 tolerance are implementation notes; V1 runs as frozen,
duplicates are simply not re-measured). No operator bandit. No B3.

## 7. REQUIRED BEFORE FREEZE (v1)
  [x] arms = 2 (Naive, Ours); S=1; K=4; T=5 fixed; proposal-matched; sealed F_0/F_5 only — DECIDED
  [ ] user approves the cost (T=5 vs T=3) and tops up
  [ ] BOS_MANIFEST env override applied to bos_alfworld.py; freeze echo: F0 on the default manifest
      reproduces the registered 3-seed numbers before any loop pass
  [ ] slices written and sha'd (validation_train134, sealed_validseen140); F_0 on both (6 passes)
  [ ] loop driver written: two arms, per-round sha assertions on router/operator prompts, memory
      serialisation for Ours, probe cache (already-measured configs reused), dry-run with zero calls
  [ ] guard raised; three-number check; launch as one job
