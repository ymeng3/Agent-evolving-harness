#!/usr/bin/env bash
cd /net/scratch/ymeng3/bos_alfworld; export PATH=/net/scratch/ymeng3/llm_agent_opd/envs/seed/bin:$PATH
LED=/home/ymeng3/agent_knowledge/validation_line/METHOD_REGISTRY.md; JOBS=$(cat /net/scratch/ymeng3/local_llm/overnight2_jobs)
while true; do q=0; for j in $JOBS; do squeue -h -j $j 2>/dev/null | grep -q . && q=1; done; [ $q -eq 0 ] && break; sleep 180; done
echo "$(date) all jobs finished" >> overnight2.log
python /net/scratch/ymeng3/bos_screens/hag/overnight2_analysis.py >> overnight2.log 2>&1
{ echo "$(date '+%F %H:%M') OVERNIGHT-2 RESULTS (unattended; prereg R6_MECHANISM_PREREG.md sha d3f3059f39b50f51):"; cat /net/scratch/ymeng3/bos_screens/hag/overnight2_result.txt; } >> $LED
sleep 60
ssh -i $HOME/.ssh/autodl_key -o StrictHostKeyChecking=no -o ConnectTimeout=20 -p 14023 root@connect.bjb1.seetacloud.com 'pkill -f "api_serve[r]"; sleep 3; shutdown' >> overnight2.log 2>&1
sleep 20; if timeout 10 nc -z connect.bjb1.seetacloud.com 14023 2>/dev/null; then echo "$(date) WARNING: instance still reachable" >> overnight2.log; echo "$(date '+%F %H:%M') OVERNIGHT-2: shutdown command sent but port still open — check console." >> $LED; else echo "$(date) instance shut down" >> overnight2.log; echo "$(date '+%F %H:%M') OVERNIGHT-2: AutoDL instance SHUT DOWN after all analyses (weights/env on data disk)." >> $LED; fi
