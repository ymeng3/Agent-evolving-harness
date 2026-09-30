# source this instead of (after) /root/autodl-tmp/env.sh: same backend, but every output path points into the cc/ area,
# so nothing is written into the shared working tree /root/autodl-tmp/Agent-evolving-harness or its results/.
source /root/autodl-tmp/env.sh > /dev/null
export CC_ROOT=/root/autodl-tmp/cc CC_REPO=/root/autodl-tmp/cc/Agent-evolving-harness
export BOS_OUT=$CC_REPO/appworld BOS_ALF_OUT=$CC_ROOT/tmp BOS_TMPDIR=$CC_ROOT/tmp TMPDIR=$CC_ROOT/tmp
export BOS_TIMEOUT=900   # a request queued behind a busy shared server waits instead of timing out into a retry / api_error
mkdir -p $CC_ROOT/tmp $BOS_OUT/results
