# CLOSED-LOOP EVOLUTION — PREREG v2 (2026-09-16). FINAL DESIGN FOR APPROVAL. NOTHING LAUNCHED.

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

## 3. ROUND STRUCTURE — T = 5, K = 4, S = 1, n_val = 96. FIXED. NO CONDITIONAL EXTENSION.
T=5 fixed from the start (conditional extension REJECTED: horizon must not depend on outcome).
VALIDATION SLICE = 96 games from `train`, hash-fixed (96 lowest sha256(path)). ONE slice for EVERY
in-loop decision — candidate validation AND Credit probes. No dual scale (a 96/64 split was considered
and rejected: it would make a bad inheritance unattributable between "Credit failed" and "Credit's
evidence was thinner"). Single-seed SE at p~.5 is ~5.1 pp (vs 4.3 at 134, 6.25 at 64).
Round t, per arm:
  1. STATE S_t = (F_t source, F_t validation traces/hook_effects, arm memory M_t).
  2. VARIATION: K=4 compound candidates, evidence-routed dedicated operators (frozen router: repeated
     inadmissible responses -> Repair; two validated structures in archive -> Compose; lineage saturated
     -> Explore; else Induce). DESIGN_INTENT/MECHANISM/EVIDENCE_USED/PATCH; STATIC + smoke gate.
  3. ROUND-1 BANK SHARED across both arms and validated ONCE (t=1 isolates inheritance). t>=2: each arm
     proposes from its own (F_t, M_t).
  4. CANDIDATE VALIDATION with the FROZEN EVIDENCE-EFFICIENT POLICY, identical in both arms (section 3a).
  5. FINALIST: C_t* = argmax_i Q_val(C_i) among survivors. **Credit is applied to the FINALIST ONLY.**
     This is the algorithm, not a cost hack: Credit answers "given the candidate evolution would
     otherwise inherit, what inside it deserves to survive?" — not exhaustive attribution over the bank.
  6. INHERITANCE: Naive commits C_t* whole. Ours runs frozen Credit V1 on C_t*: Stage 0 free; LOO 1 seed
     on the 96 slice; 1 additivity probe; **Stage 3 capped at 1 unique extra probe** (computational
     budget spec, frozen now; the pilot needed 0); Q(C_t*) reused from step 4; already-measured
     executable configs never re-measured -> S_t*; commit S_t* under the same rule.
  7. COMMIT RULE, UNCHANGED, BOTH ARMS: point estimate Q(X) - Q(F_t) > 0 AND game-bootstrap LCB95 > -2 pp.
  8. MEMORY: Naive stores (C, Q, intent, traces); Ours also stores (unit, gamma, closure, intent, outcome).
Seeds: validation seed 1 for every in-loop pass. ONE evolution stream. No in-loop multi-seeding.

## 3a. EVIDENCE-EFFICIENT VALIDATION — $0 PROTOCOL AUDIT RESULT, and what is and is not applied
Audited the only frozen instantiation on record (Line A prereg, registry ~8063): batches of 9
validation games per surviving candidate in a per-candidate seeded random order; after each batch drop
a candidate if UCB(z=1.0) < best LCB or UCB < F_0 - 2 pp; continue survivors; stop when one candidate
remains, all survivors exhaust n_val, or the stability stop fires (survivor order unchanged for two
consecutive batches AND leader LCB > runner-up UCB).
  PROSPECTIVELY APPLICABLE TO CANDIDATE SELECTION: YES. Every input (batch UCB/LCB, F_0 on the same
  slice, survivor ordering) exists at decision time; z was fixed at 1.0 in that prereg; NO threshold is
  retuned here. It is therefore APPLIED, IDENTICALLY IN BOTH ARMS, to step 4 above. Expected saving
  roughly a third of candidate-validation passes (ST0 replay: matched quality at ~22-42% of cost, CIs
  wide). Its effect on Q is expected to be ~0; it is shared infrastructure, never an arm difference.
  NOT APPLICABLE TO CREDIT PROBES: a Credit probe decides the SIGN of gamma_i = Q(C) - Q(C\A_i), a
  counterfactual-vs-parent difference. The frozen rule compares candidates to the best survivor and to
  F_0; no stopping rule for a difference sign was ever frozen. Inventing one now is exactly what the
  user's criterion forbids. **Credit probes run the full 96 games.**
  Adaptive stopping has replay-level evidence only (never fresh-confirmed); it enters here as cost
  infrastructure, not as a claim. If a future efficiency claim is wanted it is a separate experiment.

## 4. ENDPOINTS
PRIMARY   Delta_5 = Q_test(F_5^Ours) - Q_test(F_5^Naive), 3 seeds x 140 valid_seen, game-bootstrap CI95
          PAIRED on the same games and seeds.
PROMOTE   Delta_5 > 0 with CI95 excluding 0; "substantial" if >= 5.3 pp.
KILL      Delta_5 <= 0 or CI includes 0 -> headline fails; Credit stays a case-study result; diagnose;
          do NOT rescue with a second stream.
LONGITUDINAL (pre-specified, descriptive): Q_test(F_t) for t=0..5, both arms, drawn as the evolution
          curve; Delta_t = Q_test(F_t^O) - Q_test(F_t^N). Q_val(F_t) reported alongside.
THREE MECHANISM COUNTERS, per round, explain the gap, never decide it:
  N_salvage    rounds where C_t* FAILED the commit rule but S_t* PASSED it
  N_hitchhiker negative-gamma units removed before inheritance
  N_reuse      later proposals whose EVIDENCE_USED cites a prior relational-credit record AND whose
               patch changes the cited unit (mechanical check)

## 4a. TEST-SET PROTOCOL — PER-ROUND, BLIND, READ-ONLY. It is no longer called "sealed".
`valid_seen` (140) is a HELD-OUT LONGITUDINAL EVALUATION SET. After each round's parent is fixed,
F_t^N and F_t^O are evaluated on it automatically and the scores are WRITTEN BUT NOT DISPLAYED
(results/testblind/*.json, read by no code path in the loop). No test score may enter S_{t+1},
variation, validation, Credit, memory, or the commit rule. NO protocol change of any kind after the
first test pass has run. Unblinding happens once, after F_5 for both arms exists.
  seeds:  F_0: 1 seed at start, +2 seeds at the end (3 total)
          F_1..F_4, both arms: 1 seed each (descriptive trajectory)
          F_5, both arms: 3 seeds (primary)
(A visible-per-round variant was considered and rejected: a human reading round-2 test scores is part
of the optimisation loop even if the code is not.)

## 5. BUDGET — exact config, measured 134-game anchors scaled by slice size
Tiers: typical $1.50/134-game pass, retry-bearing p90 $2.30. V = 96/134, Tst = 140/134.
  candidate validation  2 arms x 5 rounds x 4 x V     = 28.7 pass-equiv (t=1 bank shared: -2.9)
  Credit, finalist only 5 x (LOO 4 + add 1 + S3 <=1) x V = 21.5
  blind test            F0 + 8 x (1 seed) + 2 x 3 seeds + F0 +2, all x Tst = 17.8
  fixed                 freeze-echo 1 + F0 on validation 3 x V = 3.1
  generation            ~$1
  **fixed-96 total: ~71 pass-equiv -> ~$108 typical / ~$164 p90**
  **with the frozen stopping policy on candidate validation (~35% of those passes): ~61 -> ~$93 / ~$141**
  Credit-on-all-K instead of finalist-only would ADD ~64 pass-equiv (x4 on the Credit line): rejected.
Current: credit $98.96, guard headroom $13.00. Typical fits the account with stopping; p90 needs
~$45 more. Guard must be raised by baseline shift to cover the p90 figure under one trip point.

## 6. WHAT IS DELIBERATELY NOT IN THIS LOOP
No active/adaptive validation allocation (matched fixed budget in every arm; efficiency is a
follow-up "sealed performance vs validation cost" curve only if the headline is positive). No
random-subset search baseline (deferred ablation). No tree search. No reference trajectories. No
Credit V2 changes (probe cache and Stage-2 tolerance are implementation notes; V1 runs as frozen,
duplicates are simply not re-measured). No operator bandit. No B3.

## 7. REQUIRED BEFORE FREEZE (v2)
  [x] arms 2; S=1; K=4; T=5; n_val=96 single slice; finalist-only Credit; Stage3<=1; frozen stopping
      on candidate validation only; per-round BLIND test; Q(F_3) reported — ALL DECIDED
  [ ] user approves budget (~$93-141) and tops up to cover p90
  [ ] BOS_MANIFEST env override; freeze echo (default-manifest F0 reproduces registered numbers)
  [ ] slices written + sha'd (validation_train96, test_validseen140); F_0 on validation 3 seeds; F_0 on test 1 seed
  [ ] loop driver: two arms; router + operator prompt shas asserted per round; probe cache; memory
      serialisation; blind test writer with NO reader; dry-run with zero API calls
  [ ] guard raised; three-number check; single launch
