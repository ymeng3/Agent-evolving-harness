#!/usr/bin/env bash
# One BIT round (docs/design/BIT_IMPLEMENTATION_PLAN.md): tree -> propose (qsub) -> screen -> [D10 bench] -> branch build -> qsub branch jobs
# -> readout + admission -> validation arm. Documentation-grade: each phase is one step of the round, run by hand on the box and checked
# before the next (the propose / branch / val phases only QUEUE jobs; wait for the queue to drain, tools/queue/qstat.sh).
# usage (on the box, from anywhere):  R=R1 BASE=H1 bash appworld/boost/bit_round.sh <phase>
#   phases: tree | propose | screen | bench | branch | readout | valarm
# Variables (env):
#   R         round id; outputs go to appworld/bit/$R/ (tags CC_BIT_${R}_...)                              [R1]
#   BASE      base preset: H1 (benchmark round, unpatched H1 disc) or H2 (real round, H1origP disc = H2 base)  [H1]
#   RUNS      comma list of base discovery logs (overrides the preset), relative to appworld/
#   BASE_VAL  comma list of the base's val logs (valarm readout)
#   BASE_ENV  file with the base job's env (K=V ... or the whole qsub line); BOS_TASKS/BOS_REPLAY/BOS_HINTS are stripped by bit_branch.
#             MUST be the exact env of the base discovery job (copy it from $CCQ_DIR/done/*_<base tag>.job).
#   P         proposer run id ($R-unique, e.g. P1; ablations P1w = --outcome-detail won, P1ns = --no-sibling, P1ft = --failed-tests)
#   PROPOSE_ARGS  extra bit_propose args for the ablations                                                       []
#   INSTR     tid -> instruction json                                                                            [results/instructions_all100.json]
# Never enable MTP on the vLLM server for these jobs (prefix-cache loss on the hybrid model); concurrency comes from --workers.
set -euo pipefail
source /root/autodl-tmp/cc/Agent-evolving-harness/tools/queue/ccenv.sh
cd $CC_REPO/appworld
QSUB="bash $CC_REPO/tools/queue/qsub.sh"
R=${R:-R1}; BASE=${BASE:-H1}; P=${P:-P1}; PROPOSE_ARGS=${PROPOSE_ARGS:-}; INSTR=${INSTR:-results/instructions_all100.json}
case $BASE in
  H1) RUNS=${RUNS:-results/CC_H1_F0_disc_seed1.json,results/CC_H1_F0_disc_seed2.json}
      BASE_VAL=${BASE_VAL:-results/CC_H1_F0_val_seed1.json,results/CC_H1_F0_val_seed2.json} ;;
  H2) RUNS=${RUNS:-results/CC_H1origP_disc_seed1.json,results/CC_H1origP_disc_seed2.json}
      BASE_VAL=${BASE_VAL:-results/CC_H1origP_val_seed1.json,results/CC_H1origP_val_seed2.json} ;;
  *) echo "BASE must be H1 or H2 (or set RUNS/BASE_VAL/BASE_ENV yourself)"; exit 2 ;;
esac
BASE_ENV=${BASE_ENV:-bit/$R/base_env.txt}
OUT=bit/$R; mkdir -p $OUT/logs
REFS=boost/bit_refs/D10_ref.json,boost/bit_refs/null_note.json
CANDS=$(ls $OUT/cands_*.jsonl 2>/dev/null | paste -sd, - || true)   # every proposer run of this round (P1 + ablations)

case ${1:-} in
tree)   # memory tree + cases (top 20, <= 2 per task); check: root wins = total wins, every loss has a case when --top is large
  python boost/bit_tree.py --runs $RUNS --instr $INSTR --out $OUT/tree.json --top 20 --max-per-task 2 | tee $OUT/logs/tree.log ;;

propose)   # hindsight self-proposer, one call per case, thinking on, <= 6 concurrent calls; queued so it waits for a quiet server.
  # inspect one prompt first:  python boost/bit_propose.py --tree $OUT/tree.json --runs $RUNS --instr $INSTR --out /dev/null --run-id $P --dry-run
  $QSUB CC_BIT_${R}_propose_$P python boost/bit_propose.py --tree $OUT/tree.json --runs $RUNS --instr $INSTR \
        --out $OUT/cands_$P.jsonl --run-id $P --n-cases 20 --k-per-case 2 --workers 6 --max-tokens 16000 --patch-dir patches_ccbit/$R $PROPOSE_ARGS ;;

screen)   # offline screening of all valid candidates of the round (+ refs scored, never kept)
  python boost/bit_screen.py --cands $CANDS --runs $RUNS --instr $INSTR --tree $OUT/tree.json --out $OUT/screen.json --refs $REFS \
         --k-within 4 --k-raw 4 --max-won-fire 0.05 --workers 6 | tee $OUT/logs/screen.log ;;

bench)   # BASE=H1 only: D10 rediscovery benchmark against the frozen gold set (prereg A23); sanity = D10_ref passes, null_note fails
  [ $BASE = H1 ] || { echo "bench is defined on the H1 disc base only"; exit 2; }
  python boost/bit_bench_d10.py bench --cands $CANDS --screen $OUT/screen.json --tree $OUT/tree.json --runs $RUNS --instr $INSTR \
         --gold boost/bit_refs/d10_gold_H1disc.json --out $OUT/bench_d10.json | tee $OUT/logs/bench.log ;;

branch)   # branch-at-fire states for every kept candidate (first firing per (tid, seed)); D10_ref forced in on the H1 round as the
          # positive control of the branch estimator. Then queue the jobs (2 arms x (candidate, origin seed)).
  [ -s $BASE_ENV ] || { echo "write the base job's env to $BASE_ENV first"; exit 2; }
  FORCE=""; [ $BASE = H1 ] && FORCE="--refs boost/bit_refs/D10_ref.json --force-cid ref_d10_answer_on_action_task"
  python boost/bit_branch.py build --screen $OUT/screen.json --cands $CANDS --runs $RUNS --instr $INSTR --out $OUT/branch --round $R \
         --env-file $BASE_ENV --reps 1 --max-states 40 $FORCE | tee $OUT/logs/branch_build.log
  bash $OUT/branch/jobs.txt ;;

readout)   # after every CC_BIT_${R}_c* job is in $CCQ_DIR/done: a-bar on won and G, task-bootstrap CI, sign-flip + Holm, admission
  python boost/bit_branch.py readout --build $OUT/branch --results results --screen $OUT/screen.json --out $OUT/branch/readout.json \
         | tee $OUT/logs/readout.log ;;

valarm)   # compile the admitted specs into one patch, print (and here: queue) the val seed 1/2 jobs; then the multi-metric readout
  python boost/bit_branch.py valarm --admitted $OUT/branch/admitted.json --round $R --env-file $BASE_ENV --base-val $BASE_VAL \
         --base-name $BASE | tee $OUT/logs/valarm.log
  grep "qsub.sh CC_" $OUT/logs/valarm.log | bash
  echo "after both val jobs finish, run the multi_metric_readout line printed above" ;;

*) sed -n '2,20p' "$0"; exit 2 ;;
esac
