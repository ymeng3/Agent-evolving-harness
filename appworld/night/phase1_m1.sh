#!/bin/bash
cd /net/scratch/ymeng3/bos_appworld; L=night/phase1.log; HF=/net/scratch/ymeng3/local_llm/host; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md
sub(){ while [ $(squeue -h -u ymeng3 -o %j | grep -c -E "^(lean|aw-m1)$") -ge 2 ]; do sleep 30; done; sbatch --parsable --job-name=aw-m1 --array=$1-$1 --time=03:59:00 --export=ALL,JOBS_FILE=$PWD/$2,BOS_TASKS=$3,BOS_AW_STEPS=30,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=900,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=16 run_aw_local.sbatch; }
while ! grep -q "lean loop paused" night/redo3_m1.log; do sleep 120; done; sleep 30
printf "P1_E1_disc patches_phase1/E1_pagination.py 2\nP1_E2_disc patches_phase1/E2_crossapp_memory.py 2\nP1_E3_disc patches_phase1/E3_subgoal_tracker.py 2\nP1_E123_disc patches_phase1/E123_all.py 2\n" > night/jobs_p1_disc2.txt
printf "P1_E123_val patches_phase1/E123_all.py 2\nP1_E1_val patches_phase1/E1_pagination.py 2\n" > night/jobs_p1_val2.txt
for i in 0 1 2 3; do tag=$(sed -n "$((i+1))p" night/jobs_p1_disc2.txt | awk '{print $1}'); [ -e results/${tag}_seed2.json ] && continue; J=$(sub $i night/jobs_p1_disc2.txt $PWD/tasks_challenge50.json); echo "$(date) m1 $tag s2 -> $J" >> $L; sleep 5; done
for i in 0 1; do tag=$(sed -n "$((i+1))p" night/jobs_p1_val2.txt | awk '{print $1}'); [ -e results/${tag}_seed2.json ] && continue; J=$(sub $i night/jobs_p1_val2.txt $PWD/tasks_challenge_val50.json); echo "$(date) m1 $tag s2 -> $J" >> $L; sleep 5; done
while squeue -h -u ymeng3 -o %j | grep -q -E "^(aw-m1|aw-m2)$"; do sleep 60; done; while ! grep -q "m2 phase1 passes done" $L; do sleep 60; done
python3 night/phase1_score.py > night/phase1_result.txt 2>&1; cat night/phase1_result.txt >> $L
{ echo; echo "$(date '+%F %H:%M') PHASE 1 RESULT (hand-written scaffolds E1 pagination / E2 cross-app memory / E3 sub-goal tracker / E123; challenge 30 steps, local 27B; Discovery vs CH27_F0, Validation vs VAL_F0):"; cat night/phase1_result.txt; } >> $LED; echo "$(date) phase1 done" >> $L
