batch0 tasks: f099b4c_1 a676f2a_1 33e202d_1 80acbaf_1 e7f15ba_1   (15 failed attempts; ALL hit the 30-cell limit without complete_task; none failed by a wrong final answer)

- f099b4c_1 (reset Amazon cart from note list, report total; mixed). All 3 failures [I,A,G(,B,J)]: one search_products cell per item (5 items), one doc per call; never added to cart. Success: ONE loop that parsed the note and searched all 5 with exact-name matching, then one add loop (clear_cart_first=True saved a cell). Divergence = the cell after the first single-product search. Only behavioural difference between successes and failures was looping.
- a676f2a_1 (Venmo-request coworkers' lunch shares; mixed). fix_seed1 c8 and disc_seed3 c11 [E,G,J]: AMBIGUITY PARALYSIS — data complete by c7/c10, then 18-21 code-less deliberation turns ("does the user have their own food item?"), each silently running the fallback show_app_descriptions cell. orig_seed1 c28 [J,A,I]: ~9 cells lost to code-extraction artifacts (partial block, placeholder show_api_doc(...), prose executed), globals() checks. Success committed to the natural reading at c10, batched, finished c18.
- 33e202d_1 (CSV of applicants' LinkedIn URLs, download attachments; always fails). All 3 [E,G,J,...]: data extracted by c14-22, then code-less deliberation about CSV row order / attachment scope (14 fallback turns in fix_seed1, identical reasoning tails), globals()/pseudo-state rebuild with '...'; disc_seed2 also truncation re-prints, manual pagination, code cut off mid-line.
- 80acbaf_1 (create Spotify account, import songs/albums/playlists; always fails). All 3 [I,A,(B,F,D,J)]: pacing — one doc per call (11 doc cells), truncation re-prints, login before signup, signup+Gmail code+verify+login took ~12 cells; access_token passed to search_songs (exec error); like_song instead of add_song_to_library.
- e7f15ba_1 (order 3 products to parents' address; always fails). All 3 [I,A,B,(J)]: one doc cell per API (reasoning: "Instructions say always look at API spec before calling"; "It says one chunk of code in every step. Could do one API call per step"), access_token error on search_products, one search and one add per item; never reached checkout.

BATCH PATTERNS:
1. Over-literal reading of the prompt rules (one api_docs lookup before EVERY call; one API call / item per cell) = main budget killer; sole cause in f099b4c, 80acbaf, e7f15ba (all failures). 35-50% of cells are api_docs. The model quotes the rules in its reasoning.
2. SILENT HARNESS FALLBACK on code-less / malformed replies: harness runs print(apis.api_docs.show_app_descriptions()) or a fragment/placeholder and does not tell the model. Hides deliberation loops and burns cells: a676f2a fix (21 cells), disc3 (18), 33e202d fix (14), etc.
3. AMBIGUITY PARALYSIS after data gathering is complete: re-arguing one underspecified detail turn after turn (identical reasoning tails), never committing.
4. State-confusion spiral from artifacts: globals() checks, '...' pseudo-code state rebuilds.
5. Display truncation of long outputs forces 1-3 re-print cells per app.
6. access_token passed to public search APIs -> 'Unexpected parameter' exec error (1 cell each, many runs).
7. Output-token cap cuts code mid-line -> syntax errors.
8. No failure from a wrong final answer: all 15 failures = budget exhaustion; several had correct intermediate results.
