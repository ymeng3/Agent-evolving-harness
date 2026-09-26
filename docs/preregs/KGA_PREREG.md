# KG-A — FROZEN PREREG (2026-09-13). Zero cost. Nothing generated, nothing launched.

Internal name for the object under test: **HAG (Hereditary Artifact Graph)**. NOT "EKG" and NOT
"knowledge graph" — see the naming note at the end. No name goes in a title until a full audit runs.

## THE FIVE REGISTERED FIELDS

**HYPOTHESIS.** Typed structural and runtime relations extracted from evolutionary history predict a
held-out candidate's runtime validity BEYOND (a) features of its own source and (b) its position in
the provenance lineage. Plainly: does knowing how RELATED ARTIFACTS behaved at runtime help predict
this one?

**INTERVENTION.** None on the agent. This is a retrospective predictive gate on 628 already-existing
patches, labelled by the existing unmodified `b2_smoke.smoke()`.

**CHEAPEST FALSIFIER.** Grouped cross-validation over 61 generation groups, three nested feature sets,
one frozen model. $0, minutes.

**WHAT KILLS IT.** See KILL RULE below. If it fires, the graph is NOT promoted to a decision
substrate; it stays provenance visualisation, and the paper's headline stays hereditary artifact
construction with no graph claim.

**WHICH PREVIOUS FAILURE OF THIS PROJECT IT AVOIDS.** The sixth-failure-of-that-shape pattern: every
previous attempt to give the PROPOSER more structured information failed (credit annotation,
provenance prompt, coverage state, Transform, verbose evidence, diversity floor). KG-A puts no
information in front of the proposer at all; it asks whether the information has predictive content
for the SYSTEM. If it does not, no amount of plumbing it into a prompt will help.

## LABELS — FROZEN BEFORE ANY FEATURE WAS COMPUTED
Source: `b2_smoke.smoke()`, used UNMODIFIED, run over `patches*/**/*.py`. Output
`/net/scratch/ymeng3/bos_screens/hag/smoke_all.json`, 628 rows. No API calls.
  y = 1 iff smoke_verdict == "PASS"; y = 0 for PARTIAL / CRASH / INERT / FATAL:* / TIMEOUT.
  Marginal: 440 positive, 188 negative (70.1% positive). 61 groups.
ONLY THE MARGINAL AND THE GROUP SIZES WERE INSPECTED BEFORE FREEZING. No feature-label relationship
was examined. Recorded because the whole gate depends on it.

## THREE NESTED CONDITIONS — THE CONTRAST IS *KIND* OF INFORMATION, NOT AMOUNT
C1 FLAT (own source only): hooks declared, LOC, per-hook LOC, counts of try/except, loops,
  comprehensions, regex calls, dict/set ops, indexing, string ops, `state` reads vs writes, declared
  constants and whether in range, max nesting depth, number of returns, presence of a bare fallback
  return. NOTHING about history.
C2 = C1 + PROVENANCE (structure only, NO other candidate's runtime outcome): group size, index within
  group, parent group, DAG depth, ancestor count, edit count, Jaccard overlap of its hook set with its
  parent's, number of siblings, whether it is a drop-cell or whole-cell descendant.
C3 = C2 + RUNTIME-RELATIONAL (the actual claim): features that propagate OTHER candidates' runtime
  labels through the graph — for each candidate, the PASS rate of OTHER-GROUP candidates sharing its
  hook set, its hook PAIRS, and its exact edit shas; the parent artifact's own smoke verdict where
  known; whether any other-group candidate with the same hook pair had a never-fired hook.
All three use the SAME frozen model with the SAME fixed hyperparameters and the same seed. The only
thing that varies is the feature set. That is what isolates the question.

## VALIDATION — TWO LEVELS, PRIMARY IS THE GROUPED ONE
PRIMARY: LEAVE-ONE-GROUP-OUT over the 61 generation groups. A candidate's whole group — same parent,
same prompt, same generation event — is removed from training. C3's propagated-label features are
recomputed INSIDE each fold from the training groups only, never from the held-out group.
SECONDARY: ordinary leave-one-candidate-out (reported, NOT decisive; it is the leaky version and
exists only to quantify how much near-neighbour leakage there is).

## ENDPOINTS
PRIMARY ENDPOINT: balanced accuracy (BA). Secondary: AUROC, Brier.
PRIMARY CONTRAST (as the user specified):  dBA_31 = BA(C3) - BA(C1)
CO-PRIMARY CONTRAST (the discriminating one, added because C3-C1 conflates "lineage helps" with
  "runtime relations help"):          dBA_32 = BA(C3) - BA(C2)
Uncertainty: group bootstrap (resample the 61 groups, 5000 draws), CI95 on each contrast.

## KILL RULE — FROZEN, BOTH CONDITIONS REQUIRED
The graph is promoted ONLY IF **both** dBA_31 > 0 and dBA_32 > 0 with a group-bootstrap CI95
excluding zero. If either fails, KG-A is a KILL: the graph is not a decision substrate, KG-B and KG-C
are not run, and the graph is reported as provenance bookkeeping only.
NO practical-threshold escape hatch is registered. "No stable superiority => kill", as instructed.

## LEAKAGE BANS — FROZEN
1. NO task-outcome quantity may enter any predictor in any condition: no success_rate, delta, won,
   steps, retries, invalid, calls, cost. The 2026-09-12 telemetry false positive (raw rho +.595,
   partial -.146 after controlling steps/game) is the reason; that channel is collider-contaminated.
2. C3 may use OTHER candidates' RUNTIME LABELS (that is the claim) but never the held-out group's.
3. No hyperparameter tuning, no model selection, no feature selection after seeing any score. One
   model, fixed, all three conditions.
4. If the gate is re-run for any reason, the re-run and its reason are registered; the first result
   stands as primary.

## WHAT THIS GATE DOES **NOT** TEST
It does not test value. Runtime validity is a necessary condition the graph might supply cheaply; it
is NOT evidence that the graph can pick a better parent. Even a clean win here licenses only KG-B/C,
never a claim about Q.

## MODEL — AMENDED 2026-09-13 BEFORE ANY RESULT EXISTED, AND BEFORE THE GATE WAS RUN
No sklearn or numpy exists in any environment on this machine, and every Python install is
uv-managed / externally managed; forcing a package in was declined as an unnecessary, hard-to-reverse
change to the user's environment. Both models are therefore HAND-ROLLED IN PURE PYTHON, self-tested
on synthetic data with known signal BEFORE touching the real features.
  PRIMARY MODEL:   random forest, 40 trees, max_depth 4, min_samples_leaf 5, max_features 6,
                   quantile candidate thresholds (<=8 per feature), seed 20260913. No tuning.
  SECONDARY MODEL: L2 logistic regression, lambda 1.0, 300 full-batch gradient steps, lr 0.5,
                   features standardised with TRAINING-FOLD statistics only. No tuning.
Both are applied identically to C1, C2 and C3. The kill rule is evaluated on the PRIMARY model.
Class imbalance (70/30) is handled by the balanced-accuracy endpoint itself; no resampling, no class
weights, threshold fixed at 0.5. Registered before running.
