#!/bin/bash
# Phase 2 pilot evaluation: whole candidates (Discovery s1) on 3 boxes -> decompose every valid compound (dependency-closed OFF per edit) -> score
cd /net/scratch/ymeng3/bos_appworld; L=phase2/eval.log; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md; P=/net/scratch/ymeng3/appworld_scout_venv/bin/python
HOSTS=(/net/scratch/ymeng3/local_llm/host /net/scratch/ymeng3/local_llm/host2); NAMES=(aw-m1 aw-m2)   # m3 handed to the coworker (2026-09-28)
sub(){ # $1 tag $2 patch $3 seed $4 box-index $5 extra-env
  local HF=${HOSTS[$4]} JN=${NAMES[$4]}; while [ $(squeue -h -u ymeng3 -o %j | grep -c "^$JN$") -ge 1 ]; do sleep 30; done; printf "$1 $2 $3 50\n" > phase2/job_$1_s$3.txt
  sbatch --parsable --job-name=$JN --array=0-0 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/phase2/job_$1_s$3.txt,BOS_TASKS=$PWD/tasks_challenge50.json,BOS_AW_STEPS=30,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=240,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=12$5 run_aw3_local.sbatch; }
wait_all(){ while squeue -h -u ymeng3 -o %j | grep -q -E "^(aw-m1|aw-m2|aw-m3)$"; do sleep 60; done; sleep 10; }
# stage 1: whole candidates
i=0; $P - <<'PY' > phase2/whole_jobs.txt
import json; [print(c["pid"], c["path"]) for c in json.load(open("/net/scratch/ymeng3/bos_appworld/phase2/candidates.json")) if c["valid"]]
PY
while read -r pid path; do [ -e results/${pid}_seed1.json ] && continue; J=$(sub $pid $path 1 $((i % 2)) ""); echo "$(date) whole $pid -> $J" >> $L; i=$((i+1)); sleep 3; done < phase2/whole_jobs.txt; wait_all
echo "$(date) stage 1 done" >> $L
# stage 2: decomposition of every compound (OFF each edit; harness closes dependencies)
$P - <<'PY' > phase2/off_jobs.txt
import json
for c in json.load(open("/net/scratch/ymeng3/bos_appworld/phase2/candidates.json")):
    if c["valid"] and c["n_edits"] > 1:
        for e in c["edits"]: print(c["pid"], c["path"], e["id"])
PY
i=0; while read -r pid path eid; do tag="${pid}_off_${eid}"; [ -e results/${tag}_seed1.json ] && continue; J=$(sub $tag $path 1 $((i % 2)) ",BOS_EDITS_OFF=$eid"); echo "$(date) off $tag -> $J" >> $L; i=$((i+1)); sleep 3; done < phase2/off_jobs.txt; wait_all
echo "$(date) stage 2 done" >> $L
BOS_GUARD_USD=202 $P phase2/score.py > phase2/result.txt 2>&1; cat phase2/result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') PHASE 2 PILOT RESULT (naive vs failure-conditioned, Discovery s1 whole + dependency-closed OFF for every compound):"; cat phase2/result.txt; } >> $LED; echo "$(date) phase2 pilot done" >> $L
