# TRAJECTORY-GUIDED HARNESS EDITS E1/E2 — FROZEN 2026-09-25 BEFORE THE RUNS. ($0 API; ~1 GPU-hour when the instance is on)
Chain under test: logs expose a recurring failure scenario -> a concrete rule edit -> full paired episodes decide.
E1 (r6 and MECH07): fallback never answers 'look'; it navigates to a place not yet visited (tracked in memory_update),
   else any non-look admissible action. Patches patches_edits/r6_E1_unvisited.py, mech07_E1_unvisited.py (validate+STATIC+smoke PASS).
   Runs: r6_E1 and mech07_E1, 48 games (first 48 of validation_train96), seed 1, slot-paired with existing C and C\fallback
   passes (PV_r6_C/PVA_r6_nofb first-48 slots; XS_MECH07_C/XS_MECH07_nofb).
   PREDICTION: E1 removes the harm on both: Q(E1) - Q(C\fb) >= -3pp AND Q(E1) - Q(C) >= +5pp. (r6's V2 already showed
   'no look' removes harm via history repeats; E1 tests the NEW rule 'unvisited navigation' and generalises to MECH07.)
E2 (ctrl21 retry): on retry, name three concrete admissible commands and require one verbatim, instead of repeating the
   same hint. Patch patches_edits/ctrl21_E2_retryhint.py (PASS). Run: ctrl21_E2, 48 games, seed 1, paired with XS_ctrl21_C
   and XS_ctrl21_noretry. PREDICTION: retry-without-change events drop by >= 50% (C had 286/652) AND Q(E2) - Q(C) >= 0.
E3: DEFERRED. Needs raw replies; harness now logs the last 300 chars of the first reply when BOS_LOG_RAW=1 (record only);
   these three runs will collect them so the "how many reasoning-only replies contain an extractable command" check
   becomes possible at $0 afterwards.
KILL for the chain: E1 fails on both candidates -> trajectory-guided edits are not reliably better than deleting the rule.
