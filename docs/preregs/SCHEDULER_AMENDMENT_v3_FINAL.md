# SCHEDULER AMENDMENT v3 (FINAL until F_5) — ARM PARALLELISATION. FROZEN 2026-09-20 17:25 CDT.
Naive_t and Ours_t are independent from t=2 (own proposals, state, memory); their serial order inside one driver process
was an implementation artefact. They now run as two driver instances forked from the frozen post-round-1 state
(closedloop_state.json, untouched as the record), with independent state files, the same bounded-lookahead scheduler (v2,
L=2), the same protocol, decoding, backend and blind-test rule. Cache was copied at the fork; from then on each instance
keeps its own (only prevents re-measuring byte-identical patches; no scientific coupling).
FACTS AT THE SPLIT: Naive round 2 had COMPLETED under v2 before the stop (17:03): finalist CL_N_r2_c4, +12.50pp, LCB95
-1.04 -> COMMITTED, F_2^naive = CL_N_r2_c4 (first commit of the loop). Its consumed batch results were briefly moved to
quarantine by the stop script and restored unchanged (state already held the wins); its TESTBLIND_naive_F2 job had been
cancelled by the blanket scancel and was resubmitted identically (SLURM 2381949), unread. Ours had generated its round-2
proposals (17:03) and validated nothing: frozen as banks/ours_r2.json and reused. Credit-only: PAUSED NOW at the legal
post-round-1 checkpoint (its round-2 batch results, 20 files, quarantined unread in results/aborted_r2_lookahead_serial/;
banks/creditonly_r2.json kept); resumes after F_5. Final 3-seed confirmation deferred: watcher cancels seeds 5,6 of each
arm's round-5 blind array; F0 extra seeds skipped by env. No further execution changes until both F_5 exist.
