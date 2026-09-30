#!/bin/bash
# wait for m3's 27B, then a 2-task smoke with the FIXED harness (expects api_errors ~0), then register
cd /net/scratch/ymeng3/bos_appworld; KEY=$(cat /net/scratch/ymeng3/local_llm/vllm_api_key); L=night/phase1.log
until ssh -i ~/.ssh/autodl_key -o ConnectTimeout=20 -o StrictHostKeyChecking=no -p 39563 root@connect.nma1.seetacloud.com "curl -s -m 5 -H 'Authorization: Bearer $KEY' http://127.0.0.1:6006/v1/models" 2>/dev/null | grep -q "qwen3.8-27b"; do sleep 60; done; echo "$(date) m3 27B up" >> $L
printf "M3SMOKE_F0 none 1 3\n" > night/jobs_m3smoke.txt
J=$(sbatch --parsable --job-name=aw-m3 --array=0-0 --time=00:40:00 --export=ALL,JOBS_FILE=$PWD/night/jobs_m3smoke.txt,BOS_TASKS=$PWD/tasks_challenge50.json,BOS_AW_STEPS=30,BOS_MODEL=qwen/qwen3.8-27b,BOS_THINK_OFF=1,BOS_TIMEOUT=900,BOS_HOST_FILE=/net/scratch/ymeng3/local_llm/host3,BOS_GUARD_USD=202,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=3 run_aw_local.sbatch)
while squeue -h -j $J | grep -q .; do sleep 30; done; sleep 5
python3 -c "
import json;d=json.load(open('/net/scratch/ymeng3/bos_appworld/results/M3SMOKE_F0_seed1.json'));st=[s for tr in d['traj'] for s in tr];print('m3 smoke: won',sum(d['won']),'api_errors',d['api_errors'],'steps',len(st),'retried steps',sum(1 for s in st if s.get('api_retries')))" >> $L 2>&1
echo "$(date '+%F %H:%M') THIRD BOX m3 (nma1:39563, A800 PCIe, 125G) deployed by rsync from m1; host3 file added; smoke: $(tail -1 $L)" >> ~/agent_knowledge/validation_line/METHOD_REGISTRY.md
