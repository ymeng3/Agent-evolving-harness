# MECHANISM-CONDITIONED EVIDENCE vs TERMINAL CREDIT — $0 ARCHIVAL TEST. FROZEN 2026-09-21 BEFORE ANY NUMBER.
Question: does intent-conditioned trajectory evidence carry an order-of-magnitude more resolvable signal than terminal
Bernoulli credit, AND does it point the same way as terminal credit where terminal credit is resolvable?
DATA: archival passes with per-step (action, admissible) and pass-level hook counters, 134 games x 3 seeds each:
  F0; N01 parser; N03 retry; N04 history; N05 retry-temp; N06 memory+feedback; N07 temp+prompt-on-retry; N08 split
  think/act; N09 retry-on-invalid; E1_T temp .5; E1_HT; E1_HR; G_MECH07 (H+M+fallback); SV_H, SV_M, SV_HM, SV_CM.
MECHANISM METRICS (per pass, then paired vs F0 by seed):
  recover  = P(admissible_{t+1} | not admissible_t)              claim of retry/fallback: escape after a failed action
  escape   = P(a_{t+1} != a_t | a_t == a_{t-1})                    claim of temperature/fallback: leave repeated-action loops
  inadm    = P(not admissible_t)                                   claim of parser/prompt: fewer unexecutable actions
  coverage = number of conditioning events (reported with each)
TERMINAL: gamma = success(X) - success(F0), 402 paired episodes, CI95 by game-bootstrap.
PREDICTIONS (frozen):
  H1 precision: mechanism-metric CI95 half-widths are < 1/3 of the terminal gamma half-width for the same pass.
  H2 direction: across interventions whose terminal gamma CI excludes 0, the sign of the claim-matched mechanism effect
     (retry/fallback -> recover; temperature/fallback -> escape; parser/prompt -> inadm, sign flipped) agrees with the sign
     of gamma in >= 80% of cases.
  H3 specificity: interventions that do NOT claim a mechanism show |effect| on that metric below the smallest claiming
     intervention's effect (e.g. history should not move 'recover' more than retry does).
KILL: H1 fails (metrics not more precise) OR H2 fails (mechanism effects do not track terminal credit direction) -> the
  mechanism-evidence route dies at $0 and Credit V2 is not built on it. H3 failing alone = metrics too coarse; note only.
Scope: NOT a rubric, NOT an LLM judge. Only what the stored trajectories support. A per-step retry/fallback trigger log
would be needed for finer claims; that requires a logging change and a new run (not now).
