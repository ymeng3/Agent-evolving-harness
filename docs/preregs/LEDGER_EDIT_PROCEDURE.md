# TRAJECTORY-GUIDED HARNESS EDIT — FIXED PROCEDURE (v1, 2026-09-25). Learned from r6 (pass), MECH07 (E1 miss -> E1' pass), ctrl21 retry (fail).
1 READ THE RULE: list EVERY branch of the hook from its source (each return path / each state write), in order of evaluation.
2 LEDGER PER BRANCH from step logs: how often each branch fires; what it received (model's original output: no action /
  tagged-inadmissible / admissible); what it emitted; what followed within 3 steps (new place / target seen / task fact /
  nothing); and, when a paired no-rule run exists, the same for the counterfactual side.
3 NAME THE FAILURE SCENARIO in one sentence per harmful branch (e.g. "when the model emits no action, the rule answers
  'look', and nothing follows 85% of the time"). A branch with no observable consequence is NOT edited.
4 PROPOSE ONE EDIT PER HARMFUL BRANCH that changes the emitted action into one with observed value in the same ledger
  (e.g. unvisited navigation), keeping all non-harmful branches untouched. Write the patch; validate + STATIC + smoke.
5 FREEZE the prediction before running: Q(E) - Q(C) >= +5 and Q(E) - Q(C \ rule) >= -3 (48-game slot-paired, seed 1).
6 RUN the full paired episodes; the edit is kept only if the prediction holds. A miss sends you back to step 1 (missing
  branch), never to re-tuning the same edit.
NOT allowed: editing a branch with no ledger evidence; changing more than the emitted action of the harmful branch;
  choosing the replacement action from the outcome of the test run.
