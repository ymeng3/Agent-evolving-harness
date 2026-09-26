#!/bin/bash
# Failure-driven operator evolution, stages 1-2, unattended (m1). Gen alternatives -> 4 hint passes + control -> score -> ledger.
cd /net/scratch/ymeng3/bos_alfworld; HF=/net/scratch/ymeng3/local_llm/host; L=fd/fd.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 90; done; sleep 10; }
throttle(){ while [ $(squeue -h -u ymeng3 -o "%j" | grep -c "^bos-local") -ge 3 ]; do sleep 60; done; }
J=$(sbatch --parsable --array=0-0 --time=01:00:00 --export=ALL,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_MAX_TOKENS=600,BOS_CMD="python /net/scratch/ymeng3/bos_screens/hag/gen_alts.py > /net/scratch/ymeng3/bos_alfworld/fd/gen.txt 2>&1" run_cmd_local.sbatch)
echo "$(date) gen -> $J" >> $L; wait_jobs $J; tail -1 fd/gen.txt >> $L
[ -s fd/manifest.txt ] || { echo "$(date) STOP: no manifest" >> $L; exit 1; }
printf "FD_ctrl patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py 1\n" > fd/jobs_ctrl.txt
throttle; JS=$(sbatch --parsable --array=0-0 --time=02:00:00 --export=ALL,JOBS_FILE=$PWD/fd/jobs_ctrl.txt,BOS_MANIFEST=$PWD/fd/manifest.txt,BOS_REPLAY=$PWD/fd/replay.json,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=16 run_eval_local.sbatch); echo "$(date) ctrl -> $JS" >> $L
for k in 0 1 2 3; do printf "FD_hint$k patches_rescue/ctrl21_HINT.py 1\n" > fd/jobs_h$k.txt; throttle
  J=$(sbatch --parsable --array=0-0 --time=02:00:00 --export=ALL,JOBS_FILE=$PWD/fd/jobs_h$k.txt,BOS_MANIFEST=$PWD/fd/manifest.txt,BOS_REPLAY=$PWD/fd/replay.json,BOS_HINTS=$PWD/fd/hints_$k.json,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=16 run_eval_local.sbatch); echo "$(date) hint$k -> $J" >> $L; JS="$JS $J"; done
wait_jobs $JS; python fd_score.py > fd/fd_result.txt 2>&1; cat fd/fd_result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') FAILURE-DRIVEN STAGE 1-2 RESULT (unattended, m1, \$0):"; head -8 fd/fd_result.txt; echo "full: /net/scratch/ymeng3/bos_alfworld/fd/fd_result.txt"; } >> $LED
echo "$(date) FD stage 2 done" >> $L
