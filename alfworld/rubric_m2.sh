#!/bin/bash
# m2, after Phase 3 and FD stage 3 (needs events.json): rubric A/B/C proposals -> held-out passes on m2 -> score -> ledger
cd /net/scratch/ymeng3/bos_alfworld; mkdir -p rubric patches_rubric; HF=/net/scratch/ymeng3/local_llm/host2; L=rubric/rubric.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 90; done; sleep 10; }
throttle(){ while [ $(squeue -h -u ymeng3 -o "%j" | grep -c "^bos-m2") -ge 3 ]; do sleep 60; done; }
while ! grep -q "p3 done" p3_m2.log 2>/dev/null; do sleep 120; done
while ! grep -q "stage3 ->" fd/fd.log 2>/dev/null || [ ! -s fd/events.json ]; do sleep 120; done; sleep 60
J=$(sbatch --parsable --job-name=bos-m2 --array=0-0 --time=01:30:00 --export=ALL,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_CMD="python /net/scratch/ymeng3/bos_screens/hag/rubric_abc.py > /net/scratch/ymeng3/bos_alfworld/rubric/abc.txt 2>&1" run_cmd_local.sbatch); echo "$(date) rubric abc -> $J" >> $L; wait_jobs $J; cat rubric/abc.txt >> $L
[ -s rubric/jobs_heldout.txt ] || { echo "$(date) STOP: no rubric jobs" >> $L; exit 1; }
n=$(wc -l < rubric/jobs_heldout.txt); IDS=""
for i in $(seq 0 $((n-1))); do throttle; J=$(sbatch --parsable --job-name=bos-m2 --array=$i-$i --time=02:30:00 --export=ALL,JOBS_FILE=$PWD/rubric/jobs_heldout.txt,BOS_MANIFEST=$PWD/slices/heldout48.txt,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=24 run_eval_local.sbatch); IDS="$IDS $J"; echo "$(date) rubric:$i -> $J" >> $L; sleep 10; done
wait_jobs $IDS; python3 /net/scratch/ymeng3/bos_screens/hag/rubric_score.py > rubric/result.txt 2>&1; cat rubric/result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') EVOLVING-RUBRIC A/B/C RESULT (unattended, m2, held-out48, seeds 1,2):"; cat rubric/result.txt; echo "evolved rubric: /net/scratch/ymeng3/bos_alfworld/rubric/evolved_rubric.txt"; } >> $LED
echo "$(date) rubric done" >> $L
