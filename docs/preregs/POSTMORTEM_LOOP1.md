# POSTMORTEM — CLOSED LOOP 1 (Local-v2 regime, prereg v2.1). 2026-09-21. Zero-cost, computed from logs/states/results.
HEADLINE: Q_blind(F5 ours) - Q_blind(F5 naive) = +2.86 pp, CI95 [-5.00, +10.71] (single seed). No separation.
THREE DIAGNOSTIC LAYERS
1. Candidate compoundness (36 proposed candidates, both arms, rounds 1-5):
     |C|=1: 22%   |C|=2: 50%   |C|=3: 25%   |C|>=4: 3%   (median 2). Finalists: naive 2,2,2,3,2; ours 3,3,5,1.
   -> The proposer (Induce/Explore/Repair operators, gpt-4o) mostly emits 1-2 unit edits. With |C|<=2 component credit
      nearly degenerates to candidate fitness. The G_MECH07-type opportunity (3 units, +/- mixed) appeared in 2/5 rounds.
2. Credit opportunity (Ours, per round): S* != C in 2/5 rounds (r3 dropped TEMPERATURE gamma -4.2; r4 dropped parse_action
   gamma -7.3). Q(S*)-Q(C) = +4.17 [-10.4,+18.8] and +7.29 [-8.3,+21.9]. Per-unit gamma CI95 half-width ~ +/-15 pp at n=96
   (e.g. retry_policy +14.6 [+1.0,+29.2]; HISTORY_LENGTH +13.5 [0.0,+28.1]). Only 2 of 13 measured units have a CI excluding 0.
   -> Credit found the right sign in the point estimates, but a single 96-game LOO probe cannot resolve a unit whose true
      effect is < ~15 pp. This is "opportunity exists but is not estimable at this n", not "no opportunity".
3. Gate suppression: both S* != C cases were then rejected by the whole-state gate: Q(S*)-Q(F_t) = +3.12 [-6.25,+12.50] and
   +4.17 [-4.17,+12.50] (rule: LCB95 > -2 and point > 0). The gate is deterministic (seeded bootstrap; 20/20 re-draws agree);
   at n=96 it needs roughly +12 pp to pass; both commits in the loop were exactly +12.50 (naive r2 LCB -1.04 PASS; ours r2
   +12.50 LCB -2.08 REJECT — same point, different per-game pattern). Ours' only commit (r5) is a 1-unit random fallback.
OFFLINE REPLAY of a component-level rule (unit-sign + S* point > 0, no LCB): would have inherited in r1, r2, r3, r4 —
   i.e. it is effectively "commit anything with point > 0", which under +/-8 pp evaluation noise is noise-chasing; the
   replay cannot be continued past the first divergence (F_t would change). A per-unit LCB rule inherits nothing (all unit
   CIs span 0). -> Changing the gate alone does not create a resolvable signal; it trades false negatives for false positives.
VERDICT: three coupled bottlenecks, in order of leverage:
   (a) evaluation noise vs effect size: n=96 single-seed gives +/-8 pp on candidates and +/-15 pp on units; typical unit
       effects here are 1-7 pp. Credit V1 as run is below its own resolution.
   (b) low compoundness: median |C| = 2; the method's opportunity (mixed-sign compounds) occurred in 2/5 rounds.
   (c) whole-state gate on top of component credit: fine-grained diagnosis, coarse-grained inheritance.
   Not a bottleneck: infrastructure (all in-loop passes clean), the estimator's logic (signs right where measurable),
   memory/reuse (never reached: nothing credible to reuse).
IMPLICATION FOR LOOP 2 (design, not yet prereg'd): (1) make the unit the object of evaluation budget: allocate probes until
   the unit's CI excludes 0 or a cap (unit-level sequential test), rather than one 96-game pass per unit; (2) a compound
   proposal regime (operator that composes >=3 credited/novel units, or K candidates x forced multi-unit) so credit has
   opportunities every round; (3) inheritance at unit level with a unit-level evidence gate, replacing the whole-state LCB
   gate. Relational memory/graph is deferred until credible unit-level events exist to accumulate.
