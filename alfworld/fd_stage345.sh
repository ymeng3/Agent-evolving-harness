#!/bin/bash
# m1, after AppWorld chain: stage3 (proposer) -> stage4 passes (train48 + local check) -> stage5 inheritance -> held-out 3-agent -> ledger
cd /net/scratch/ymeng3/bos_alfworld; HF=/net/scratch/ymeng3/local_llm/host; L=fd/fd.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 90; done; sleep 10; }
throttle(){ while [ $(squeue -h -u ymeng3 -o "%j" | grep -c "^bos-local") -ge 3 ]; do sleep 60; done; }
submit_lines(){ # $1 jobs file, $2 manifest, $3 extra env ; echoes job ids
  n=$(wc -l < $1); ids=""; for i in $(seq 0 $((n-1))); do throttle; J=$(sbatch --parsable --array=$i-$i --time=02:30:00 --export=ALL,JOBS_FILE=$PWD/$1,BOS_MANIFEST=$PWD/$2,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=24$3 run_eval_local.sbatch); ids="$ids $J"; echo "$(date) $1:$i -> $J" >> $L; sleep 10; done; echo $ids; }
while ! grep -q "aw chain done" /net/scratch/ymeng3/bos_appworld/aw_chain.log 2>/dev/null; do sleep 120; done
J=$(sbatch --parsable --array=0-0 --time=01:00:00 --export=ALL,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_CMD="python /net/scratch/ymeng3/bos_screens/hag/fd_stage3.py > /net/scratch/ymeng3/bos_alfworld/fd/stage3.txt 2>&1" run_cmd_local.sbatch); echo "$(date) stage3 -> $J" >> $L; wait_jobs $J; cat fd/stage3.txt >> $L
[ -s fd/jobs_stage4.txt ] || { echo "$(date) STOP: stage3 produced no jobs" >> $L; exit 1; }
IDS=$(submit_lines fd/jobs_stage4.txt slices/train48.txt ""); IDS="$IDS $(submit_lines fd/jobs_local.txt fd/manifest.txt ",BOS_REPLAY=$PWD/fd/replay.json")"; wait_jobs $IDS
J=$(sbatch --parsable --array=0-0 --time=00:40:00 --export=ALL,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_CMD="python /net/scratch/ymeng3/bos_screens/hag/fd_stage5.py > /net/scratch/ymeng3/bos_alfworld/fd/stage5.txt 2>&1" run_cmd_local.sbatch); echo "$(date) stage5 -> $J" >> $L; wait_jobs $J; cat fd/stage5.txt >> $L
IDS=$(submit_lines fd/jobs_heldout.txt slices/heldout48.txt ""); wait_jobs $IDS
python3 /net/scratch/ymeng3/bos_screens/hag/fd_final.py > fd/final.txt 2>&1; cat fd/final.txt >> $L
{ echo; echo "$(date '+%F %H:%M') FAILURE-DRIVEN OPERATOR EVOLUTION, STAGES 3-5 RESULT (unattended, m1):"; grep -E "rescue events|operators|search-only|spent" fd/stage3.txt; cat fd/stage5.txt; cat fd/final.txt; echo "files: /net/scratch/ymeng3/bos_alfworld/fd/"; } >> $LED
echo "$(date) FD stages 3-5 done" >> $L
