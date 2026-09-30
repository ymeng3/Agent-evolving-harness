#!/usr/bin/env bash
# qsub.sh TAG command...  -> appends one job to the FIFO queue. The command runs under bash in $CC_REPO/appworld after
# sourcing tools/queue/ccenv.sh, e.g.
#   qsub.sh CC_F0_fix BOS_TASKS=tasks_challenge50.json BOS_PARSE_UNCLOSED=1 python bos_appworld_v3.py eval --patch none --seed 1 --tag CC_F0_fix --workers 8
set -euo pipefail
Q=${CCQ_DIR:-/root/autodl-tmp/cc/queue}; mkdir -p $Q/{pending,running,done,failed,logs}
[ $# -ge 2 ] || { echo "usage: qsub.sh TAG command..."; exit 2; }
TAG=$1; shift
case "$TAG" in CC_*) ;; *) echo "TAG must start with CC_ (isolation from other users' tags)"; exit 2;; esac
ID=$(date +%Y%m%d-%H%M%S)_$TAG
printf '%s\n' "$*" > $Q/pending/$ID.job
echo "queued $ID"
