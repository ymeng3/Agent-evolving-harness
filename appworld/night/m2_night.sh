#!/bin/bash
cd /net/scratch/ymeng3/bos_appworld; L=night/m2_night.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md; HF=/net/scratch/ymeng3/local_llm/host2
sub(){ # $1 idx $2 jobsfile $3 tasks $4 extra
  while [ $(squeue -h -u ymeng3 -o %j | grep -c "aw-local") -ge 4 ]; do sleep 30; done; sbatch --parsable --array=$1-$1 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/$2,BOS_TASKS=$3,BOS_AW_STEPS=50,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=300,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=4$4 run_aw_local.sbatch; }
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 60; done; sleep 10; }
while ! grep -q "^arm " /net/scratch/ymeng3/tau2_scout/tau2_27b_result.txt 2>/dev/null; do sleep 120; done; echo "$(date) tau2 done; rescue round 2" >> $L
J=$(cd /net/scratch/ymeng3/bos_alfworld && sbatch --parsable --job-name=cmd-local --array=0-0 --time=01:30:00 --export=ALL,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_CMD="/net/scratch/ymeng3/appworld_scout_venv/bin/python /net/scratch/ymeng3/bos_appworld/night/gen_alts_aw.py > /net/scratch/ymeng3/bos_appworld/night/gen.txt 2>&1" run_cmd_local.sbatch); echo "$(date) gen_alts -> $J" >> $L; wait_jobs $J; tail -1 night/gen.txt >> $L
[ -s night/tasks.json ] || { echo "STOP: no tasks" >> $L; exit 1; }
printf "RS2_ctrl none 1\nRS2_ctrl none 2\nRS2_h0 patches/AW_HINT.py 1\nRS2_h0 patches/AW_HINT.py 2\nRS2_h1 patches/AW_HINT.py 1\nRS2_h1 patches/AW_HINT.py 2\nRS2_h2 patches/AW_HINT.py 1\nRS2_h2 patches/AW_HINT.py 2\n" > night/jobs_rs2.txt
IDS=""; for i in 0 1 2 3 4 5 6 7; do line=$(sed -n "$((i+1))p" night/jobs_rs2.txt); pol=$(echo $line | awk '{print $1}' | sed 's/RS2_//'); H=""; [ "$pol" != "ctrl" ] && H=",BOS_HINTS=$PWD/night/hints_${pol#h}.json"
  J=$(sub $i night/jobs_rs2.txt $PWD/night/tasks.json ",BOS_REPLAY=$PWD/night/replay.json$H"); IDS="$IDS $J"; echo "$(date) $line -> $J" >> $L; sleep 5; done; wait_jobs $IDS
python3 night/rescue2_score.py > night/rescue2_result.txt 2>&1; cat night/rescue2_result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') APPWORLD CHALLENGE RESCUE ROUND 2 (branch before first state-changing call; 3 generated strategies + control; 50-step continuation; seeds 1,2; m2):"; head -12 night/rescue2_result.txt; echo "full: night/rescue2_result.txt"; } >> $LED
# ---- rubric A/B/C
echo "$(date) rubric propose" >> $L; export BOS_GUARD_USD=202; /net/scratch/ymeng3/appworld_scout_venv/bin/python night/rubric_aw.py propose > night/rubric/propose.txt 2>&1; tail -2 night/rubric/propose.txt >> $L
[ -s night/rubric/jobs_s1.txt ] || { echo "STOP: no rubric jobs" >> $L; exit 1; }
n=$(wc -l < night/rubric/jobs_s1.txt); IDS=""; for i in $(seq 0 $((n-1))); do J=$(sub $i night/rubric/jobs_s1.txt $PWD/tasks_challenge50.json ""); IDS="$IDS $J"; echo "$(date) rubric s1 line $i -> $J" >> $L; sleep 5; done; wait_jobs $IDS
while [ ! -s night/steps.txt ] && [ ! -e results/CH27S50_F0_seed2.json ]; do sleep 120; done; BT=CH27S50_F0; [ -e results/CH27S50_F0_seed1.json ] || BT=CH27_F0
python3 - <<PY > night/rubric/jobs_s2.txt
import json,os,glob
R="/net/scratch/ymeng3/bos_appworld"; b=json.load(open(f"{R}/results/${BT}_seed1.json")); bw=sum(b["won"])
for p in sorted(glob.glob(f"{R}/patches_rubric_aw/RB*.py")):
    pid=os.path.basename(p)[:-3]; f=f"{R}/results/{pid}_seed1.json"
    if os.path.exists(f) and sum(json.load(open(f))["won"])-bw>=2: print(f"{pid} {p} 2 50")
PY
n=$(wc -l < night/rubric/jobs_s2.txt); IDS=""; for i in $(seq 0 $((n-1))); do [ $n -eq 0 ] && break; J=$(sub $i night/rubric/jobs_s2.txt $PWD/tasks_challenge50.json ""); IDS="$IDS $J"; echo "$(date) rubric s2 line $i -> $J" >> $L; sleep 5; done; [ -n "$IDS" ] && wait_jobs $IDS
/net/scratch/ymeng3/appworld_scout_venv/bin/python night/rubric_aw.py score $BT > night/rubric/result.txt 2>&1; cat night/rubric/result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') APPWORLD CHALLENGE EVOLVING-RUBRIC A/B/C ROUND 2 (27B local, m2; s1 all, s2 for s1>=+2):"; cat night/rubric/result.txt; echo "evolved rubric: night/rubric/evolved_rubric.txt"; } >> $LED; echo "$(date) m2 night done" >> $L
