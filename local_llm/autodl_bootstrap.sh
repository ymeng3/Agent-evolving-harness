#!/usr/bin/env bash
# AutoDL bootstrap for self-hosted Qwen3-30B-A3B-Instruct-2507 (bf16, single 80GB GPU). Paste step by step.
set -e
# 0. sanity
nvidia-smi --query-gpu=name,memory.total --format=csv
df -h /root/autodl-tmp
# 1. fresh env (do NOT reuse the image's torch)
pip install -U uv
uv venv --python 3.12 /root/autodl-tmp/vllm-env && source /root/autodl-tmp/vllm-env/bin/activate
uv pip install vllm --torch-backend=auto
uv pip install "huggingface_hub[cli]"
# 2. weights to the DATA disk (HF mirror for China)
export HF_HOME=/root/autodl-tmp/hf HF_ENDPOINT=https://hf-mirror.com
hf download Qwen/Qwen3-30B-A3B-Instruct-2507 --local-dir /root/autodl-tmp/qwen3-30b-a3b --max-workers 8
du -sh /root/autodl-tmp/qwen3-30b-a3b   # expect ~61 GB
# 3. serve (served-model-name IDENTICAL to the API id; api-key = pick a string and give it to the cluster side)
export VLLM_API_KEY=CHANGE_ME
nohup python -m vllm.entrypoints.openai.api_server \
  --model /root/autodl-tmp/qwen3-30b-a3b --served-model-name qwen/qwen3-30b-a3b-instruct-2507 \
  --dtype bfloat16 --max-model-len 8192 --max-num-seqs 64 --gpu-memory-utilization 0.92 \
  --enable-prefix-caching --host 0.0.0.0 --port 6006 --api-key "$VLLM_API_KEY" > /root/autodl-tmp/vllm.log 2>&1 &
sleep 60; tail -5 /root/autodl-tmp/vllm.log
# 4. single-request smoke (must return an <action> and a usage block)
curl -s http://127.0.0.1:6006/v1/chat/completions -H "Authorization: Bearer $VLLM_API_KEY" -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-30b-a3b-instruct-2507","messages":[{"role":"user","content":"Answer as <action>look</action>."}],"temperature":0.4,"max_tokens":64}' | python -m json.tool | head -30
# 5. then expose port 6006 via AutoDL 自定义服务, and send the public URL + VLLM_API_KEY to the cluster side.
