#!/bin/bash
cd /net/scratch/ymeng3/bos_appworld; L=night/redo_m1.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md; HF=/net/scratch/ymeng3/local_llm/host; KEY=$(cat /net/scratch/ymeng3/local_llm/vllm_api_key)
sub(){ while [ $(squeue -h -u ymeng3 -o %j | grep -c -E "^(lean|aw-m1)$") -ge 2 ]; do sleep 30; done; sbatch --parsable --job-name=aw-m1 --array=$1-$1 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/$2,BOS_TASKS=$PWD/tasks_challenge50.json,BOS_AW_STEPS=$3,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=300,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=16 run_aw_local.sbatch; }
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 60; done; sleep 10; }
until ssh -i ~/.ssh/autodl_key -o ConnectTimeout=20 -o StrictHostKeyChecking=no -p 50445 root@connect.nma1.seetacloud.com "curl -s -m 5 -H 'Authorization: Bearer $KEY' http://127.0.0.1:6006/v1/models" 2>/dev/null | grep -q "qwen3.8-27b"; do sleep 60; done; echo "$(date) m1 27B up" >> $L
# 1) step-budget test
printf "CH27S50_F0 none 1\nCH27S50_F0 none 2\n" > night/jobs_s50.txt; echo "$(date) step test: waiting for the two running 50-step passes" >> $L
while [ ! -e results/CH27S50_F0_seed1.json ] || [ ! -e results/CH27S50_F0_seed2.json ]; do sleep 60; done; sleep 10
python3 - > night/steps_result.txt <<'PY'
import json
R="/net/scratch/ymeng3/bos_appworld/results"; tot30=tot50=0; lines=[]
for s in (1,2):
    a=json.load(open(f"{R}/CH27_F0_seed{s}.json")); b=json.load(open(f"{R}/CH27S50_F0_seed{s}.json")); wa=dict(zip(a["games"],a["won"])); wb=dict(zip(b["games"],b["won"]))
    lines.append(f"seed {s}: 30 steps {sum(wa.values())}/50 -> 50 steps {sum(wb.values())}/50 (rescued {sum(wb[t] and not wa[t] for t in wa)}, broken {sum(wa[t] and not wb[t] for t in wa)}, api_err {b['api_errors']}, mean steps {sum(b['steps'])/50:.1f})"); tot30+=sum(wa.values()); tot50+=sum(wb.values())
steps=50 if tot50-tot30>=5 else 30; print("\n".join(lines)); print(f"decision: STEPS={steps} (gain {tot50-tot30:+d} over 2 seeds; rule >= +5)"); open("/net/scratch/ymeng3/bos_appworld/night/steps.txt","w").write(str(steps))
PY
cat night/steps_result.txt >> $L; { echo; echo "$(date '+%F %H:%M') APPWORLD CHALLENGE STEP-BUDGET TEST (30 vs 50 steps, bare 27B, m1):"; cat night/steps_result.txt; } >> $LED
STEPS=$(cat night/steps.txt); BT=$([ "$STEPS" = "50" ] && echo CH27S50_F0 || echo CH27_F0)
# 2) challenge harness rows at the chosen step cap
printf "CH27_full patches/AW_full.py 1\nCH27_full patches/AW_full.py 2\nCH27_verify patches/AW_verify.py 1\nCH27_errhint patches/AW_errhint.py 1\nCH27_docfirst patches/AW_docfirst.py 1\n" > jobs_ch27_h.txt
IDS=""; for i in 0 1 2 3 4; do line=$(sed -n "$((i+1))p" jobs_ch27_h.txt); tag=$(echo $line | awk "{print \$1}"); sd=$(echo $line | awk "{print \$3}"); [ -e results/${tag}_seed$sd.json ] && continue; J=$(sub $i jobs_ch27_h.txt $STEPS); IDS="$IDS $J"; echo "$(date) harness line $i -> $J" >> $L; sleep 5; done; [ -n "$IDS" ] && wait_jobs $IDS
python3 - $BT > ch27_h_result.txt <<'PY'
import json,os,sys
R="/net/scratch/ymeng3/bos_appworld/results"; BT=sys.argv[1]
def load(t,s):
    f=f"{R}/{t}_seed{s}.json"; return json.load(open(f)) if os.path.exists(f) else None
base={s:load(BT,s) for s in (1,2)}; print(f"baseline {BT}")
print(f"{'run (challenge-50)':20s} seed  won  meanG  partial  G=0  api_err  rescued  broken   rescued tasks")
for t,s in ((BT,1),(BT,2),("CH27_full",1),("CH27_full",2),("CH27_verify",1),("CH27_errhint",1),("CH27_docfirst",1)):
    d=load(t,s)
    if not d: print(t,s,"missing"); continue
    b=base.get(s); resc=brk=[]
    if b and t!=BT:
        wb=dict(zip(b["games"],b["won"])); wd=dict(zip(d["games"],d["won"])); resc=[g for g in wd if wd[g] and not wb[g]]; brk=[g for g in wd if wb[g] and not wd[g]]
    part=sum(1 for w,g in zip(d["won"],d["G"]) if not w and g and 0<g<1); z=sum(1 for w,g in zip(d["won"],d["G"]) if not w and not g)
    print(f"{t:20s} {s}    {sum(d['won']):3d}  {d['mean_G']:.2f}   {part:3d}    {z:3d}   {d['api_errors']:4d}   {len(resc):3d}     {len(brk):3d}   {resc}")
PY
cat ch27_h_result.txt >> $L; { echo; echo "$(date '+%F %H:%M') APPWORLD CHALLENGE-50 HARNESS ROWS at STEPS=$STEPS (rerun, m1):"; cat ch27_h_result.txt; } >> $LED
# 3) lean loop
python3 -c "
import json; json.dump({'round':1,'parent':'/net/scratch/ymeng3/bos_appworld/patches_lean/F0_parent.py','parent_tag':'$BT','history':[],'memory':[]}, open('/net/scratch/ymeng3/bos_appworld/night/lean_state.json','w'), indent=1)"
echo "$(date) lean loop start STEPS=$STEPS parent_tag=$BT" >> $L
cd /net/scratch/ymeng3/bos_alfworld; export LL_ARENA=appworld LL_BACKEND=local LL_PARENT=/net/scratch/ymeng3/bos_appworld/patches_lean/F0_parent.py LL_STATE=/net/scratch/ymeng3/bos_appworld/night/lean_state.json LL_ROUNDS=4 LL_K=4 LL_NGAMES=50 LL_TASKS=/net/scratch/ymeng3/bos_appworld/tasks_challenge50.json BOS_AW_STEPS=$STEPS BOS_MODEL=qwen/qwen3.8-27b BOS_HOST_FILE=$HF BOS_GUARD_USD=202
: > /net/scratch/ymeng3/bos_appworld/lean_loop.log; python3 lean_loop.py >> /net/scratch/ymeng3/bos_appworld/night/lean_loop.stdout 2>&1; echo "$(date) lean loop finished" >> /net/scratch/ymeng3/bos_appworld/$L
