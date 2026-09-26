#!/usr/bin/env bash
# Phase 2 remainder on machine 2, throttled: at most 3 SLURM jobs at a time, 24 workers each.
cd /net/scratch/ymeng3/bos_alfworld; export PATH=/net/scratch/ymeng3/llm_agent_opd/envs/seed/bin:$PATH; H=/net/scratch/ymeng3/bos_screens/hag; LED=/home/ymeng3/agent_knowledge/validation_line/METHOD_REGISTRY.md; L=p2_m2.log; HF=/net/scratch/ymeng3/local_llm/host2
B="ssh -i $HOME/.ssh/autodl_key -o StrictHostKeyChecking=no -o ConnectTimeout=20 -p 37456 root@connect.bjb1.seetacloud.com"
until $B 'grep -q "Application startup complete" /root/autodl-tmp/vllm.log' 2>/dev/null; do sleep 60; done; echo "$(date) m2 server ready" >> $L
throttle(){ while [ $(squeue -h -u ymeng3 -o "%j" | grep -c "^bos-local") -ge 3 ]; do sleep 60; done; }
# Stage A: step-logged C passes (48 games) for candidates lacking logs
python $H/p2_components.py newc > jobs_p2c.txt; n=$(wc -l < jobs_p2c.txt); i=0; JA=""
while read -r line; do echo "$line" > jobs_p2c_$i.txt; throttle; J=$(sbatch --parsable --array=0-0 --time=03:00:00 --export=ALL,JOBS_FILE=$PWD/jobs_p2c_$i.txt,BOS_MANIFEST=$PWD/slices/validation_train96.txt,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=24 run_eval_local.sbatch); JA="$JA $J"; echo "$(date) stageA $line -> $J" >> $L; i=$((i+1)); done < jobs_p2c.txt
while true; do q=0; for j in $JA; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 120; done; echo "$(date) stage A done" >> $L
# Stage B: OFF-only branch sets (B<=48) for components without a result yet
python $H/p2_components.py list | while IFS='|' read -r name src kind cp op g; do
  s="p2_$(echo "$name" | tr ' ' '_')"; [ -e results/PL_${s}_OFF_rep1_seed1.json ] && continue; [ -e results/${src}_seed1.json ] || { echo "skip $name (no C log)" >> $L; continue; }
  python $H/build_probeL.py $src $kind "$cp" "$op" $s 48 1 >> $L 2>&1; n=$(wc -l < probeL/${s}_jobs.txt 2>/dev/null || echo 0); [ "$n" -gt 0 ] && [ -s probeL/${s}_manifest.txt ] || { echo "skip $name (no activation states)" >> $L; continue; }
  throttle; J=$(sbatch --parsable --array=0-0 --time=03:00:00 --export=ALL,JOBS_FILE=$PWD/probeL/${s}_jobs.txt,BOS_MANIFEST=$PWD/probeL/${s}_manifest.txt,BOS_REPLAY=$PWD/probeL/${s}_replay.json,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=24 run_eval_local.sbatch); echo "$(date) $s -> $J" >> $L; echo $J >> /net/scratch/ymeng3/local_llm/p2m2_jobs
done
sleep 60; while true; do q=0; for j in $(cat /net/scratch/ymeng3/local_llm/p2m2_jobs 2>/dev/null); do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 180; done
python $H/p2_score.py > $H/p2_result.txt 2>&1; { echo "$(date '+%F %H:%M') LOCAL-CF PHASE 2 RESULT (unattended, machine 2, throttled; B nested 8/16/32/48):"; cat $H/p2_result.txt; } >> $LED; echo "$(date) phase 2 done" >> $L
