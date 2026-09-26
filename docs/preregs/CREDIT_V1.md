# CREDIT ALGORITHM V1 — FROZEN 2026-09-15, BEFORE ANY OUTCOME ON ANY m=5-6 HOST IS KNOWN
No behavioural evaluation has been run on any of the ten census hosts except the two already-measured
positives (P08_stack +13.93, armC30_A_whole_19 +5.22), neither of which is the prospective host.
Every rule below is fixed now. Nothing in it may be chosen after seeing a result.

## INPUT
A compound executable update C, given as source. Nothing else. No score is required as input.

## STAGE 0 — UNITS, DEPENDENCY CLOSURE, VALIDITY.  ZERO COST, NO API.
U(C) = {each top-level hook def} u {each module constant}, with ONE merge rule: a TEMPERATURE
constant is not a separate unit when retry_policy also sets temperature internally (one two-site
intervention). Recorded because this merge fired in 35 of 51 archive candidates.
VALIDITY PREDICATE  V(S) := smoke(S) == "PASS", i.e. every declared hook is invoked, none raises, and
none has zero effect. "Zero effect" is included deliberately: N06's format_prompt does not crash when
its writer is removed, it goes SILENTLY INERT, and a crash-only test would have missed it.
DEPENDENCY CLOSURE  A_i := {e_i} u {e_j : V(C \ {e_i}) holds only if e_j is also removed}, computed by
smoke over C \ {e_i} and repaired minimally. Ablatable units := {i : V(C \ A_i) and A_i != U}.
Units whose closure is all of U are UN-ABLATABLE, excluded, and reported as such.
OUTPUT of Stage 0: the ablatable set, k = its size, and the valid lattice. All free.

## STAGE 1 — CONTEXTUAL LEAVE-ONE-OUT.  1 + k PROBES.
Measure Q(C) and Q(C \ A_i) for every ablatable i.
  gamma_i := Q(C) - Q(C \ A_i).     gamma_i < 0 means removing A_i HELPS.
Contextual, not standalone. Standalone credit is known in this project to mislead about composition
(retry standalone CIs contain zero yet it contributes +6.72..+12.69), so standalone is never used.

## STAGE 2 — ADDITIVITY VERIFICATION.  EXACTLY 1 PROBE. THIS IS THE STEP THAT MAKES V1 AN ALGORITHM.
D := {i : gamma_i < 0}.  If D is empty, output C and stop.
Otherwise measure Q(C \ union_{i in D} A_i) =: Q(S_joint).
RATIONALE, REGISTERED: dropping every individually-negative unit ASSUMES ADDITIVITY, and this
project's own data says that assumption fails. Stage 2 tests it once instead of assuming it. The
G_MECH07 arm did not have this step; it got away with it because the joint drop happened to be the
exhaustive argmax. V1 does not rely on that luck.

## STAGE 3 — BOUNDED REPAIR.  FIRES ONLY IF STAGE 2 REGRESSED.  AT MOST |D| PROBES.
If Q(S_joint) >= max(Q(C), max_i Q(C \ A_i)), skip Stage 3.
Otherwise masking/antagonism is demonstrated (two units were jointly load-bearing though each looked
droppable). Probe the add-backs Q(S_joint u A_i) for each i in D, and stop.

## OUTPUT
S_credit := argmax of Q over EVERY configuration measured in Stages 1-3, including C itself.
B_credit := the number of probes actually consumed = 1 + k + 1 + (0 or |D|).
For m=6 with k=6: B_credit is 8 in the additive case, up to 14 with full repair.

## BUDGET-MATCHED UNINFORMED BASELINE — FROZEN NOW
S_search := argmax of Q over B_credit distinct valid proper subsets drawn UNIFORMLY at random from
the Stage-0 valid lattice, numpy default_rng(20260915), same seed count per probe as the credit arm.
B_search := B_credit exactly. The draw is seeded and is made once B_credit is known; it is independent
of every measured outcome.

## FINAL COMPARISON — FRESH SEEDS, AS IN THE G_MECH07 ARM
Both finalists re-evaluated on seeds not used in discovery. Discovery seeds may never be reused.
PRIMARY   Q(S_credit) - Q(S_search) on fresh seeds, game-bootstrap CI95.
CONTROL 1 Q(S_credit) - Q(C): did credit actually improve on the compound at all.
CONTROL 2 regret against the full-lattice oracle, reported only where the full lattice is affordable.
DEFENSIBILITY FLOOR: 5.3 pp, the same MDE arithmetic as the G_MECH07 arm (3-seed configs, SE of a
difference about 2.7 pp). A margin below 5.3 pp is NOT a positive and may not be presented as one.

## KILL CRITERION
KILL if Q(S_credit) - Q(S_search) <= 0, or its CI95 contains zero. In that case credit has
explanatory value but no search advantage, and the method headline drops to the G_MECH07 case study.
Also KILL if Q(S_credit) <= Q(C): no salvage occurred at all.

## WHAT V1 DELIBERATELY DOES NOT CLAIM
Not "we beat exponential enumeration". The census showed the largest natural host in 628 archive
patches has m=6, so the full lattice is 63, not 255. A <=14-probe budget against ~62 valid subsets is
about a 5x compression. The claim is VALID AND ACTIONABLE CREDIT UNDER DEPENDENCIES AND INTERACTIONS,
with the compression as a secondary consequence. This concession is frozen here so it cannot be
quietly upgraded after a positive result.

---

## AMENDMENT 1 to STAGE 0 — MADE 2026-09-15, BEFORE ANY BEHAVIOURAL OUTCOME ON ANY PROSPECTIVE HOST
Reason: the validity predicate `smoke(S) == PASS` is only as good as the fixture's branch coverage.
A branch the scripted 6-step episode never reaches is invisible to it. Demonstrated concretely:
armD_02's `choose_fallback` contains `admissible[random.randint(...)]` with **`random` never imported**;
that branch fires only when `loop_detected` is True, which `memory_update` sets after three identical
consecutive actions -- reachable in real episodes, not reachable in the fixture. Smoke calls it PASS.

**STAGE 0 NOW ALSO REQUIRES A FREE STATIC CHECK, applied to the compound C AND to every counterfactual:**
  STATIC(S) := S contains no Load of a name that is not a builtin, a module-level binding, an import,
  a function parameter, or a local binding in the enclosing scope.
  V(S) := smoke(S) == "PASS"  AND  STATIC(S).
Measured coverage of this addition over the 628-patch archive: 46 patches reference an undefined name;
smoke already catches 37 (CRASH) and 4 (PARTIAL); **the static check adds the remaining 5 that smoke
calls PASS.** Cost: zero, no API, pure AST.

**IF THE COMPOUND C ITSELF FAILS V(C), V1 DECLARES IT NON-ANALYSABLE AND REFUSES TO PROCEED.**
Rationale: credit measured on a parent with a reachable silent-failure branch is uninterpretable --
one cannot separate "unit X is harmful" from "unit X triggers another unit's swallowed exception".
V1 reports the defect and the host is rejected. It does NOT attempt repair, because repairing the
artifact would make it no longer the artifact the loop actually produced.
