#!/usr/bin/env bash
# Single FIFO runner for the shared GPU box. Start once:  screen -dmS ccq bash tools/queue/qrunner.sh
# One job at a time. Before starting a job it waits until the vLLM server is quiet (running+waiting requests from
# everyone < CCQ_MAX_LOAD for 3 checks in a row), so it yields to other users' experiments instead of queueing behind
# them and risking BOS_TIMEOUT api_errors. Controls:  touch $Q/pause (stop taking jobs)  |  touch $Q/force (skip the wait once)
Q=${CCQ_DIR:-/root/autodl-tmp/cc/queue}; mkdir -p $Q/{pending,running,done,failed,logs}
exec 9> $Q/runner.lock; flock -n 9 || { echo "runner already running"; exit 1; }
HERE=$(cd "$(dirname "$0")" && pwd); MAX_LOAD=${CCQ_MAX_LOAD:-8}   # ~ where the A800 saturates; with BOS_TIMEOUT=900 sharing only slows jobs down
load() { curl -s -m 5 -H "Authorization: Bearer $(cat /root/autodl-tmp/vllm_api_key)" http://127.0.0.1:6006/metrics \
         | awk '/^vllm:num_requests_(running|waiting)\{/ {s += $2; n++} END {if (n) print int(s); else print "down"}'; }
st() { echo "$(date '+%F %T') $*" > $Q/status; }
while true; do
  if [ -e $Q/pause ]; then st "paused"; sleep 30; continue; fi
  J=$(ls $Q/pending/*.job 2>/dev/null | sort | head -1)
  if [ -z "$J" ]; then st "idle"; sleep 30; continue; fi
  ID=$(basename $J .job); ok=0
  while [ $ok -lt 3 ]; do
    [ -e $Q/force ] && { rm -f $Q/force; break; }
    L=$(load)
    if [ "$L" != "down" ] && [ "$L" -lt $MAX_LOAD ]; then ok=$((ok + 1)); else ok=0; st "waiting for $ID: server load=$L (need <$MAX_LOAD)"; fi
    sleep 20
  done
  mv $J $Q/running/; st "running $ID"; T0=$(date +%s)
  bash -c "source $HERE/ccenv.sh; cd \$CC_REPO/appworld; $(cat $Q/running/$ID.job)" > $Q/logs/$ID.log 2>&1; RC=$?
  DT=$(( $(date +%s) - T0 ))
  if [ $RC -eq 0 ]; then mv $Q/running/$ID.job $Q/done/; else mv $Q/running/$ID.job $Q/failed/; fi
  printf '%s\t%s\trc=%s\t%ss\n' "$(date '+%F %T')" "$ID" "$RC" "$DT" >> $Q/history.tsv
done
