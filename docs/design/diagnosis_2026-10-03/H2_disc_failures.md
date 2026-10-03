# H2 (H1 harness + original prompt), discovery seeds 1-2: the 13 remaining losses (2026-10-03)

Runs: `CC_H1origP_disc_seed1/2` (41/50 and 44/50 won). There are 15 losses; the two ba46d91 losses are excluded (ground-truth rounding convention), leaving 13. Sources: `scratchpad/diag/h2_fail/` (step logs, full I/O, ground truth). The full I/O logs are cut off after about 12-18 interactions for 7 of the tasks. Where they are, I located the failing tests from the per-task G value (passed/total) in the ccdata JSON. All detector false-positive (FP) counts below were measured on the 85 won trajectories.

## Per loss

| # | Task (seed) | Steps | Failing test(s) and cause | Decisive step and class | Online signal | Fix |
|---|---|---|---|---|---|---|
| 1 | ce73d68 (s1) | 17 | Only "answers match" fails (G=8/9). Both reminders were correct, but it ended with `complete_task(answer=2)` | Step 16. **Answer on action task**. It never read the complete_task spec | Non-None answer, and the task ("Reply ... to everyone") has no question cue | D1' |
| 2 | dc5c5c6 (s1) | 29 | Only "answers" fails (9/10): `answer="Ordered 2x PlayStation 5 ... (order 3146) ..."` | Step 28. **Answer on action task**. Its reasoning: "provide a minimal confirmation" | Same as #1 | D1' |
| 3 | b6d1f70 (s1) | 30 | Only "answers" fails (11/12). It picked the right product (734, stock 2, after it noticed "732 inventory_quantity: 1"). The last step did both orders plus `complete_task(answer="Bought 2 Jabra ...")` | Step 29. **Answer on action task, budget-crammed**: the final cell was the 30th, and the complete_task spec was never read | Same as #1 | D1', D7 |
| 4 | e7f15ba (s1) | 30 | Episode never completed. The last cell's `place_order(payment_card_id=payment_cards[0]...)` returned 422 (card 325; in seed 2, card 325 was filtered out as expired and 327 was used) | Step 29. **Budget exhaustion**, plus an unchecked card expiry in the last cell | At 27/30 steps used, complete_task had not been called, and add_address/place_order were still pending | D2-idx, D7, D5 |
| 5 | f86d850 (s1) | 30 | Never completed (7/13). The Venmo request and complete_task were missing | Steps 0-26: 15 doc steps. **Budget exhaustion** | At 27/30, no Venmo write and no complete_task yet | D2-idx, D7 |
| 6 | f86d850 (s2) | 30 | 3/13 fail, the three tests that depend on a "Fwd: Amazon Order Confirmation" email (subject, `#order` in body, recipient). Probably it forwarded the wrong Amazon thread | Step 28: one blind cell that searches five queries, takes the first thread whose subject contains 'Amazon', then forwards it and makes the Venmo request. It never printed which email it chose. **Budget-induced blind batch** (plan at step 24: "tight but possible") | A forward was executed on a thread id chosen by code whose subject was never shown | D2-idx |
| 7 | 1a79e37 (s1) | 29 | 7/8 pass; the delivery-address test fails. The contact output shows `work_address ... 44564`; the agent typed `zip_code=44464` | Step 26, a crammed cell (login + product types + search + add_address). **Transcription error under budget pressure** (the literal was copied from an output 13 steps earlier) | The write literal `44464` appears in no prior output, but `44564` does (edit distance 1) | D4 |
| 8 | 9871968 (s1) | 17 | Model-changes test fails: `amazon.WishListEntry` is unchanged. It read the `move_product_from_wish_list_to_cart` doc (step 7) but used `add_product_to_cart` | Step 11. **Wrong API (copy instead of move), so a side effect is missing** | The task mentions "wishlist", the move_* spec was read, and add_product_to_cart was called on the wishlist ids | Specific nudge (low priority) |
| 9 | 9871968 (s2) | 21 | 4/6 pass; product ids and product_id-to-quantity fail. It moved the wishlist items into a cart that already held hedge trimmer, picture strips and dumbbells (debited 1339.19 instead of 521.89) | Step 17. **Unchecked precondition (stale cart)**. show_cart/clear_cart were never called | place_order is about to run, and the episode has had no show_cart, clear_cart or clear_cart_first | D3 |
| 10 | e201314 (s2) | 26 | 3/10 pass. The 1st order's add_product_to_cart did not clear the cart, so stale items ended up in the orders (product, rating, review and quantity tests fail). It also shipped to 12 invitee homes (the H1 R11 misreading again) | Step 24. **Stale cart plus misread delivery target** | D3 condition; 5 contact-derived add_address calls | D3 plus H1-D5 (both needed) |
| 11 | c1091c7 (s1) | 29 | Alarm-id set fails (2/3). It disabled 744 and 745 (the "Cancel Meeting?" threads) but missed thread 47821, "Skip this time?" from stmcco ("I am swamped... Cannot make it"), which corresponds to the 1-1 with Stephen | Step 22. **Incomplete coverage: a literal keyword filter** (`'cancel' in subject`) applied to free text | Write decisions based on substring filters; recent coworker threads (05-21/22) not opened | Uncertain nudge |
| 12 | c1091c7 (s2) | 27 | Same failure. At step 20 it did see 47821 in the listing sorted by date, but called the others "distractors" | Step 23. **Same class** | Same | Same |
| 13 | 80acbaf (s2) | 29 | Song-library test fails (8/9). The file's "# Song Library" section lists 12 songs; the agent added 52 to the library (the union with the playlist songs) | Step 27. **Misread scope (extra writes)**. Two steps (11-12) also went to checking a silently cut output ("Output truncated?"), and step 26 executed only the final `print` block | Writes (52) exceed the entries in the matching source section (12) | Count nudge (specific); truncation marker |

