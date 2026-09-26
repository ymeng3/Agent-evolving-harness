#!/usr/bin/env bash
source /root/autodl-tmp/vllm-env/bin/activate
export HF_HUB_OFFLINE=1 VLLM_LOGGING_LEVEL=INFO VLLM_USE_FLASHINFER_SAMPLER=0
exec python -m vllm.entrypoints.openai.api_server   --model /root/autodl-tmp/qwen3-30b-a3b --served-model-name qwen/qwen3-30b-a3b-instruct-2507   --dtype bfloat16 --max-model-len 16384 --max-num-seqs 96 --gpu-memory-utilization 0.92   --enable-prefix-caching --host 127.0.0.1 --port 6006 --api-key ${VLLM_API_KEY:?set VLLM_API_KEY}
