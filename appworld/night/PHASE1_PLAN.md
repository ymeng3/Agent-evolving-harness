# PHASE 1 PLAN — AppWorld harness repairability diagnosis (2026-09-27 night)

## What the user asked (organised)
1. Hooks: the 5 ALFWorld hooks were transplanted; retry_policy/choose_fallback are near-dead in AppWorld. Decide a search space with
   open modules (Prompt / Planning / Memory / Tool Use / Recovery / Verification) but isolated, testable edit units.
2. Before any evolution: hand-implement three code-level scaffolds matched to the three failure classes seen in the logs, test each on
   its class and on the full set (regressions). This answers "missing model capability vs missing harness expressivity".
3. Proposer is too weak / knob-turning; credit can only reject. Later: failure-conditioned operator search (Select -> Generate ->
   Transform -> Compose), single mechanisms verified before Compose; upgrade the proposer only if specific inputs still yield knobs.
4. Arena: challenge = development; normal = regression check. Keep Discovery / Validation / Sealed Test split by task family.
5. Rubric round 2 stopped (generic dimensions, dead-hook candidates); lean loop paused after round 1. Rubric v3 later must be
   mechanism-level (trigger / evidence / mechanism / intervention module / counter-evidence), valued by downstream proposal gain
   with a token-matched control, diagnosed on unseen failures.
6. Hand-written fixes must NOT seed the evolution parent (they are diagnostic upper bounds). Middle road adopted: the harness gains
   only generic infrastructure (SETUP_CODE = sandbox helpers executed before step 0; state passthrough), not the fix logic.

## Data
- Discovery: tasks_challenge50.json (50 families; inspected).  Validation: tasks_challenge_val50.json (50 new families).
- Sealed test: tasks_challenge_TESTSEALED50.json (39 families; sha 5fc182d611121ca8) — frozen, not run tonight.
- Failure classes on Discovery (from the 27B/30-step logs; best-effort assignment):
  shop (multi-constraint purchase, 11): e7f15ba_1 4242c97_1 dc5c5c6_1 d9987f6_1 20c1328_1 b6d1f70_1 953b296_1 690d51b_1 77bcb81_1 9871968_1 f86d850_1
  cross-app (13): 9126bf0_1 f099b4c_1 3fcc458_1 1a79e37_1 e201314_1 a676f2a_1 c8f5f44_1 80acbaf_1 ffea2b5_1 a3ba388_1 33e202d_1 ce73d68_1 c1091c7_1
  multi-action (6): 5800354_1 2e9b91e_1 3f3c139_1 7574325_1 09ac073_1 e52623a_1

## Interventions (hand-written, patches_phase1/)
- E1 pagination + structured filter (Tool Use): sandbox helpers fetch_all / filter_products + one step-0 prompt line.
- E2 cross-app memory (Memory): sandbox `notes` + remember(); harness re-injects saved notes each step.
- E3 sub-goal tracker (Planning/Verification): sandbox plan()/done(); remaining actions re-injected; complete_task blocked ONCE
  while planned actions are open (bounded, unlike the verify prompt that looped).
- E123 = union.

## Runs (challenge, 30 steps, local 27B, 16 workers, <=2 passes per box)
- m2 now: VAL_F0 s1,s2 (bare on Validation); E1/E2/E3/E123 on Discovery s1; E1/E2/E3/E123 on Validation s1.
- m1 after lean-loop round 1: E1/E2/E3/E123 on Discovery s2; E123 on Validation s2.
- Read-out per intervention: (a) Discovery, its own class: rescued / broken vs bare (s1,s2); (b) Discovery full 50: net;
  (c) Validation 50: net vs VAL_F0 (generalisation to new families), split by class where the class can be assigned.
- Decision rule (pre-committed, loose): an intervention is 'repairs its class' if it rescues >= 3 class tasks in >= 1 seed with
  <= 2 broken outside the class on Discovery, AND is non-negative on Validation. If none qualifies -> executor capability is the
  binding constraint on this slice. Whatever qualifies defines the active modules of the AppWorld search space; the fix code
  itself is NOT reused as the evolution parent.
