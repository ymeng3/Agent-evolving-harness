# VERIFIER INCREMENT TEST — FROZEN 2026-09-24 BEFORE THE TWO PASSES RUN. $0 API, ~40 GPU-min.
Question: in paired ON/OFF full trajectories, does goal-atom divergence precede and predict outcome discordance?
DATA: existing step-logged C passes PV_r6_C and PV_L2c4_C (seed 1) paired by slot with NEW step-logged passes of the
fallback-ablated configs (PVA_r6_nofb, PVA_L2c4_nofb; same manifest, seed 1, same env permutation). Atoms from
task_type+pddl_params; witnesses from observation text (move / heat / cool / clean / slice / use; 'take X from <target
receptacle>' as destruction). Atom trajectory per episode = ordered set of (atom, step) establishments/destructions.
FROZEN PREDICTIONS (for the verifier line to survive; evaluated on r6 and L2c4 separately, both must hold unless noted):
  P1 enrichment: P(outcome discordant | atom trajectories differ) >= 2 x P(outcome discordant) overall.
  P2 timing: among outcome-discordant pairs, >= 70% show an atom divergence (an atom established/destroyed on one side and
     not the other, or at an earlier step) before the episode ends; report the median lead (steps from first atom
     divergence to the end of the shorter episode).
  P3 direction: among pairs with atom divergence, the side that first establishes a goal atom (or avoids destroying one)
     wins more often: agreement with the outcome winner >= 75%, and the pooled direction matches the sign of gamma for both
     fallbacks (r6 negative, L2c4 positive).
KILL: P1 or P3 fails on either candidate, or P2 fails on both -> "goal-atom representation cannot see this component's
     causal path"; no further verifier/VICT investment. PASS -> verifier trace is adopted as a SELECTION/EXPLANATION layer
     only (where to branch, what changed); inheritance decisions remain the terminal counterfactual.
Bias guard: no branch rollouts are run on atom-selected states in this test; unselected LOO results stay the estimate.
