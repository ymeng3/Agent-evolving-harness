# OVERNIGHT DECISION TREE — FROZEN 2026-09-21 23:00 CDT, BEFORE ANY SEED-2 RESULT IS READ (0 of 7 files existed at freeze).
STEP 0  Seed-2 pooled analysis (192 paired episodes; F0 = LQD_F0 seeds 1-2; rule delta=3pp/90%). Endpoints as registered:
        E1 ours_r4: C\HISTORY is KEEP AND C is not KEEP.   E2 ours_r6: choose_fallback is DROP (gamma < -3 with 90%).
        GATE: E1 or E2 holds -> continue. Neither -> STOP; write verdict; nothing else launched.
STEP 1  Loop-2 pilot, ROUND 1 ONLY (paired): same parent F0, one shared K=4 bank from the DEDICATED COMPOSE operator
        (P1a' text verbatim; mechanism pool at round 1 = the 9 Loop-1 finalists with their validation deltas and Credit
        gammas, identical for both arms), same validation (Line-A stopping, batches of 9, lookahead 2), same finalist,
        same commit rule. Arm W (whole) inherits the finalist as a unit; arm K (credit) applies frozen Credit V1 to the
        same finalist. Blind tests per round as in v2.1 (1 seed). Namespace: tags L2_*, TESTBLIND_L2_*, own state/patch dirs.
        Everything else = prereg v2.1 + amendments (local backend, explicit decoding, bounded lookahead).
STEP 2  After round 1: CREDIT EVENT := arm K's S* != C (hitchhikers_removed >= 1 or salvage) — i.e. Credit changed the
        inherited artifact or the decision. No event -> STOP after round 1. Event -> run round 2 (arms now diverge).
STEP 3  After round 2: continue to round 3 only if a credit event occurred in round 2 as well ("persistent divergence").
        Hard stop after round 3. T=3 is never launched unconditionally.
ENGINEERING GATE before any GPU pass: driver dry-run with the new switches must complete rounds 1-3 with zero API calls;
        round-1 proposals are generated ($~0.1) and must pass static+smoke for >= 2 of 4 before validation is submitted.
PRIMARY MECHANISTIC ENDPOINT of the pilot: number of rounds with a credit event and its kind (reject->keep, or harmful
        hitchhiker removed). Q(F_3) contrasts are secondary and single-seed. Estimated wall time: R1 ~4-5 h; each further
        round ~5 h (two arms in one process, serial) -> worst case ~15 h.
