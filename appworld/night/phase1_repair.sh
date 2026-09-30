#!/bin/bash
# after both Phase-1 orchestrators: rerun any P1_*/VAL_F0 pass with >50 API errors (8 workers, single pass per box) + clean loop seed-2 confirmation; rescore; ledger
cd /net/scratch/ymeng3/bos_appworld; L=night/phase1.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md
while ! grep -q "phase1 done" $L; do sleep 120; done; sleep 20
python3 - > night/repair_list.txt <<'PY'
import json,glob,os
R="/net/scratch/ymeng3/bos_appworld/results"
for f in sorted(glob.glob(f"{R}/P1_*_seed*.json")+glob.glob(f"{R}/VAL_F0_seed*.json")):
    d=json.load(open(f))
    if d["api_errors"]>50:
        tag=d["tag"]; s=d["seed"]; patch=d.get("patch") or "none"; tasks="tasks_challenge_val50.json" if tag.endswith("_val") or tag.startswith("VAL_") else "tasks_challenge50.json"
        print(f"{tag} {patch} {s} {tasks} {d['api_errors']}")
PY
echo "$(date) repair list:" >> $L; cat night/repair_list.txt >> $L
n=$(wc -l < night/repair_list.txt); i=0
while read -r tag patch s tasks err; do [ -z "$tag" ] && continue; rm -f results/${tag}_seed$s.json; box=$((i % 2)); HF=/net/scratch/ymeng3/local_llm/host; JN=aw-m1; [ $box -eq 1 ] && HF=/net/scratch/ymeng3/local_llm/host2 && JN=aw-m2
  while [ $(squeue -h -u ymeng3 -o %j | grep -c "^$JN$") -ge 1 ]; do sleep 30; done
  printf "$tag $patch $s\n" > night/job_repair_$i.txt; J=$(sbatch --parsable --job-name=$JN --array=0-0 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/night/job_repair_$i.txt,BOS_TASKS=$PWD/$tasks,BOS_AW_STEPS=30,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=900,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=8 run_aw_local.sbatch); echo "$(date) repair $tag s$s ($err errs) -> $J on $JN" >> $L; i=$((i+1)); sleep 5; done < night/repair_list.txt
# clean loop seed-2 confirmation for c1
rm -f results/LL_r1_c1_adjust_temperature_and_forma_seed2.json; printf "LL_r1_c1_adjust_temperature_and_forma /net/scratch/ymeng3/bos_appworld/patches_lean/LL_r1_c1_adjust_temperature_and_forma.py 2\n" > night/job_repair_loop.txt
while [ $(squeue -h -u ymeng3 -o %j | grep -c "^aw-m1$") -ge 1 ]; do sleep 30; done
J=$(sbatch --parsable --job-name=aw-m1 --array=0-0 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/night/job_repair_loop.txt,BOS_TASKS=$PWD/tasks_challenge50.json,BOS_AW_STEPS=30,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=900,BOS_HOST_FILE=/net/scratch/ymeng3/local_llm/host,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=8 run_aw_local.sbatch); echo "$(date) loop c1 seed2 clean rerun -> $J" >> $L
while squeue -h -u ymeng3 -o %j | grep -q -E "^(aw-m1|aw-m2)$"; do sleep 60; done; sleep 10
python3 night/phase1_score.py > night/phase1_result.txt 2>&1; cat night/phase1_result.txt >> $L
python3 - >> night/phase1_result.txt <<'PY'
import json,os
R="/net/scratch/ymeng3/bos_appworld/results"; f=f"{R}/LL_r1_c1_adjust_temperature_and_forma_seed2.json"
if os.path.exists(f):
    d=json.load(open(f)); b=json.load(open(f"{R}/CH27_F0_seed2.json")); print(f"\nLOOP c1 seed-2 clean: {sum(d['won'])}/50 vs parent {sum(b['won'])} (api_err {d['api_errors']}); s1 was 20 vs 18 -> 2-seed gain {sum(d['won'])-sum(b['won'])+2:+d} (commit rule: s2>=parent and total>=+3)")
PY
{ echo; echo "$(date '+%F %H:%M') PHASE 1 FINAL (after repair reruns of passes with >50 API errors; all rows below have <=50):"; cat night/phase1_result.txt; python3 -c "
import json,glob; [print(f.split('/')[-1],'api_err',json.load(open(f))['api_errors']) for f in sorted(glob.glob('/net/scratch/ymeng3/bos_appworld/results/P1_*_seed*.json')+glob.glob('/net/scratch/ymeng3/bos_appworld/results/VAL_F0_seed*.json'))]"; } >> $LED; echo "$(date) phase1 repair done" >> $L
