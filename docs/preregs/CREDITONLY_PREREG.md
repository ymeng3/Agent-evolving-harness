# CREDIT-ONLY ARM — PREREG, FROZEN 2026-09-20 BEFORE THE MAIN LOOP'S ROUND-1 RESULTS ARE READ BY ANYONE
Parallel third arm of the frozen closed loop (prereg v2.1, sha f02984c01c87d725), run as a separate driver instance in the
Local-v2 regime. It separates the paper's two cores: Core 1 (Evolutionary Credit) vs Core 2 (cross-round credited-structure
reuse).
1 HYPOTHESIS   Part of Ours' gain over Naive comes from conditioning later proposals on component-level credit records
               (gamma, closure, kept/dropped), not only from selective inheritance within a round.
2 INTERVENTION Identical to Ours in every respect (K, T, S, n_val, stopping, Credit V1, Stage-3 cap, commit rule, backend,
               decoding, proposer, operators) EXCEPT the proposal state: the "PRIOR COMPONENT CREDIT" block is never rendered;
               the arm sees the same "CANDIDATE HISTORY" block Naive sees. Memory records are still produced and stored
               (mechanistic secondary) but never enter a prompt. Mechanically: arm name != "ours" in build_prompt.
               Fork rule: Credit-only == Ours at t=1 (empty memory), so its state is forked verbatim from the main loop's
               saved state after Ours finishes round 1 (same F_1, archive, cache); rounds 2-5 run independently.
3 CHEAPEST     Q_blind(F_5^{ours}) - Q_blind(F_5^{creditonly}) on the 140 held-out games, 3 seeds, game-bootstrap CI95;
  FALSIFIER    reported next to Ours - Naive. Predicted ordering under H: Naive < Credit-only < Ours.
4 WHAT KILLS   Credit-only >= Ours (CI excluding a positive reuse effect): Core 2 has no headline; the paper compresses to
               Credit. Naive >= Credit-only while Ours > Naive: single-round decomposition is insufficient; value is in
               accumulation (Core 2 only).
5 AVOIDS       (a) the old KG line's error of validating reuse by prediction instead of by behaviour; (b) confounding memory
               with Credit, which the two-arm loop cannot separate; (c) mid-run design: this text is frozen before any
               round-1 number is read. Blind files TESTBLIND_creditonly_F* are never opened before both main arms' F_5 exist.
RESOURCE       ~$1 gpt-4o; local backend; no mid-loop comparison between instances.
