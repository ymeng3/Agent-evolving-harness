# CLOSED-LOOP EVOLUTION — PREREG DRAFT v0 (2026-09-16). FOR REVIEW. NOT FROZEN. NOTHING LAUNCHED.

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

## 2. ARMS — four, everything shared except inheritance
  A  NAIVE          whole-candidate gated inheritance (HarnessEvolve-style): validate K candidates,
                    commit the best whole candidate if it passes the commit rule, else keep F_t.
  B  SEMANTIC       LLM attribution + targeted mutation (EvoTool-inspired, NOT a reproduction): the
                    LLM reads the best candidate + its validation traces, names ONE unit to blame or
                    credit, and emits a single-unit edit; that edit is validated (1 pass) and committed
                    under the same rule. No behavioural counterfactuals.
  C  CREDIT-ONLY    frozen Credit V1 on the best candidate (Stage 0 free; contextual LOO; one
                    additivity probe; bounded repair) -> S*; commit S* under the same rule. The next
                    round's state carries F_{t+1} and its traces only — NO component-credit memory.
  D  CREDIT+MEMORY  = C, plus M_{t+1} receives (unit, gamma, closure, intent, outcome) records, which
                    are exposed as TEXT in the next round's proposal state (retrieve + condition; no
                    learned value predictor — the KG value-prediction line is not revived).
Shared by all arms: F_0; proposer backend (gpt-4o, T=1.0, as everywhere in this project); the
evidence-routed dedicated-operator variation of Test C with structured artifact output; K; T; the
validation slice and seed; the commit rule; the sealed slice and its seeds.

## 3. ROUND STRUCTURE, T = 3   [DECIDE: T=3 vs T=4]
Round t, per arm:
  1. STATE S_t = (F_t source, F_t validation traces/hook_effects, arm-specific memory M_t).
  2. VARIATION: K = 4 compound candidates by evidence-routed dedicated operators. Router picks the
     operator from the evidence in S_t (frozen rule: repeated inadmissible responses -> Repair;
     two validated structures in the archive -> Compose; lineage saturated -> Explore; else Induce).
     Each proposal emits DESIGN_INTENT / MECHANISM / EVIDENCE_USED / PATCH; STATIC + smoke gate.
     [DECIDE: K=4 vs K=6]
  3. ROUND-1 BANK IS SHARED: the same four candidates go to all four arms, so t=1 isolates
     inheritance exactly. From t=2 onward each arm proposes from its own (F_t, M_t): path dependence
     is the phenomenon, not a confound.
  4. VALIDATION: each candidate, 1 seed, on the 134-game validation slice. Identical across arms.
  5. INHERITANCE (the only thing that differs): A commits whole; B one-unit edit; C/D Credit V1 -> S*.
  6. COMMIT RULE (the project's frozen rule, reused): commit X if game-bootstrap LCB95 of
     Q(X) - Q(F_t) > -2 pp AND point estimate > 0; else F_{t+1} = F_t.
  7. MEMORY UPDATE: A/B/C store candidate-level (C, Q, intent); D also stores component records.
Seeds: validation seed = 1 for all in-loop passes [DECIDE: S=1 stream vs S=2 paired streams, which
doubles cost]. Sealed seeds 4/5/6 for F_0 and every F_T.

## 4. ENDPOINTS
PRIMARY   Q_sealed(F_T) per arm, 3 seeds on 140 games; trajectory Q(F_0..F_T) on validation.
  Delta_credit = Q_sealed(F_T^C) - Q_sealed(F_T^A)     game-bootstrap CI95, paired on the 140 games
  Delta_memory = Q_sealed(F_T^D) - Q_sealed(F_T^C)
  Delta_semantic = Q_sealed(F_T^C) - Q_sealed(F_T^B)   (does behavioural credit beat LLM attribution)
PROMOTE   Delta_credit > 0 with CI95 excluding 0. "Substantial" if >= 5.3 pp (the MDE floor used
          throughout). Delta_memory reported; promote memory only on its own CI.
KILL      Delta_credit <= 0 or CI includes 0 -> the closed-loop headline fails; Credit stays a
          case-study result; do NOT stack Credit ablations afterwards (diagnose the bottleneck).
MECHANISTIC SECONDARIES (explain, never decide): commits per arm; rounds where the whole candidate
failed the gate but S* passed (salvage events); units retained across rounds; negative-gamma units
removed; in D, proposals whose EVIDENCE_USED cites a memory record.

## 5. BUDGET — projected from measured anchors, subset mix, NOT parent x count
Per-pass anchors on 134 games (ledger): retry-bearing candidates $1.4-2.4; no-retry $0.35-0.55.
Loop mix assumed ~$1.5/pass mean, $2.3 p90.
  passes per round:  A 4 | B 5 | C 4+6 = 10 | D 10     -> 29/round -> 87 over T=3
  sealed:            (F_0 + 4 arms) x 3 seeds x 140/134  ~ 15.7 passes
  F_0 on validation: 3 passes;  generation: ~$1-2 total
  TOTAL ~ 106 passes  ->  **~$160 at $1.5/pass, ~$245 at $2.3 p90**
  With S=2 paired streams: roughly double.
Current: credit $98.96, guard headroom $13.00, key $1149. **The loop cannot start without a top-up
(~$150-250) and a guard raise to cover the full projection.** Three-number check at launch, guard
raised by baseline shift so all concurrent arrays share one trip point.

## 6. WHAT IS DELIBERATELY NOT IN THIS LOOP
No active/adaptive validation allocation (matched fixed budget in every arm; efficiency is a
follow-up "sealed performance vs validation cost" curve only if the headline is positive). No
random-subset search baseline (deferred ablation). No tree search. No reference trajectories. No
Credit V2 changes (probe cache and Stage-2 tolerance are implementation notes; V1 runs as frozen,
duplicates are simply not re-measured). No operator bandit. No B3.

## 7. REQUIRED BEFORE FREEZE
  [ ] user decides: T, K, S, and whether B (Semantic) is in the first batch or deferred
  [ ] BOS_MANIFEST override applied and freeze-echoed
  [ ] slices written and sha'd; F_0 measured on both (6 passes, ~$3-5)
  [ ] loop driver written; dry-run with zero API calls; per-arm sha assertions
  [ ] Semantic-arm prompt and memory serialisation frozen and sha'd
  [ ] top-up and guard raise
