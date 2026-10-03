batch2 tasks: a3ba388_1 4242c97_1 77bcb81_1 20c1328_1 d9987f6_1

- a3ba388_1 (attach resignation PDF to draft, schedule Monday; mixed). All 6 runs ~18 doc cells; successes finish on exactly cell 29. Failures: fix c27 phone date API doc+call instead of datetime.now(), update on c29, no complete_task (8/9). disc2 c29: last cell = show_api_doc(complete_task) instead of calling it (logged called_complete_task=True is a FALSE POSITIVE from the doc call). disc3: 2 cells to generation artifacts (empty fence -> fallback; truncated syntax error), verification reads at 28-29.
- 4242c97_1 (two XL Hanes shirts, preferred available color; mixed). fix c26 [G,B,I,J]: each color searched twice (single page then paginated), access_token to search_products, guessed 'checkout'; empty code block at c26 -> fallback; order on c29, no complete_task (6/7). disc4 c20 [G,D,I,J]: redundant searches, supervisor.show_addresses detour (no address_id), 'Need final.' loop with no code, context loss. Successes: one XL search, three show_product stock checks, 1 spare cell.
- 77bcb81_1 (order cart + wishlist to home; mixed). ALL 4 runs hit place_order 422 from an invalid promo code (promo_valid:false visible at first show_cart). Successes recovered in 3 cells because they already knew remove_promo_code_from_cart. disc2: artifacts + show_api_doc(complete_task) on last cell (5/6). disc4: truncated API list, guessed 'remove_promo_code', supervisor-address detour (0/6).
- 20c1328_1 (top-rated $10-20 frame per roommate; always fails). orig [A,B,I]: 18 doc cells, search spec read 3x, access_token error, query search instead of product_type. fix [D,A,J,I]: 6 supervisor cells up front, then generation collapse (fragments 'print'). disc2 [E,K:stock-insufficient,B,I]: picked frame without checking inventory_quantity -> add_to_cart(qty=3) 422.
- d9987f6_1 (extension cord rated > 4.5; always fails). orig [J,A,D,I]: replies truncated mid-code from c21 (7 fallback cells). fix + disc2 [K:card-insufficient-balance,...]: place_order 422 insufficient balance on both Amazon cards; remedy = add the supervisor's extra valid card to Amazon (needs 3+ cells).

BATCH PATTERNS:
1. Spec reading eats the budget: 14-21 of 30 cells in failures, 14-18 in successes; successes finish at 27-29, outcomes set by 1-2 incidental cells.
2. Generation truncation masked by the harness fallback (runs show_app_descriptions or the fragment); detect and regenerate without charging a cell.
3. Wasted final cells: show_api_doc(complete_task) or verification reads at 28-29 instead of calling complete_task; no budget awareness near the end. called_complete_task metric has false positives from doc calls.
4. Checkout preconditions surface only as a late 422 (invalid promo; insufficient stock; insufficient card balance), when recovery needs 3-5 cells.
5. Truncated show_api_descriptions -> API-name guessing ('checkout', 'remove_promo_code', 'show_wishlist').
6. access_token passed to search_products/show_product.
7. Supervisor detour: supervisor.show_addresses/show_payment_cards fetched though place_order needs amazon IDs (2-6 cells per run).
8. Redundant retrieval (re-searching with pagination, re-reading specs, query-only searches without product_type).
