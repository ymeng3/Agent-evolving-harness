batch4 tasks: 3f3c139_1 09ac073_1 dc5c5c6_1 e52623a_1 f86d850_1 ba46d91_1

- 3f3c139_1 (delete expired cards from every app; mixed). All 3 failures [I,A,(G,B,J),endgame]: serial per-app with a separate cell per step (~6-8 cells per app); deletions done by c26-29, then verification/re-discovery instead of complete_task; orig had goal checks 0.8 already. seed2 rebound the name `apis` to a list (broke session). seed3 harness ran a literal '...' (3 cells to recover). Success: docs, logins, fetches batched across apps in loops (cells 7-10), completed at c20.
- 09ac073_1 (archive read threads except priority/starred; mixed). seed2 [B,J,G]: literal access_token=... placeholder poisoned the session (same ValueError on every later cell, even `pass`). seed3/seed5 [J,...]: archive returned success but re-reads showed nothing archived -> investigation / retry loops (ENV read-after-write inconsistency). Successes archived and completed immediately without re-reading.
- dc5c5c6_1 (top-rated controller gift-wrapped per sibling; always fails). All 3 [A,I,(B)]: ~18 single doc cells, access_token to no-auth search APIs, guessed add_to_cart, truncated API list.
- e52623a_1 (relabel priority-1/2 to P1/P2; always fails). All 3 [J,...]: label write reverts on later reads (ENV persistence anomaly); seed2 verified correct state and completed but evaluator gave 0.5 — agent state vs evaluator mismatch. Task likely broken / needs env audit.
- f86d850_1 (buy vase for Debra, forward receipt, Venmo request; always fails). orig [J,A,I,B]: 5 cells lost to unclosed fences -> silent fallback; fix [A,I]: 16 single doc cells; disc2 [K:deliberation-paralysis,J,G,E]: 11 code-less turns debating whether clearing the cart is collateral damage, fallback substituted each time.
- ba46d91_1 (days left on Spotify premium; always fails). All 6 runs answered round(335.9999)=336; evaluator rejects; calendar-day difference 335 is probably the convention — ANSWER-CONVENTION / ground-truth issue, not process.

BATCH PATTERNS:
1. One api_docs lookup per cell eats 40-60% of budget; fatal on multi-app tasks; successes batch docs/logins/fetches across apps.
2. No budget awareness at the end (verify / re-discover instead of complete_task).
3. Harness code-extraction artifacts silently waste cells (fallback on unclosed/missing fence; draft/placeholder from reasoning executed; prose executed). Harness should take the last closed block, reject bare '...', return explicit 'no code found' without charging a cell.
4. Ellipsis placeholders poison the session (identical ValueError thereafter) -> need pre-execution check + REPL reset on repeated identical errors.
5. Gmail thread writes do not stay put (env/isolation issue) -> verification/retry loops; e52623a fails evaluation even after verified state.
6. Cheap API misuse: access_token on public search APIs; page_limit > 20; guessed API names from truncated listings.
7. Deliberation paralysis on safety/collateral rules (no-code turns).
8. Answer-convention mismatch (ba46d91: every seed 336, likely expected 335).
