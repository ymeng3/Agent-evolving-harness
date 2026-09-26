# "DOES THE SUBSTITUTED ACTION ADVANCE THE SEARCH?" — SIGNAL FROZEN 2026-09-24 BEFORE THE NEW PASSES RUN.
Plain statement: a component that turns the model's non-action into an action is good when the action gives new
information (first visit to a place, or the target becomes visible, or a task fact is established) and bad when it gives
none ('look', a place already visited, a redundant repeat).
PER-ACTIVATION LABEL (components with a trigger: fallback, retry, parse):
  +1  executed action: first visit to a receptacle, or target seen, or a task fact established (holding/at/heat/cool/clean/place)
  -1  executed action: 'look', or revisit of an already-visited receptacle, or re-establishing an already-true fact
   0  anything else
  SIGNAL S = mean label over activations.  Sign of S is the component verdict (|S| < 0.05 -> undecided).
EPISODE-LEVEL PROFILE (components acting every step: HISTORY, TEMPERATURE, format, memory): ON vs OFF, slot-paired,
  T = (episodes reaching 'target seen' ON - OFF) + (episodes reaching 'holding' ON - OFF) + (episodes reaching a core fact
  ON - OFF), each in fraction of episodes; sign of T is the verdict (|T| < 0.05 -> undecided).
PREDICTIONS (must hold or the line stops):
  MECH07 fallback (LOO -16.4, firm): S < 0.   naive r5 retry (LOO +13.5, firm): S > 0.   ctrl21 retry (LOO +8.2): S > 0.
  Loop-1 r3 TEMPERATURE (LOO -4.2, noisy): T <= 0 expected, not required.   N04 history (+6.3 vs F0, firm): T > 0.
  Already computed on old logs (not predictions): r6 fallback S must be < 0 and L2c4 fallback S > 0 under this exact rule.
FAIL RULE: any of the three firm predictions wrong, or r6/L2c4 not separated under the frozen rule -> stop this line.
RUNS: 8 passes x 48 games (first 48 of validation_train96, seed 1), step-logged, local backend, $0 API.
ADDENDUM (written after checking the rule on OLD logs, before any NEW pass is read):
  Old-log check: r6 fallback S=-0.86, L2c4 fallback S=+0.10 -> separated (rule prerequisite OK). BUT r4 retry S=-0.11 with a
  firm helpful LOO (+13.0): a pre-existing COUNTEREXAMPLE for retry. Two attribution flaws found by inspection: (1) when
  retry and fallback fire on the same step the executed action belongs to the LAST stage (fallback), yet the step was
  counted for both; (2) 'open X' / 'examine X' on a not-yet-opened receptacle is information gain but was labelled 0.
  VARIANT B (pre-registered now, evaluated alongside rule A on the new passes; NOT tuned on them): action owner = last
  stage that changed it; +1 also for first 'open'/'examine' of a receptacle. Adoption rule: B replaces A only if B passes
  the same three firm predictions AND turns r4 retry positive AND keeps r6/L2c4 separated. Otherwise A's failure stands.
