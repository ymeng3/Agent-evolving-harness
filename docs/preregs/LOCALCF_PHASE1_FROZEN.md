# LOCAL COUNTERFACTUAL — PHASE 1 SMOKE TEST. FROZEN 2026-09-24 BEFORE ANY BRANCH RUNS.
Plain design: for each component, find states where it actually acted (from step-logged C runs), "save the game" there
(deterministic prefix replay, verified 8/8), continue ONCE with the component removed (OFF branch), and compare with the
original continuation (ON = the logged trajectory itself). CF@B = mean(Y_on - Y_off) over the first B states of one fixed
shuffled order (B=8 is the first 8 of the same 32; no separate runs). Every-step components (HISTORY, TEMPERATURE) branch at
step 6 (first step where the longer history / decoding change can matter).
COMPONENTS (10; global LOO from the frozen table): r6 fallback (-6.8), L2c4 fallback (+16.7), r4 retry (+13.0),
  r4 HISTORY (-0.5), r6 HISTORY (+3.1), MECH07 fallback (-16.4), naive r5 retry (+13.5), ctrl21 retry (+8.2),
  r3 TEMPERATURE (-4.2), r3 retry (LOO not measured; descriptive).
READ-OUT (no significance claims): do the clearly helpful ones (L2c4 fb, r4 retry, naive r5 retry, ctrl21 retry) come out
  positive at CF@32? does the clearly harmful pair (r6 fb, MECH07 fb) come out negative? does CF@32 look steadier than
  CF@8? is the ranking roughly right? Cost = OFF-branch LLM calls / full-LOO-pass calls.
KILL: if CF@32 cannot even order {L2c4 fb, r4 retry} above {r6 fb, MECH07 fb}, stop the local-CF (C3) line.
CONTINUE: otherwise Phase 2 (about 20 components, all families, cost-quality table at B=8/16/32/64).
Cost guard: ~10 components x 32 OFF continuations ~ 3 full-pass equivalents, one A800, no second GPU.
