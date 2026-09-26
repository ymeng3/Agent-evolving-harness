#!/usr/bin/env bash
#SBATCH --job-name=bos-alfworld
#SBATCH --partition=yuxinchen-contrib,general
#SBATCH --cpus-per-task=4
#SBATCH --mem=24G
#SBATCH --time=03:00:00
#SBATCH --output=/net/scratch/ymeng3/bos_alfworld/slurm/%x-%A_%a.out
#SBATCH --error=/net/scratch/ymeng3/bos_alfworld/slurm/%x-%A_%a.err
set -euo pipefail
export TMPDIR=/local/ymeng3/tmp_${SLURM_JOB_ID}; mkdir -p "$TMPDIR"
export PATH=/net/scratch/ymeng3/llm_agent_opd/envs/seed/bin:$PATH
export PYTHONNOUSERSITE=1 ALFWORLD_DATA=/net/scratch/ymeng3/llm_agent_opd/data/alfworld OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
export RAY_TMPDIR="$TMPDIR"
JOBS=${JOBS_FILE:-/net/scratch/ymeng3/bos_alfworld/jobs.txt}
LINE=$(sed -n "$((SLURM_ARRAY_TASK_ID + 1))p" "$JOBS")   # "TAG PATCH SEED [NGAMES]"
set -- $LINE
TAG=$1; PATCH=$2; SEED=$3; NG=${4:-}
echo "job $SLURM_ARRAY_TASK_ID: tag=$TAG patch=$PATCH seed=$SEED ngames=${NG:-all} host=$(hostname) start=$(date +%H:%M:%S)"
cd /net/scratch/ymeng3/bos_alfworld; export BOS_PROVIDER=${BOS_PROVIDER:-}
if [ -n "$NG" ]; then python bos_alfworld.py eval --patch "$PATCH" --seed "$SEED" --tag "$TAG" --n-games "$NG" --workers ${BOS_WORKERS:-8}
else python bos_alfworld.py eval --patch "$PATCH" --seed "$SEED" --tag "$TAG" --workers ${BOS_WORKERS:-8}; fi
echo "end=$(date +%H:%M:%S)"
rm -rf "$TMPDIR"
