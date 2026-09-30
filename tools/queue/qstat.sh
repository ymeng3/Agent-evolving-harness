#!/usr/bin/env bash
# qstat.sh -> runner state, server load, running / pending jobs, last finished jobs
Q=${CCQ_DIR:-/root/autodl-tmp/cc/queue}
flock -n $Q/runner.lock true 2>/dev/null && echo "RUNNER: NOT RUNNING (start: screen -dmS ccq bash tools/queue/qrunner.sh)" || echo "RUNNER: up"
echo "status: $(cat $Q/status 2>/dev/null)"
curl -s -m 5 -H "Authorization: Bearer $(cat /root/autodl-tmp/vllm_api_key)" http://127.0.0.1:6006/metrics | awk '/^vllm:num_requests_(running|waiting)\{/ {sub(/\{.*/, "", $1); printf "%s=%s  ", $1, $2} END {print ""}'
echo "running:"; for f in $Q/running/*.job; do [ -e "$f" ] && echo "  $(basename $f .job)  [$(tail -1 $Q/logs/$(basename $f .job).log 2>/dev/null | cut -c1-100)]"; done
echo "pending:"; ls $Q/pending/ 2>/dev/null | sed 's/\.job$//; s/^/  /'
echo "finished (last 10):"; tail -10 $Q/history.tsv 2>/dev/null | sed 's/^/  /'
