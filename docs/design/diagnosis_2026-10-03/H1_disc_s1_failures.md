# H1 (standard base harness), discovery seed 1: the 8 remaining failures (2026-10-03)

Run: `CC_H1_F0_disc_seed1`, 42/50 successes. All 8 failures called `complete_task`, so every failure is semantic.
Sources: step logs, full I/O logs and ground truth in `scratchpad/diag/h1_fail/`, plus `ccdata/CC_H1_F0_disc_seed1.json`, which has all 50 trajectories and was used to check how often each detector fires on successful episodes.

**How the failing tests were identified.** G counts only the `no_op_fail` tests. For every task, the G value matches exactly the set of tests that I name as failing below. Examples: e7f15ba G=5/6, where only "answers match" fails; a3ba388 G=4/9; b6d1f70 G=8/12.

## Per task

**e7f15ba, 4242c97, d9987f6, 77bcb81 (four amazon purchase tasks; ground-truth answer `null`)**
1. Failed test: only "assert answers match". The order itself passed every state test (products, quantities, address, model changes). The agent ended with `apis.supervisor.complete_task(answer=3146)`, the order_id returned by `place_order`.
2. Decisive step: the final step. Class: **wrong answer format, here an answer given on an action task**. The prompt says "If no answer is required ... omit the answer argument". The agent's reasoning shows it chose to add the answer anyway:
   - d9987f6 step 14: "Providing the order ID is informative and harmless."
   - e7f15ba step 12: "the instructions say to keep answers minimal ... the confirmation would be the order_id."
3. Online signal: yes, and it can be checked before the code runs. The answer literal (3146) equals an `order_id` returned earlier in the same episode by a successful write (`place_order`), and the task sentence is imperative ("Make an order…", "Buy me…", "Place an order…"). The gate must run before `complete_task` executes, because executing it ends the episode.
4. Nudge (fixes all 4): "This task asks you to perform an action, not to answer a question. Call `apis.supervisor.complete_task()` without an answer; do not pass the order_id or any other id."

