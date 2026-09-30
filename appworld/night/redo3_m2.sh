#!/bin/bash
cd /net/scratch/ymeng3/bos_appworld; L=night/redo3_m2.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md; HF=/net/scratch/ymeng3/local_llm/host2
sub(){ # $1 idx $2 jobsfile $3 tasks $4 steps $5 workers $6 maxjobs $7 extra
  while [ $(squeue -h -u ymeng3 -o %j | grep -c "^aw-m2$") -ge $6 ]; do sleep 30; done; sbatch --parsable --job-name=aw-m2 --array=$1-$1 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/$2,BOS_TASKS=$3,BOS_AW_STEPS=$4,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=900,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=$5$7 run_aw_local.sbatch; }
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 60; done; sleep 10; }
# 1) rescue strategy arms: 50-step continuation, 8 workers, ONE pass at a time; resubmit any missing result once
for rnd in 1 2; do for i in 0 1 2 3 4 5; do line=$(sed -n "$((i+1))p" night/jobs_rs2b.txt); tag=$(echo $line | awk '{print $1}'); sd=$(echo $line | awk '{print $3}'); k=${tag#RS2_h}; [ -e results/${tag}_seed$sd.json ] && continue
  J=$(sub $i night/jobs_rs2b.txt $PWD/night/tasks.json 50 8 1 ",BOS_REPLAY=$PWD/night/replay.json,BOS_HINTS=$PWD/night/hints_$k.json"); echo "$(date) $line -> $J" >> $L; wait_jobs $J; done; done
python3 night/rescue2_score.py > night/rescue2_result.txt 2>&1; cat night/rescue2_result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') APPWORLD CHALLENGE RESCUE ROUND 2 (proper rerun: 8 workers, 1 pass; 3 generated strategies + control; 50-step continuation; seeds 1,2; m2):"; head -12 night/rescue2_result.txt; python3 -c "
import json,glob
for f in sorted(glob.glob('/net/scratch/ymeng3/bos_appworld/results/RS2_*_seed*.json')): d=json.load(open(f)); print(f.split('/')[-1], 'api_err', d['api_errors'])"; } >> $LED
# 2) rubric A/B/C at 30 steps (baseline CH27_F0), 16 workers, <=2 passes
echo "$(date) rubric propose" >> $L; export BOS_GUARD_USD=202; /net/scratch/ymeng3/appworld_scout_venv/bin/python night/rubric_aw.py propose > night/rubric/propose.txt 2>&1; tail -1 night/rubric/propose.txt >> $L
[ -s night/rubric/jobs_s1.txt ] || { echo "STOP: no rubric jobs" >> $L; exit 1; }
n=$(wc -l < night/rubric/jobs_s1.txt); IDS=""; for i in $(seq 0 $((n-1))); do J=$(sub $i night/rubric/jobs_s1.txt $PWD/tasks_challenge50.json 30 16 2 ""); IDS="$IDS $J"; echo "$(date) rubric s1 line $i -> $J" >> $L; sleep 5; done; wait_jobs $IDS
python3 - CH27_F0 <<'PY' > night/rubric/jobs_s2.txt
import json,os,glob,sys
R="/net/scratch/ymeng3/bos_appworld"; BT=sys.argv[1]; bw=sum(json.load(open(f"{R}/results/{BT}_seed1.json"))["won"])
for p in sorted(glob.glob(f"{R}/patches_rubric_aw/RB*.py")):
    pid=os.path.basename(p)[:-3]; f=f"{R}/results/{pid}_seed1.json"
    if os.path.exists(f) and sum(json.load(open(f))["won"])-bw>=2: print(f"{pid} {p} 2 50")
PY
n=$(wc -l < night/rubric/jobs_s2.txt); IDS=""; for i in $(seq 0 $((n-1))); do [ $n -eq 0 ] && break; J=$(sub $i night/rubric/jobs_s2.txt $PWD/tasks_challenge50.json 30 16 2 ""); IDS="$IDS $J"; echo "$(date) rubric s2 line $i -> $J" >> $L; sleep 5; done; [ -n "$IDS" ] && wait_jobs $IDS
/net/scratch/ymeng3/appworld_scout_venv/bin/python night/rubric_aw.py score CH27_F0 > night/rubric/result.txt 2>&1; cat night/rubric/result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') APPWORLD CHALLENGE EVOLVING-RUBRIC A/B/C ROUND 2 (30 steps, 27B local, m2):"; cat night/rubric/result.txt; echo "evolved rubric: night/rubric/evolved_rubric.txt"; } >> $LED; echo "$(date) m2 redo3 done" >> $L
