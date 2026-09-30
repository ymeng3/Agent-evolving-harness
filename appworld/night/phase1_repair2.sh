#!/bin/bash
# second repair pass with the auto-reconnecting tunnel: rerun every P1_*/VAL_F0/loop-s2 row still >50 API errors; one pass per box, 8 workers
cd /net/scratch/ymeng3/bos_appworld; L=night/phase1.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md
while ! grep -q "phase1 repair done" $L; do sleep 120; done; sleep 20
KEY=$(cat /net/scratch/ymeng3/local_llm/vllm_api_key); ssh -i ~/.ssh/autodl_key -o ConnectTimeout=20 -o StrictHostKeyChecking=no -p 39563 root@connect.nma1.seetacloud.com "curl -s -m 5 -H 'Authorization: Bearer $KEY' http://127.0.0.1:6006/v1/models" 2>/dev/null | grep -q "qwen3.8-27b" || echo "$(date) m3 not up at repair2 start; rows assigned to m3 will wait on their tunnel readiness (20 attempts)" >> $L
for rnd in 1 2; do
python3 - > night/repair2_list.txt <<'PY'
import json,glob
R="/net/scratch/ymeng3/bos_appworld/results"
for f in sorted(glob.glob(f"{R}/P1_*_seed*.json")+glob.glob(f"{R}/VAL_F0_seed*.json")+glob.glob(f"{R}/LL_r1_c1_adjust_temperature_and_forma_seed2.json")):
    d=json.load(open(f))
    if d["api_errors"]>50:
        tag=d["tag"]; s=d["seed"]; patch=d.get("patch") or "none"; tasks="tasks_challenge_val50.json" if (tag.endswith("_val") or tag.startswith("VAL_")) else "tasks_challenge50.json"
        print(f"{tag} {patch} {s} {tasks} {d['api_errors']}")
PY
echo "$(date) repair2 round $rnd list:" >> $L; cat night/repair2_list.txt >> $L; [ -s night/repair2_list.txt ] || break
i=0; while read -r tag patch s tasks err; do [ -z "$tag" ] && continue; rm -f results/${tag}_seed$s.json; box=$((i % 3)); HF=/net/scratch/ymeng3/local_llm/host; JN=aw-m1; [ $box -eq 1 ] && HF=/net/scratch/ymeng3/local_llm/host2 && JN=aw-m2; [ $box -eq 2 ] && HF=/net/scratch/ymeng3/local_llm/host3 && JN=aw-m3
  while [ $(squeue -h -u ymeng3 -o %j | grep -c "^$JN$") -ge 1 ]; do sleep 30; done
  printf "$tag $patch $s\n" > night/job_repair2_$i.txt; J=$(sbatch --parsable --job-name=$JN --array=0-0 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/night/job_repair2_$i.txt,BOS_TASKS=$PWD/$tasks,BOS_AW_STEPS=30,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=900,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=8 run_aw_local.sbatch); echo "$(date) repair2 $tag s$s ($err errs) -> $J on $JN" >> $L; i=$((i+1)); sleep 5; done < night/repair2_list.txt
while squeue -h -u ymeng3 -o %j | grep -q -E "^(aw-m1|aw-m2|aw-m3)$"; do sleep 60; done; sleep 10
done
python3 night/phase1_score.py > night/phase1_result.txt 2>&1
python3 - >> night/phase1_result.txt <<'PY'
import json,os
R="/net/scratch/ymeng3/bos_appworld/results"; f=f"{R}/LL_r1_c1_adjust_temperature_and_forma_seed2.json"
if os.path.exists(f):
    d=json.load(open(f)); b=json.load(open(f"{R}/CH27_F0_seed2.json")); print(f"\nLOOP c1 seed-2 clean: {sum(d['won'])}/50 vs parent {sum(b['won'])} (api_err {d['api_errors']}); s1 was 20 vs 18 -> 2-seed gain {sum(d['won'])-sum(b['won'])+2:+d}")
PY
cat night/phase1_result.txt >> $L; { echo; echo "$(date '+%F %H:%M') PHASE 1 FINAL after repair2 (auto-reconnecting tunnel; rows with >50 API errors are listed as unusable):"; cat night/phase1_result.txt; python3 -c "
import json,glob; [print(f.split('/')[-1],'api_err',json.load(open(f))['api_errors']) for f in sorted(glob.glob('/net/scratch/ymeng3/bos_appworld/results/P1_*_seed*.json')+glob.glob('/net/scratch/ymeng3/bos_appworld/results/VAL_F0_seed*.json'))]"; } >> $LED; echo "$(date) phase1 repair2 done" >> $L