**b6d1f70: buy 2 identical earbuds; one gift-wrapped to the parents, one to my home**
1. Failed tests (4/12):
   - The answer was a long sentence where `null` was expected.
   - Expected 2 new orders; there were 3 (#3146 AirPods 732 to the parents with gift wrap, #3147 Jabra 734 to the parents with gift wrap, #3148 Jabra 734 to home).
   - The first two orders have different product ids, so "identical" fails.
   - The gift-wrap quantities are [0,1,1] instead of [0,1].
2. Decisive step: step 18/20, where it placed the first order for product 732 without checking stock. Step 17's cart showed `inventory_quantity: 1` for 732; the agent's own reasoning at step 22 says "the inventory of 732 was 1 (shown in cart as inventory_quantity: 1)". The step-13 search results also contained `inventory_quantity`, but the agent's print statement dropped that field. When step 21 failed, there was no cancel API, so it bought two more units. Class: **unverified feasibility before an irreversible write**, which then caused an **extra unwanted side effect** (the stray order). It also passed an answer on an action task.
3. Online signal: yes. A `place_order` was about to run while the most recent cart output showed `inventory_quantity` (1) below the number of units the task requires (2, from "Buy 2 identical").
4. Nudge: "The cart shows inventory_quantity=1 for product 732, but the task needs 2 identical units and orders cannot be cancelled. Choose a product whose stock covers all the units before placing any order." With this nudge it would pick 734 (8 reviews, rating 3.9, stock 2). It would also need the answer gate.

**a3ba388: attach a file to the existing resignation draft and schedule it**
1. Failed tests (5/9): the evaluator expects 0 added drafts, 1 updated draft and 0 removed drafts. The agent created draft 519, which had the attachment and the schedule, and then deleted the original draft 518. So the checks on the updated draft (recipients, scheduled_send_at, no other changed fields) fail, and so does `attachment.draft_id == 518`.
2. Decisive step: steps 7–8, `create_draft(...)` followed by `delete_draft(draft_id=518)`. Root cause: the harness truncated output **silently**. In the step-2 `api_index('gmail')` output, `update_draft(` starts at character 7251 and `upload_attachments_to_draft` at character 8013. The H1 cap for documentation cells is 8000 characters (`out_cap`), and nothing tells the model the output was cut. At step 3 the agent noted: "update_draft's compact signature doesn't show an attachment parameter". Class: **harness display truncation hid the right API, leading to a destructive workaround** (recreate and delete instead of modifying in place).
3. Online signal: yes, two of them. (a) The harness knows `len(out) > out_cap`. (b) Before execution: a cell calls `create_X` while the task refers to an existing item ("I have drafted…") and a `show_Xs` output already returned that item (draft 518). In the next cell, `delete_X` targets that pre-existing id.
4. Nudge: "The task refers to your existing draft 518; modify it in place (gmail has `upload_attachments_to_draft` and `update_draft(scheduled_send_at=...)`) instead of creating a new draft or deleting the original." The structural fix is a truncation marker.

**e201314: party return gifts; backpacks must "reach home by the end of the day before the party"**
1. Failed test (1/10): "all orders were to be delivered at main_user.home_address". The agent added 12 Amazon addresses for the friends and roommates and shipped one backpack to each of their homes. Product, quantity (12), rating, review count and delivery date all passed.
2. Decisive step: step 13, an `add_address` loop over the invitees. Class: **misread instruction**. "Reach home" means the user's home; the agent read it as each invitee's home. This is the same misreading as R11 in TAXONOMY.md, so it recurs across seeds.
3. Online signal: partly visible. In one cell, `add_address` was called 12 times with addresses taken from phone contacts, but the task sentence never says "their address", "ship to each", "to them" or "send".
4. Nudge (plausible, not certain): "The task says the gifts must 'reach home'. It does not say to ship to each invitee, so deliver every order to your own home address unless the task explicitly names their addresses."

**ba46d91: Spotify premium days left, "round to the nearest number"**
1. Failed test: answers match. The agent answered 336; the expected answer is 335.
2. Step 5 computed `round((end - now).total_seconds()/86400)`. The values were end 2024-04-18 23:59:59 and now 2023-05-19 00:00:10, giving 335.9999, which rounds to 336. The ground truth uses the calendar-date difference (335). Class: **environment / ground-truth ambiguity**. TAXONOMY §3 already lists this task: all 6 earlier runs plus the V2 runs answered 336.
3. Online signal: there is none, short of encoding the ground truth's convention.
4. Nudge: "use `(end.date()-today.date()).days`" would flip the answer, but that fits the ground truth. Do not count it.

## Class counts (8 failures; decisive class first, secondary class in parentheses)

| Class | Count | Tasks |
|---|---|---|
| Wrong answer format: answer passed on an action task | 4 (+1 secondary) | e7f15ba, 4242c97, d9987f6, 77bcb81 (b6d1f70) |
| Unverified feasibility before an irreversible write, then a collateral extra order | 1 | b6d1f70 |
| Harness silent truncation hid the API, then recreate/delete instead of modify (collateral write) | 1 | a3ba388 |
| Misread instruction (delivery target) | 1 | e201314 |
| Environment / ground-truth ambiguity (rounding) | 1 | ba46d91 |
| Incomplete coverage / pagination | 0 | Every list call paged with `page_limit=20` loops |
| Wrong data source | 0 | Detours to supervisor cards/addresses happened but were recovered |

## Proposed online detectors (ranked by expected recovered failures)

**D1. Answer gate on action tasks (pre-execution; expected +4, measured on 0/42 successes).**
```
on cell about to execute containing apis.supervisor.complete_task(answer=A), A not None:
    ids = {v for each earlier successful write cell (place_order|add_*|create_*|send_*|update_*|upload_*)
           for v in re.findall(r"_id['\"]?\s*[:=]\s*(\d+)", out)}
    fire if str(eval_literal(A)) in ids or re.search(r"#\d{3,}", A) or (isinstance(A, str) and len(A.split()) > 8)
    optionally: or (task has no '?' and no cue in {how many, how much, what, which, who, when, where,
                    tell me, let me know, give me, find out})
    action: do not execute; free re-ask with the nudge.
```
On the 50 trajectories the id rule fires on 5 failures (the four tasks above, plus b6d1f70 through `#3147`) and on 0 successes. The answers in successful episodes were values such as `total_paid`, `'yes'`, `42`, `'Wells Fargo'` and `None`. The optional question-cue rule must treat "tell me" as a cue (f099b4c: "…and tell me its total cost").

**D2. Silent-truncation marker (harness fix; expected +1, a3ba388).**
```
if len(out) > cap: shown = out[:cap] + f"\n[output truncated: {len(out)-cap} more chars]"
    if cell is api_index/show_api_descriptions: append the names of the APIs that were cut, comma-separated
```
This adds information and blocks nothing, so it carries essentially no risk on successes. It also saves a step whenever the agent re-lists a cut output (e7f15ba step 7, d9987f6 step 1).

**D3. Recreate-instead-of-modify gate (pre-execution; a3ba388; 1 success also matches).**
```
fire before a cell that calls delete_X(id=k) where k appeared in an earlier show_X/show_Xs output (a pre-existing record)
  and the episode already created a create_X (or the same cell does),
  or before create_X when the task says "I have drafted"/"my draft" and show_Xs returned a match
```
It also matches ffea2b5, which succeeded: there the agent deleted the draft and recreated it, but then sent it, so the draft disappeared anyway. The nudge would steer ffea2b5 toward `upload_attachments_to_draft` plus `send_email_from_draft`, which should still succeed. The false-positive cost is low.

**D4. Stock feasibility before an irreversible order (pre-execution; b6d1f70, which also needs D1).**
```
N = units required, parsed from the task (r"\b(buy|order|purchase)\s+(\d+|two|three|four|...)\b", or the length of the invitee list for "one for each")
inv[p] = latest inventory_quantity seen for product p in any output (search/show_product/show_cart)
fire before place_order if some cart product p has inv[p] < N and the task needs N identical/same units across orders
```
The rule needs full outputs, which the stored `out[:200]` excerpts do not contain. Few episodes would match: 16/50 call `place_order`, and stock below the required count is rare. In 4242c97 the agent already avoided the low-stock colors itself.

**D5. Delivery-target check (e201314; uncertain).**
```
fire after a cell with >=2 add_address calls whose street values come from phone contacts
  (not supervisor/user addresses), when the task lacks /their (home|address)|to each|ship to them|send .* to/
```
My first loose version also matched 690d51b, because that cell had an unrelated `while` loop. The refined rule, which requires at least 2 contact-derived addresses, matches 0 successes.

## Not fixable by nudges
- **ba46d91**: ground-truth convention (calendar-day difference compared with rounded elapsed days). Exclude it or flag it as an environment/ground-truth issue.
- **e201314** can be fixed only in part: a nudge can point at the ambiguous phrase but cannot guarantee the reading.
- Ceiling if D1–D5 all work: about 49/50. D1 alone gives about 46/50 (+4 with no measured false positives), so it is the clear first patch.
