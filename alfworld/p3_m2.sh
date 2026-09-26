#!/bin/bash
cd /net/scratch/ymeng3/bos_alfworld; HF=/net/scratch/ymeng3/local_llm/host2; L=p3_m2.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md; JS=""
throttle(){ while [ $(squeue -h -u ymeng3 -o "%j" | grep -c "^bos-m2") -ge 3 ]; do sleep 60; done; }
for name in "r6 fallback" "MECH07 fallback" "L2c4 fallback" "r4 retry" "naive r5 retry" "E1_HR retry+hist" "L2c4 HISTORY" "r4 HISTORY" "ctrl21 memory" "N04 history"; do
  s="p2_$(echo "$name" | tr ' ' '_')"; line=$(cat probeL/${s}_jobs.txt); set -- $line; op=$2
  printf "PL_${s}_OFF_rep2 $op 2 32\n" > probeL/${s}_jobs_rep2.txt; throttle
  J=$(sbatch --parsable --job-name=bos-m2 --array=0-0 --time=03:00:00 --export=ALL,JOBS_FILE=$PWD/probeL/${s}_jobs_rep2.txt,BOS_MANIFEST=$PWD/probeL/${s}_manifest.txt,BOS_REPLAY=$PWD/probeL/${s}_replay.json,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=24 run_eval_local.sbatch)
  echo "$(date) $s rep2 -> $J" >> $L; JS="$JS $J"; sleep 15; done
while true; do q=0; for j in $JS; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 120; done; sleep 10
python3 /net/scratch/ymeng3/bos_screens/hag/p3_score.py > p3_result.txt 2>&1
{ echo; echo "$(date '+%F %H:%M') LOCAL-CF PHASE 3 CROSS-SEED RESULT (unattended, m2, B=32, \$0):"; cat p3_result.txt; } >> $LED; echo "$(date) p3 done" >> $L
