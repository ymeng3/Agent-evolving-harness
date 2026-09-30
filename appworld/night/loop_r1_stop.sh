#!/bin/bash
# let lean loop finish round 1, then stop the driver and its jobs
cd /net/scratch/ymeng3/bos_appworld
while ! grep -q "=== ROUND 2\|LEAN LOOP done" lean_loop.log; do sleep 60; done
for p in $(ps -eo pid,args | grep "[l]ean_loop.py\|[r]edo3_m1.sh" | awk '{print $1}'); do kill $p; done; sleep 3; scancel -n lean
echo "$(date) lean loop paused after round 1 (user decision)" >> night/redo3_m1.log; echo "$(date '+%F %H:%M') LEAN LOOP PAUSED after round 1; round-1 record: $(grep -E 'COMMIT|keep parent' lean_loop.log | tail -1)" >> ~/agent_knowledge/validation_line/METHOD_REGISTRY.md
