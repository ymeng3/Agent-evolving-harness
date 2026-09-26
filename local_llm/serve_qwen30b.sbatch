#!/usr/bin/env bash
#SBATCH --job-name=vllm-qwen30b
#SBATCH --partition=yuxinchen-contrib,general
#SBATCH --gres=gpu:a40:2
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=24:00:00
#SBATCH --output=/net/scratch/ymeng3/local_llm/logs/serve-%j.out
source /opt/conda/etc/profile.d/conda.sh && conda activate /net/scratch/ymeng3/conda_envs/vllm
export HF_HOME=/net/scratch/ymeng3/hf_cache TMPDIR=/local/ymeng3/tmp_${SLURM_JOB_ID}; mkdir -p "$TMPDIR"
PORT=8400; echo "http://$(hostname -f):$PORT/v1" > /net/scratch/ymeng3/local_llm/ENDPOINT
python -m vllm.entrypoints.openai.api_server --model Qwen/Qwen3-30B-A3B-Instruct-2507 \
  --served-model-name qwen/qwen3-30b-a3b-instruct-2507 --dtype bfloat16 --tensor-parallel-size 2 \
  --max-model-len 16384 --gpu-memory-utilization 0.92 --port $PORT --host 0.0.0.0