## Class counts (13)

| Class | n | Tasks |
|---|---|---|
| Answer passed on an action task | 3 | ce73d68, dc5c5c6, b6d1f70 (budget-crammed) |
| Budget exhaustion (no complete_task) | 2 | e7f15ba s1, f86d850 s1 |
| Budget pressure leading to a blind batch or transcription error | 2 | f86d850 s2, 1a79e37 |
| Unchecked precondition: stale cart | 2 | 9871968 s2, e201314 s2 (plus the misread) |
| Incomplete coverage: keyword filter | 2 | c1091c7 s1, s2 |
| Wrong API, missing side effect | 1 | 9871968 s1 |
| Misread scope, extra writes | 1 | 80acbaf s2 |

Budget is a direct or contributing cause in 6/13 losses (#2-#7). Wins average 21.0 steps (10.6 doc-only); losses average 25.0 (12.5 doc-only).

## Step accounting for the 6 budget-related losses

Doc = cells that only call `api_docs`. Desc/login = `show_app/api_descriptions` cells plus the docs for login and `show_account_passwords`.

| Task | Steps | Doc (desc/login) | Redundant doc | Per-item excess | Error retry | Productive |
|---|---|---|---|---|---|---|
| e7f15ba s1 | 30 | 15 (4/3) | 0 | 4 (3 searches, 3 adds) | 2 (access_token, 422) | 9 |
| f86d850 s1 | 30 | 15 (6/3) | 0 (2 redundant action cells: supervisor cards, passwords re-fetched) | 0 | 0 | 13 |
| f86d850 s2 | 30 | 17 (5/3) | 1 (forward doc read twice) | 0 | 0 | 12 |
| b6d1f70 s1 | 30 | 16 (4/3) | 0 | 1 | 1 (+2 loose query/type search) | 10 |
| 1a79e37 s1 | 29 | 16 (5/3) | 0 | 0 | 1 (+1 wrong product: query search returned socks) | 11 |
| dc5c5c6 s1 | 29 | 12 (3/3) | 0 | 5 (8 single-call write cells instead of ~3) | 1 | 11 |
| **Total** | 178 | **91 (51%)**, of which 39 desc/login | 1 | 10 | 6 (+3) | 66 (37%) |

Repeated lookups are not the problem (redundant docs average 0.07-0.11 per episode). The cost comes from the "one spec per step" habit: every API used gets its own cell, including identical login specs for each app. The error retries include the recurring `search_products(access_token=...)` "Unexpected parameter" error, which occurs in 5/15 losses and 5/85 wins.

## Interventions, ranked by expected recovered losses

**1. D1' answer gate (pre-execution, online). Expected +3 (#1-3). FP 0/85.**
```
before executing a cell that contains complete_task(answer=A) with A not None:
  if task has no '?' and no /\b(tell me|let me know|give me|find out|how many|how much)\b/i
     and does not start with How|What|Which|Who|When|Where|Is|Are|Do|Does|Did|Has|Have|Can:
     block the whole cell (free re-ask): "This task asks for an action, not an answer. Call
     apis.supervisor.complete_task() with no answer; do not pass ids, counts or summaries."
```
Measured: it fires on ce73d68, dc5c5c6 and b6d1f70, and on none of the 85 wins (every win that passed an answer had a question cue). The cue must not include a bare "who" (ce73d68: "everyone who has not replied"). Because it blocks before execution, b6d1f70's orders are re-emitted without the answer instead of being placed twice.

**2. D2-idx: cheaper docs (harness plus one prompt sentence), only together with D1'. Expected +2 to +3 (#4, #5; relieves the pressure behind #6 and #7).** Make `show_api_descriptions(app)` print the compact signature as well (equivalently, mention `api_index(app)`). Keep "Always look at API specifications" but scope it to: full `show_api_doc` before the first call of any write API and of `supervisor.complete_task`; a signature line is enough for login/show/search. Estimated saving: desc/login docs minus (number of apps + 1), which is 3-4 steps per budget loss. The two exhausted episodes were 2-3 steps short. **Would it lose complete_task reading?** That risk is real: H1 showed that once compact signatures count as specs, the complete_task spec gets skipped. Even in H2 the spec is read in only 55% of wins and 27% of losses, and none of the 3 answer-format losses read it. Mitigations: (a) D1' catches the failure mode regardless of reading; (b) append the answer rule ("pass answer iff the task asks a question; action tasks leave None") to complete_task's signature line. Without D1', I would not ship this. Validate on val, where H1 lost 15 pp.

**3. D3 stale-cart gate (pre-execution, online). Expected +1 (9871968 s2). e201314 also needs H1-D5. FP 0/85.**
```
before a cell whose place_order( call is reached with no earlier show_cart(, clear_cart( or
clear_cart_first=True/expr in the episode (or earlier in the same cell):
  block: "You have not checked your cart; it may hold earlier items and place_order buys everything in it.
  Inspect it with show_cart or add the first item with clear_cart_first=True."
```
Measured: it fires on 9871968 s2 and e201314 s2 only.

**4. D4 literal-provenance check on writes (pre-execution, online). Expected +1 (1a79e37). FP not measurable here (needs full outputs), expected low.** For `add_*`/`place_*`/`send_*`/`create_*` calls, take every numeric literal of 5+ digits and every street-like string literal. If it appears in no prior full output but a token within edit distance 1 does, then nudge: "zip_code=44464 appears in no output; the contact shows 44564. Use the value from the variable (`husbands[0]['work_address']`) instead of retyping it."

**5. D7 endgame nudge plus a free re-ask for parameter-name errors. Expected +1 (f86d850 s1, possibly e7f15ba). Largely redundant if #2 works.** When steps used ≥ 27 and complete_task has not been called, append: "3 steps left. Do all remaining required actions in one cell, then call complete_task() (with an answer only if the task asks a question)." It would be shown in 8/15 losses and 12/85 wins. It is informational only, but it encourages cramming, which caused #6 and #7. It would not have saved b6d1f70 or dc5c5c6 without the answer clause, and D1' covers those anyway. Companion change: when a read-only cell fails with "Unexpected parameter" (no state change), re-ask for free instead of charging a step. That saves 1 step in 5/15 losses (e7f15ba, b6d1f70, dc5c5c6, 1a79e37, e201314) at no risk.

**Also cheap and zero-risk:** turn on the H1.1 truncation marker. H2 still cuts non-doc outputs at 3000 characters without saying so; this cost 80acbaf 2 steps and c1091c7 1 step, and it hid char 27,624 of c1091c7's 34K thread listing.

**Not addressed:** c1091c7 ×2 (semantic recall). A possible nudge: "coworkers with 1-1 alarms whose recent emails you have not opened: Stephen, Sabrina, Cody, Sandra; cancellations may not say 'cancel'". The trigger is fuzzy. Also not addressed: 80acbaf (scope), 9871968 s1 (move vs add), and the e201314 misread.

Projected effect: interventions 1-4 recover about 7 of 13, taking discovery from 0.85 to about 0.92. Interventions 1 and 3 are near-certain, with no measured false positives.
