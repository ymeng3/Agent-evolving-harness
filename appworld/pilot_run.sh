#!/bin/bash
cd /net/scratch/ymeng3/bos_appworld; L=pilot/pilot.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md; HF=/net/scratch/ymeng3/local_llm/host
J=$(cat /net/scratch/ymeng3/local_llm/awf0full_jobid); while squeue -j $J -h | grep -q .; do sleep 30; done; sleep 5
[ -e results/AW_F0full_seed1.json ] || { echo "$(date) STOP: no F0full" >> $L; exit 1; }
/net/scratch/ymeng3/appworld_scout_venv/bin/python pilot_build.py >> $L 2>&1
printf "PILOT_ctrl none 1\nPILOT_ctrl none 2\nPILOT_docfirst patches/AW_HINT.py 1\nPILOT_docfirst patches/AW_HINT.py 2\nPILOT_verify patches/AW_HINT.py 1\nPILOT_verify patches/AW_HINT.py 2\n" > pilot/jobs.txt
IDS=""; for i in 0 1 2 3 4 5; do line=$(sed -n "$((i+1))p" pilot/jobs.txt); pol=$(echo $line | awk '{print $1}' | sed 's/PILOT_//'); H=""; [ "$pol" != "ctrl" ] && H=",BOS_HINTS=$PWD/pilot/hints_$pol.json"
  while [ $(squeue -h -u ymeng3 -o "%j" | grep -c "aw-local") -ge 3 ]; do sleep 30; done
  J=$(sbatch --parsable --array=$i-$i --time=01:00:00 --export=ALL,JOBS_FILE=$PWD/pilot/jobs.txt,BOS_TASKS=$PWD/pilot/tasks10.json,BOS_REPLAY=$PWD/pilot/replay.json$H,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=4 run_aw_local.sbatch); IDS="$IDS $J"; echo "$(date) $line -> $J" >> $L; sleep 5; done
while true; do q=0; for j in $IDS; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 60; done; sleep 5
python3 pilot_score.py > pilot/result.txt 2>&1; cat pilot/result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') APPWORLD RESCUE PILOT RESULT (10 partial failures, branch before first state-changing call; ctrl vs docfirst vs verify hints; seeds 1,2; unattended, \$0):"; cat pilot/result.txt; } >> $LED; echo "$(date) pilot done" >> $L
