#!/bin/bash
# E123-v2 (conditional): smoke on m3 -> Discovery s1 (m3) + s2 (m1 after VAL_F0) -> compare vs bare 18/19 -> if 2-seed gain >= +4: Validation s1 (m2) vs VAL_F0
cd /net/scratch/ymeng3/bos_appworld; L=night/phase1.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md; KEY=$(cat /net/scratch/ymeng3/local_llm/vllm_api_key)
sub(){ # $1 tag $2 seed $3 tasks $4 hostfile $5 jobname $6 workers $7 ngames
  while [ $(squeue -h -u ymeng3 -o %j | grep -c "^$5$") -ge 1 ]; do sleep 30; done; printf "$1 patches_phase1/E123v2_conditional.py $2 $7\n" > night/job_$1_s$2.txt
  sbatch --parsable --job-name=$5 --array=0-0 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/night/job_$1_s$2.txt,BOS_TASKS=$PWD/$3,BOS_AW_STEPS=30,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=900,BOS_HOST_FILE=$4,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=$6 run_aw_local.sbatch; }
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 60; done; sleep 10; }
until ssh -i ~/.ssh/autodl_key -o ConnectTimeout=20 -o StrictHostKeyChecking=no -p 39563 root@connect.nma1.seetacloud.com "curl -s -m 5 -H 'Authorization: Bearer $KEY' http://127.0.0.1:6006/v1/models" 2>/dev/null | grep -q "qwen3.8-27b"; do sleep 60; done; echo "$(date) m3 up (e123v2 chain)" >> $L
J=$(sub P1_E123v2_smoke 1 tasks_challenge50.json /net/scratch/ymeng3/local_llm/host3 aw-m3 3 3); wait_jobs $J
python3 -c "
import json;d=json.load(open('/net/scratch/ymeng3/bos_appworld/results/P1_E123v2_smoke_seed1.json'));print('e123v2 smoke won',sum(d['won']),'api_err',d['api_errors'],'mean steps',sum(d['steps'])/len(d['steps']))" >> $L 2>&1
J1=$(sub P1_E123v2_disc 1 tasks_challenge50.json /net/scratch/ymeng3/local_llm/host3 aw-m3 16 50); echo "$(date) E123v2 disc s1 -> $J1 (m3)" >> $L
while [ ! -e results/VAL_F0_seed2.json ]; do sleep 60; done
J2=$(sub P1_E123v2_disc 2 tasks_challenge50.json /net/scratch/ymeng3/local_llm/host aw-m1 16 50); echo "$(date) E123v2 disc s2 -> $J2 (m1)" >> $L; wait_jobs $J1 $J2
python3 - > night/e123v2_result.txt <<'PY'
import json
R="/net/scratch/ymeng3/bos_appworld/results"; tot=0
CLS={"shop":"e7f15ba_1 4242c97_1 dc5c5c6_1 d9987f6_1 20c1328_1 b6d1f70_1 953b296_1 690d51b_1 77bcb81_1 9871968_1 f86d850_1".split(),"cross":"9126bf0_1 f099b4c_1 3fcc458_1 1a79e37_1 e201314_1 a676f2a_1 c8f5f44_1 80acbaf_1 ffea2b5_1 a3ba388_1 33e202d_1 ce73d68_1 c1091c7_1".split(),"multi":"5800354_1 2e9b91e_1 3f3c139_1 7574325_1 09ac073_1 e52623a_1".split()}
for s in (1,2):
    d=json.load(open(f"{R}/P1_E123v2_disc_seed{s}.json")); b=json.load(open(f"{R}/CH27_F0_seed{s}.json")); wd=dict(zip(d["games"],d["won"])); wb=dict(zip(b["games"],b["won"]))
    r=[t for t in wd if wd[t] and not wb[t]]; k=[t for t in wd if wb[t] and not wd[t]]; tot+=sum(wd.values())-sum(wb.values())
    cls={c:(sum(1 for t in v if t in r),sum(1 for t in v if t in k)) for c,v in CLS.items()}
    print(f"E123v2 disc s{s}: {sum(wd.values())}/50 vs bare {sum(wb.values())} (net {sum(wd.values())-sum(wb.values()):+d}) rescued {len(r)} broken {len(k)} api_err {d['api_errors']} mean steps {sum(d['steps'])/50:.1f} | by class rescued/broken {cls}")
print(f"2-seed gain {tot:+d} -> {'GO validation' if tot>=4 else 'STOP (no > noise gain)'}"); open("/net/scratch/ymeng3/bos_appworld/night/e123v2_go.txt","w").write("go" if tot>=4 else "stop")
PY
cat night/e123v2_result.txt >> $L; { echo; echo "$(date '+%F %H:%M') E123-v2 CONDITIONAL SCAFFOLD, Discovery (prereg: GO to Validation iff 2-seed gain >= +4):"; cat night/e123v2_result.txt; } >> $LED
if [ "$(cat night/e123v2_go.txt)" = "go" ]; then J3=$(sub P1_E123v2_val 1 tasks_challenge_val50.json /net/scratch/ymeng3/local_llm/host2 aw-m2 16 50); echo "$(date) E123v2 val s1 -> $J3 (m2)" >> $L; wait_jobs $J3
python3 -c "
import json;R='/net/scratch/ymeng3/bos_appworld/results';d=json.load(open(f'{R}/P1_E123v2_val_seed1.json'));b=json.load(open(f'{R}/VAL_F0_seed1.json'));wd=dict(zip(d['games'],d['won']));wb=dict(zip(b['games'],b['won']));print(f'E123v2 VALIDATION s1: {sum(wd.values())}/50 vs bare {sum(wb.values())} rescued {sum(wd[t] and not wb[t] for t in wd)} broken {sum(wb[t] and not wd[t] for t in wd)} api_err {d[\"api_errors\"]}')" > night/e123v2_val.txt 2>&1; cat night/e123v2_val.txt >> $L; { echo "$(date '+%F %H:%M') E123-v2 VALIDATION:"; cat night/e123v2_val.txt; } >> $LED; fi
echo "$(date) e123v2 chain done" >> $L
