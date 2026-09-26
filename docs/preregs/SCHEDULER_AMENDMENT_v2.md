# SCHEDULER AMENDMENT v2 — PRIORITY-AWARE BOUNDED LOOKAHEAD. FROZEN 2026-09-20 BEFORE ANY ROUND-2 RESULT IS READ.
Supersedes v1 (full speculative prefetch, sha d7ce7ab71f92f4dd), whose premise "spare throughput >> speculative waste"
was falsified within 30 min: endpoint saturated (95 running / 194 queued, ~1440 tok/s ceiling), ~3/4 of the queued work
belonged to batches that would be masked, so masked compute was delaying frontier compute.
Scientific protocol: UNCHANGED from prereg v2.1 and Credit V1 (same manifests, seeds, budgets, sequential stopping rule,
commit rule, proposer protocol; distributional, not bitwise, equivalence as stated in v1).
Scheduling rule: each alive candidate may have at most LOOKAHEAD=2 batches in flight beyond its consumed frontier.
Loop: ensure frontier + lookahead submitted -> wait for FRONTIER batches only -> reveal in order -> apply the frozen rule
-> eliminated candidates' in-flight batches are scancel'ed -> survivors' next lookahead is enqueued. After the bank is
resolved, non-finalist survivors' lookahead is cancelled and the finalist's remaining batches are submitted at once
(required evidence). Any computed-but-unconsumed result is moved to results/masked/<label>/ and never read.
Priority order realised: current required evidence > near-frontier lookahead (L<=2) > Credit Stage-1 LOO (prefetched only
after the bank is resolved, so it never competes with a frontier) > nothing deeper.
Verification: dry-run vs the frozen sequential driver: identical decision log, F, memory, cache; submissions 188 vs 132
(sequential) vs 408 (v1). Hygiene: both instances stopped during round 2 under v1 before any round-2 result was read; all
v1 round-2 result files quarantined unread in results/aborted_r2_fullprefetch/; round-2 proposal banks reused verbatim;
restart from the saved post-round-1 states. Not touched: max_tokens, temperature/top_p/top_k, retry, batch size, thresholds.
