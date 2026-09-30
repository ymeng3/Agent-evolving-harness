#!/bin/bash
cd /net/scratch/ymeng3/bos_appworld; L=night/redo_m2.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md; HF=/net/scratch/ymeng3/local_llm/host2; KEY=$(cat /net/scratch/ymeng3/local_llm/vllm_api_key)
sub(){ while [ $(squeue -h -u ymeng3 -o %j | grep -c "aw-m2") -ge 2 ]; do sleep 30; done; sbatch --parsable --job-name=aw-m2 --array=$1-$1 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/$2,BOS_TASKS=$3,BOS_AW_STEPS=50,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=300,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=16$4 run_aw_local.sbatch; }
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 60; done; sleep 10; }
until ssh -i ~/.ssh/autodl_key -o ConnectTimeout=20 -o StrictHostKeyChecking=no -p 37456 root@connect.bjb1.seetacloud.com "curl -s -m 5 -H 'Authorization: Bearer $KEY' http://127.0.0.1:6006/v1/models" 2>/dev/null | grep -q "qwen3.8-27b"; do sleep 60; done; echo "$(date) m2 27B up" >> $L
# 1) rescue round 2 strategy arms (control exists)
printf "RS2_h0 patches/AW_HINT.py 1\nRS2_h0 patches/AW_HINT.py 2\nRS2_h1 patches/AW_HINT.py 1\nRS2_h1 patches/AW_HINT.py 2\nRS2_h2 patches/AW_HINT.py 1\nRS2_h2 patches/AW_HINT.py 2\n" > night/jobs_rs2b.txt
IDS=""; for i in 0 1 2 3 4 5; do line=$(sed -n "$((i+1))p" night/jobs_rs2b.txt); tag=$(echo $line | awk '{print $1}'); sd=$(echo $line | awk '{print $3}'); k=${tag#RS2_h}; [ -e results/${tag}_seed$sd.json ] && continue; squeue -h -u ymeng3 -o "%j" | grep -q "^aw-local$" && [ $i -le 3 ] && continue; J=$(sub $i night/jobs_rs2b.txt $PWD/night/tasks.json ",BOS_REPLAY=$PWD/night/replay.json,BOS_HINTS=$PWD/night/hints_$k.json"); IDS="$IDS $J"; echo "$(date) $line -> $J" >> $L; sleep 5; done
while [ $(ls results/RS2_h[012]_seed[12].json 2>/dev/null | wc -l) -lt 6 ]; do sleep 60; done; sleep 10
python3 night/rescue2_score.py > night/rescue2_result.txt 2>&1; cat night/rescue2_result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') APPWORLD CHALLENGE RESCUE ROUND 2 (rerun; 3 generated strategies + control; 50-step continuation; seeds 1,2; m2):"; head -12 night/rescue2_result.txt; echo "full: night/rescue2_result.txt"; } >> $LED
# 2) rubric A/B/C
echo "$(date) rubric propose" >> $L; export BOS_GUARD_USD=202; /net/scratch/ymeng3/appworld_scout_venv/bin/python night/rubric_aw.py propose > night/rubric/propose.txt 2>&1; tail -1 night/rubric/propose.txt >> $L
[ -s night/rubric/jobs_s1.txt ] || { echo "STOP: no rubric jobs" >> $L; exit 1; }
n=$(wc -l < night/rubric/jobs_s1.txt); IDS=""; for i in $(seq 0 $((n-1))); do J=$(sub $i night/rubric/jobs_s1.txt $PWD/tasks_challenge50.json ""); IDS="$IDS $J"; echo "$(date) rubric s1 line $i -> $J" >> $L; sleep 5; done; wait_jobs $IDS
while [ ! -s night/steps.txt ]; do sleep 120; done; BT=$([ "$(cat night/steps.txt)" = "50" ] && echo CH27S50_F0 || echo CH27_F0)
python3 - $BT <<'PY' > night/rubric/jobs_s2.txt
import json,os,glob,sys
R="/net/scratch/ymeng3/bos_appworld"; BT=sys.argv[1]; b=json.load(open(f"{R}/results/{BT}_seed1.json")); bw=sum(b["won"])
for p in sorted(glob.glob(f"{R}/patches_rubric_aw/RB*.py")):
    pid=os.path.basename(p)[:-3]; f=f"{R}/results/{pid}_seed1.json"
    if os.path.exists(f) and sum(json.load(open(f))["won"])-bw>=2: print(f"{pid} {p} 2 50")
PY
n=$(wc -l < night/rubric/jobs_s2.txt); IDS=""; for i in $(seq 0 $((n-1))); do [ $n -eq 0 ] && break; J=$(sub $i night/rubric/jobs_s2.txt $PWD/tasks_challenge50.json ""); IDS="$IDS $J"; echo "$(date) rubric s2 line $i -> $J" >> $L; sleep 5; done; [ -n "$IDS" ] && wait_jobs $IDS
/net/scratch/ymeng3/appworld_scout_venv/bin/python night/rubric_aw.py score $BT > night/rubric/result.txt 2>&1; cat night/rubric/result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') APPWORLD CHALLENGE EVOLVING-RUBRIC A/B/C ROUND 2 (rerun; 27B local, m2):"; cat night/rubric/result.txt; echo "evolved rubric: night/rubric/evolved_rubric.txt"; } >> $LED; echo "$(date) m2 redo done" >> $L
