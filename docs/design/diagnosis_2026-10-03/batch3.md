batch3 tasks: c1091c7_1 953b296_1 5800354_1 ac62177_1 c8f5f44_1 7574325_1

- c1091c7_1 (disable alarms for meetings canceled by email; mixed). disc2 [A,I,per-item]: 13 doc cells, coworker-contacts detour, show_thread one per cell. disc3 [C,H]: built the cancellation set from keyword searches only, missed Stephen's reworded email ('Skip this time? ... Cannot make it'), completed 0.67. disc4 [A,G,C,I]: kept re-searching with new keywords; each returned the same 217-thread whole inbox (query ranks, does not filter). Successes: listed threads by date window, read all candidates in one cell, disabled all in one cell. Batching, not fewer lookups, made the difference.
- 953b296_1 (XL t-shirt with no fading reports; mixed). orig [A,I,J]: same batched fading check as the success, then checkout one call per cell + supervisor address/card detour; fallback at c17. disc2 [A,I,B]: overhead alone (18 doc cells, access_token error). disc3 [A,I,D,per-item]: per-candidate copy-pasted cells. Success: one helper paged reviews/QAs for all 6 candidates; cards+addresses in one cell.
- 5800354_1 (return roommate's Amazon item, Venmo the money; always fails). orig [A,I,over-verification]: return started c19, then 3 cells verifying the Venmo user through phone contacts; never paid. fix [F,A,I]: hard-coded the wrong Venmo password, re-fetched passwords. disc2 [A,I,ambiguity-hunt]: searched past Venmo transactions to decide an amount it already had (paid_amount 389.89).
- ac62177_1 (unspam coworkers' threads, mark unread, delete other spam; always fails). orig [J,B,A]: truncated Gmail API list hid mark_thread_not_spam; 5 fallback cells. fix/disc2 [B,J,I,A]: batched writes rolled back when mark_thread_unread raised 422 on an already-unread thread (whole cell's writes undone); disc2 verified at c29 instead of complete_task.
- c8f5f44_1 (order item brother paid for on Venmo, comment thanks; always fails). orig [A,I,B]: 20 doc cells, supervisor address (no address_id), guessed add_to_cart. fix [D,A,J,I]: looked for address IDs in supervisor data. disc2 [J,A,I,B]: stray reasoning text executed as code (syntax errors), access_token error.
- 7574325_1 (change Venmo password; always "fails" at 0.8). All 3 [H,J,K:blind-retry-after-4xx]: took the newest reset email's code, reset_password 4xx, requested a second code without reading the error, succeeded, completed with 4/5 checks — systematic 1/5 failed check (extra reset request or env quirk).

BATCH PATTERNS:
1. Doc overhead: 9-11 of the first 16 cells and 10-21 of 30 are api_docs calls in every run, successes included; overhead alone exhausted the budget in 953b296, 5800354, c8f5f44.
2. Per-item cells vs batched loops = clearest split between success and failure in mixed tasks.
3. Search queries RANK but do not FILTER (217 threads for any query); agents re-search with new keywords or trust keyword hits and miss reworded items; date/sender filters + Python filtering worked.
4. Harness code extraction loses cells (fallback show_app_descriptions; reasoning text executed; JSON literal executed) when the reply has no well-formed closing fence; decided ac62177 orig.
5. Batched writes are fragile: one 422 (already-set state) rolls back the whole cell's writes.
6. Supervisor data used where app data (IDs) was needed.
7. No budget awareness at the end: verification/search in the last cells while a write is pending; complete_task not reserved.
8. Parameter misuse exec errors (access_token on public endpoints, guessed API names, hard-coded passwords).
9. Completed-but-wrong: incomplete enumeration (c1091c7 seed3); systematic 0.8 on 7574325.
