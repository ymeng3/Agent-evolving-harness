#!/bin/bash
cd /net/scratch/ymeng3/bos_appworld; L=night/m1_night.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md; HF=/net/scratch/ymeng3/local_llm/host
sub(){ while [ $(squeue -h -u ymeng3 -o %j | grep -c -E "^(lean|aw-local)$") -ge 2 ]; do sleep 30; done; sbatch --parsable --array=$1-$1 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/$2,BOS_TASKS=$PWD/tasks_challenge50.json,BOS_AW_STEPS=$3,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=300,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=4 run_aw_local.sbatch; }
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 60; done; sleep 10; }
while [ ! -s ch27_h_result.txt ]; do sleep 120; done; echo "$(date) challenge harness rows done; step-budget test" >> $L
printf "CH27S50_F0 none 1\nCH27S50_F0 none 2\n" > night/jobs_s50.txt; J1=$(sub 0 night/jobs_s50.txt 50); sleep 5; J2=$(sub 1 night/jobs_s50.txt 50); wait_jobs $J1 $J2
python3 - > night/steps_result.txt <<'PY'
import json
R="/net/scratch/ymeng3/bos_appworld/results"; tot30=tot50=0; lines=[]
for s in (1,2):
    a=json.load(open(f"{R}/CH27_F0_seed{s}.json")); b=json.load(open(f"{R}/CH27S50_F0_seed{s}.json")); wa=dict(zip(a["games"],a["won"])); wb=dict(zip(b["games"],b["won"]))
    resc=sum(wb[t] and not wa[t] for t in wa); brk=sum(wa[t] and not wb[t] for t in wa); tot30+=sum(wa.values()); tot50+=sum(wb.values())
    lines.append(f"seed {s}: 30 steps {sum(wa.values())}/50 -> 50 steps {sum(wb.values())}/50 (rescued {resc}, broken {brk}, api_err {b['api_errors']}, mean steps {sum(b['steps'])/50:.1f})")
steps = 50 if tot50 - tot30 >= 5 else 30; print("\n".join(lines)); print(f"decision: STEPS={steps} (gain {tot50-tot30:+d} over 2 seeds; rule >= +5)")
open("/net/scratch/ymeng3/bos_appworld/night/steps.txt","w").write(str(steps))
PY
cat night/steps_result.txt >> $L; { echo; echo "$(date '+%F %H:%M') APPWORLD CHALLENGE STEP-BUDGET TEST (30 vs 50 steps, bare 27B, m1):"; cat night/steps_result.txt; } >> $LED
STEPS=$(cat night/steps.txt); PT=$([ "$STEPS" = "50" ] && echo CH27S50_F0 || echo CH27_F0)
python3 -c "
import json; json.dump({'round':1,'parent':'/net/scratch/ymeng3/bos_appworld/patches_lean/F0_parent.py','parent_tag':'$PT','history':[],'memory':[]}, open('/net/scratch/ymeng3/bos_appworld/night/lean_state.json','w'), indent=1)"
echo "$(date) lean loop start: STEPS=$STEPS parent_tag=$PT" >> $L
cd /net/scratch/ymeng3/bos_alfworld; export LL_ARENA=appworld LL_BACKEND=local LL_PARENT=/net/scratch/ymeng3/bos_appworld/patches_lean/F0_parent.py LL_STATE=/net/scratch/ymeng3/bos_appworld/night/lean_state.json LL_ROUNDS=4 LL_K=4 LL_NGAMES=50 LL_TASKS=/net/scratch/ymeng3/bos_appworld/tasks_challenge50.json BOS_AW_STEPS=$STEPS BOS_MODEL=qwen/qwen3.8-27b BOS_HOST_FILE=$HF BOS_GUARD_USD=202
python3 lean_loop.py >> /net/scratch/ymeng3/bos_appworld/night/lean_loop.stdout 2>&1; echo "$(date) lean loop finished" >> /net/scratch/ymeng3/bos_appworld/$L
