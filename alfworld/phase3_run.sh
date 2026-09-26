#!/bin/bash
# PHASE 3 end-to-end (m2). Step1 cand vs parent (paired, seed1, train48) -> Step2 credit for improved cands (local: replay-to-trigger
# continuation B=48; global: adaptive 16/32/48) -> Step4 window ablation (4 passes x 32) -> report -> ledger.
cd /net/scratch/ymeng3/bos_alfworld; HF=/net/scratch/ymeng3/local_llm/host2; P3=patches_p3; L=$P3/phase3.log; H=/net/scratch/ymeng3/bos_screens/hag; LED=~/agent_knowledge/validation_line/METHOD_REGISTRY.md
wait_jobs(){ while true; do q=0; for j in "$@"; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 60; done; sleep 10; }
throttle(){ while [ $(squeue -h -u ymeng3 -o "%j" | grep -c "^bos-m2") -ge 3 ]; do sleep 45; done; }
sub(){ # $1 jobs file line-index-range e.g. 0-0, $2 jobs file, $3 manifest, $4 extra env
  throttle; sbatch --parsable --job-name=bos-m2 --array=$1 --time=02:30:00 --export=ALL,JOBS_FILE=$PWD/$2,BOS_MANIFEST=$PWD/$3,BOS_HOST_FILE=$HF,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=${BOS_W:-24}$4 run_eval_local.sbatch; }
echo "$(date) PHASE 3 start" >> $L; T0=$(date +%s)
# ---- Step 1
step1_round(){ IDS=""; n=$(wc -l < $P3/jobs_step1.txt); for i in $(seq 0 $((n-1))); do tag=$(sed -n "$((i+1))p" $P3/jobs_step1.txt | awk '{print $1}'); [ -e results/${tag}_seed1.json ] && continue
  if squeue -h -u ymeng3 -o "%j %i" | grep -q .; then :; fi; J=$(sub $i-$i $P3/jobs_step1.txt slices/train48.txt ""); IDS="$IDS $J"; echo "$(date) step1 $i ($tag) -> $J" >> $L; sleep 5; done; [ -n "$IDS" ] && wait_jobs $IDS; }
# wait for jobs already running from a previous launch, then (re)submit whatever is still missing, up to 3 rounds (tunnel failures)
RUN=$(squeue -h -u ymeng3 -o "%i" | tr '\n' ' '); [ -n "$RUN" ] && wait_jobs $RUN
for rnd in 1 2 3; do step1_round; miss=0; for tag in $(awk '{print $1}' $P3/jobs_step1.txt); do [ -e results/${tag}_seed1.json ] || miss=1; done; [ $miss -eq 0 ] && break; echo "$(date) step1 round $rnd: missing results, resubmitting" >> $L; done
python3 $H/phase3_decide.py cands >> $L; echo "$(date) step1 done ($(( ($(date +%s)-T0)/60 )) min)" >> $L
# ---- Step 2 (window ablation submitted alongside to use idle slots)
WIDS=""; n=$(wc -l < $P3/jobs_window.txt); for i in $(seq 0 $((n-1))); do J=$(BOS_W=16 sub $i-$i $P3/jobs_window.txt slices/train48.txt ""); WIDS="$WIDS $J"; echo "$(date) window $i -> $J" >> $L; sleep 5; done
python3 - <<'PY' > $P3/todo_units.txt
import json; C=json.load(open("patches_p3/cands_decision.json")); U=json.load(open("patches_p3/units.json"))
for k,v in U.items():
    if C.get(v["cand"],{}).get("decompose"): print(k, v["kind"], v["C"], v["OFF"], v["Ctag"], v["unit"])
PY
echo "$(date) units to credit: $(wc -l < $P3/todo_units.txt)" >> $L; cat $P3/todo_units.txt >> $L
LIDS=""
while read -r key kind cp op ctag unit; do
  s="p3_${key/:/_}"
  if [ "$kind" = "local" ]; then comp=$( [ "$unit" = "choose_fallback" ] && echo fallback || ( [ "$unit" = "retry_policy" ] && echo retry || echo parse ) )
    python3 $H/build_probeL.py $ctag $comp "$cp" "$op" $s 48 1 >> $L 2>&1
    if [ -s probeL/${s}_manifest.txt ]; then J=$(sub 0-0 probeL/${s}_jobs.txt probeL/${s}_manifest.txt ",BOS_REPLAY=$PWD/probeL/${s}_replay.json"); LIDS="$LIDS $J"; echo "$(date) local $key -> $J" >> $L; else echo "$(date) local $key: no activation states -> treat as global" >> $L; echo "$key global $cp $op $ctag $unit" >> $P3/todo_units_global.txt; fi
  else echo "$key global $cp $op $ctag $unit" >> $P3/todo_units_global.txt; fi
done < $P3/todo_units.txt
# global units: adaptive batches 16 -> 32 -> 48, all active units advance in parallel
declare -A NEXT; declare -A DONE
while read -r key kind cp op ctag unit; do NEXT[$key]=16; done < <(cat $P3/todo_units_global.txt 2>/dev/null)
while true; do
  IDS=""; any=0
  for key in "${!NEXT[@]}"; do [ -n "${DONE[$key]}" ] && continue; n=${NEXT[$key]}; op=$(grep "^$key " $P3/todo_units_global.txt | awk '{print $4}'); tag="P3OFF_${key/:/_}_n$n"
    printf "$tag $op 1 $n\n" > $P3/jobs_$tag.txt; J=$(BOS_W=16 sub 0-0 $P3/jobs_$tag.txt slices/train48.txt ""); IDS="$IDS $J"; echo "$(date) global $key n=$n -> $J" >> $L; any=1; sleep 3; done
  [ $any -eq 0 ] && break; wait_jobs $IDS
  for key in "${!NEXT[@]}"; do [ -n "${DONE[$key]}" ] && continue; n=${NEXT[$key]}; tag="P3OFF_${key/:/_}_n$n"; [ -e results/${tag}_seed1.json ] || { J=$(BOS_W=16 sub 0-0 $P3/jobs_$tag.txt slices/train48.txt ""); echo "$(date) RESUBMIT $tag -> $J" >> $L; wait_jobs $J; }; done
  for key in "${!NEXT[@]}"; do [ -n "${DONE[$key]}" ] && continue; n=${NEXT[$key]}; d=$(python3 $H/phase3_decide.py unit "$key" $n); echo "$(date) $key n=$n $d" >> $L
    if echo "$d" | grep -q '"stop": true' || [ $n -ge 48 ]; then DONE[$key]=1; else NEXT[$key]=$((n+16)); fi; done
done
wait_jobs $LIDS $WIDS
for key in $(awk '{print $1}' $P3/todo_units.txt); do grep -q "^$key " $P3/todo_units_global.txt 2>/dev/null || { d=$(python3 $H/phase3_decide.py unit "$key" 48); echo "$(date) $key local $d" >> $L; }; done
python3 $H/phase3_report.py > $P3/report.txt 2>&1; cat $P3/report.txt >> $L
{ echo; echo "$(date '+%F %H:%M') PHASE 3 FRESH END-TO-END RESULT (unattended, m2, $(( ($(date +%s)-T0)/60 )) min wall):"; cat $P3/report.txt; echo "log: $PWD/$L"; } >> $LED
echo "$(date) PHASE 3 done" >> $L
