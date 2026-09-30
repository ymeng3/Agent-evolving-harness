#!/usr/bin/env bash
#SBATCH --job-name=aw-local
#SBATCH --partition=yuxinchen-contrib,general
#SBATCH --cpus-per-task=12
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --output=/net/scratch/ymeng3/bos_appworld/slurm/%x-%A_%a.out
#SBATCH --error=/net/scratch/ymeng3/bos_appworld/slurm/%x-%A_%a.err
# Same as run_eval.sbatch, but the BACKBONE goes to the self-hosted vLLM endpoint through a per-job ssh tunnel.
set -euo pipefail
export TMPDIR=/local/ymeng3/tmp_${SLURM_JOB_ID}; mkdir -p "$TMPDIR"
export PATH=/net/scratch/ymeng3/appworld_scout_venv/bin:$PATH
export PYTHONNOUSERSITE=1 ALFWORLD_DATA=/net/scratch/ymeng3/llm_agent_opd/data/alfworld OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export RAY_TMPDIR="$TMPDIR"
PORT=$((20000 + SLURM_JOB_ID % 20000)); APIKEY=$(cat /net/scratch/ymeng3/local_llm/vllm_api_key)
sleep $((RANDOM % 20))   # de-synchronise simultaneous array tasks (AutoDL sshd MaxStartups)
TUN=""; ok=0
for attempt in $(seq 1 20); do
  ssh -i $HOME/.ssh/autodl_key -o StrictHostKeyChecking=no -o ConnectTimeout=20 -o ServerAliveInterval=30 -o ExitOnForwardFailure=yes -N -L 127.0.0.1:$PORT:127.0.0.1:6006 -p $(cut -d" " -f2 ${BOS_HOST_FILE:-/net/scratch/ymeng3/local_llm/host}) root@$(cut -d" " -f1 ${BOS_HOST_FILE:-/net/scratch/ymeng3/local_llm/host}) &
  TUN=$!
  for i in $(seq 1 15); do curl -s -m 5 -H "Authorization: Bearer $APIKEY" http://127.0.0.1:$PORT/v1/models 2>/dev/null | grep -q "${BOS_MODEL:-qwen}" && { ok=1; break; }; sleep 2; done
  [ $ok -eq 1 ] && break
  echo "tunnel attempt $attempt failed; retrying"; kill $TUN 2>/dev/null; wait $TUN 2>/dev/null; sleep $((10 + RANDOM % 20))
done
trap 'kill $TUN 2>/dev/null; rm -rf "$TMPDIR"' EXIT
[ $ok -eq 1 ] || { echo "TUNNEL/ENDPOINT NOT READY after 20 attempts"; exit 3; }

export BOS_TOP_P=${BOS_TOP_P:-} BOS_TOP_K=${BOS_TOP_K:-}
export BOS_BASE_URL=http://127.0.0.1:$PORT/v1 BOS_API_KEY=$(cat /net/scratch/ymeng3/local_llm/vllm_api_key) BOS_PRICE_IN=0 BOS_PRICE_OUT=0
export APPWORLD_ROOT=/net/scratch/ymeng3/appworld_v2
JOBS=${JOBS_FILE:?}
LINE=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$JOBS"); set -- $LINE
TAG=$1; PATCH=$2; SEED=$3; NG=${4:-}
echo "job $SLURM_ARRAY_TASK_ID: tag=$TAG patch=$PATCH seed=$SEED manifest=appworld base=$BOS_BASE_URL host=$(hostname) start=$(date +%H:%M:%S)"
cd /net/scratch/ymeng3/bos_appworld
if [ -n "$NG" ]; then python bos_appworld_v2.py eval --patch "$PATCH" --seed "$SEED" --tag "$TAG" --n-games "$NG" --workers ${BOS_WORKERS:-64}
else python bos_appworld_v2.py eval --patch "$PATCH" --seed "$SEED" --tag "$TAG" --workers ${BOS_WORKERS:-64}; fi
echo "end=$(date +%H:%M:%S)"
