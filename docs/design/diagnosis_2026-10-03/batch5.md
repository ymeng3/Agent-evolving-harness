batch5 tasks: 690d51b_1 e201314_1 3fcc458_1 ce73d68_1 b6d1f70_1 cdf61bd_1

- 690d51b_1 (kitchen timer < $10; mixed). orig c18 [A,I]: 16/30 docs, 5 cells of unneeded checks (show_product, show_cart, clear_cart doc), supervisor cards instead of Amazon card ids; never place_order. disc2 c11 [A,G,I]: same docs re-read 3x. disc3 c17 [J,G,A]: replies cut off mid-code from c17, old show_app_descriptions ran, 7 cells lost. Success (disc5, 23 cells): direct supervisor calls without docs, add with clear_cart_first right away. Every failure ended 2-3 cells short of place_order+complete.
- e201314_1 (12 backpacks home before Saturday; mixed). orig c26 / fix c24 [E,...]: misread "reach home" as each invitee's home -> plan 12 orders instead of one quantity-12 order to Home. disc2 c20 [A,B,G,E,J]: 9 cells re-finding the API list, guessing nonexistent API names. Success used all 30/30 cells (zero slack).
- 3fcc458_1 (add Isaac's emailed songs to Road Trip, download; always fails). orig [I,A,per-item]: 15 doc cells over a 4-app chain, then one search per song. fix [A,G,J,I]: phone-contacts detour, truncated Gmail list hid download_attachment. disc2: access_token to search_songs, one song per cell.
- ce73d68_1 (reply 'A gentle reminder.' to unanswered applications; always fails). orig c13 [J,G]: 15 consecutive code-less replies -> fallback show_app_descriptions x15. fix c14 [J,G]: cut-off/abbreviated code ('...', loops cut mid-statement). disc2 c21 [H,E]: completed but filter missed eligible threads (2/9 checks failed) — the only completed failure here.
- b6d1f70_1 (2 earbuds: one gift-wrapped to parents, one home; always fails). orig [J,A,G,I]: docs before every call; cut-off code, '...', NameError, variable checks. fix [A,J,I]: parents' address searched in supervisor before phone contacts; 4 cells lost to cut-off/old code. disc2 [A,I]: 20/30 cells docs.
- cdf61bd_1 (change t-shirt review to 1 star; mixed). orig c2 [J,G]: replies cut mid-code from c2; fallback ran in 18/30 cells; self-reinforcing truncation loop (confusion -> longer reasoning -> more truncation). Successes kept reasoning short and code blocks small, 20 cells.

BATCH PATTERNS:
1. Doc-before-every-call habit (50-65% of cells), docs re-read; main budget killer in 690d51b, e201314, 3fcc458, b6d1f70.
2. Budget so tight efficiency decides: successes 29/30 and 30/30; failures often 2-4 cells short.
3. CUT-OFF REPLIES + FALLBACK CODE EXECUTION: output cut mid-code or before any code block; harness runs partial code / prose / '...' / the default show_app_descriptions; can loop for 15-18 cells (ce73d68 orig, cdf61bd orig); long reasoning about state makes the next cut-off more likely.
4. Truncated API listings (display limit) -> re-listing; missed APIs (download_attachment), invented names (add_to_cart, checkout).
5. API misuse costing one cell each: access_token on public search APIs; missing access_token; guessed field names; bare expressions without print.
6. Per-item cells instead of loops.
7. Redundant re-fetching and checks (date, show_product after search, show_cart before clear_cart_first add, supervisor cards vs Amazon cards).
8. Misread instructions surface late near irreversible steps ('reach home' = each invitee's home; reminder filter missing cases).
