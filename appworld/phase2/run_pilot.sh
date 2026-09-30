#!/bin/bash
cd /net/scratch/ymeng3/bos_appworld/phase2; L=eval.log; P=/net/scratch/ymeng3/appworld_scout_venv/bin/python
while ! grep -q "address counts" diagnose.log; do sleep 30; done; echo "$(date) diagnoser done: $(grep 'address counts' diagnose.log | cut -c1-200)" >> $L
BOS_GUARD_USD=202 APPWORLD_ROOT=/net/scratch/ymeng3/appworld_v2 $P search.py 10 > search.log 2>&1; tail -1 search.log >> $L
{ echo; echo "$(date '+%F %H:%M') PHASE 2 PILOT SEARCH OUTPUT: $(tail -1 search.log)"; grep -E "^P2_" search.log; } >> ~/agent_knowledge/validation_line/METHOD_REGISTRY.md
bash eval_pipeline.sh
