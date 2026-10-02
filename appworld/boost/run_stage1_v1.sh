#!/usr/bin/env bash
# CC-BOOST Stage 1 v1 (prereg sections 1 + A1/A2): FIXED once (also caches instructions), then BOOST and UNTARGET x 2 replicates in
# parallel on the thinking-ON discovery runs. Validation is re-scored afterwards with rescore.py once CC_T1_F0_val exists.
# usage (on the box): screen -dmS ccboost1 bash appworld/boost/run_stage1_v1.sh
source /root/autodl-tmp/cc/Agent-evolving-harness/tools/queue/ccenv.sh
cd $CC_REPO/appworld; R=$CC_REPO/appworld/results; OUT=boost/out/s1v1; mkdir -p $OUT/logs
export BOS_TASKS=tasks_challenge50.json BOOST_EFFORT=medium
DISC=$R/CC_F0_orig_seed1.json,$R/CC_F0_fix_seed1.json; VAL=$R/CC_F0_fix_seed1.json   # placeholder; rescored on CC_T1_F0_val later
python boost/loop.py --arm FIXED --disc $DISC --val $VAL --out $OUT > $OUT/logs/FIXED.log 2>&1
for arm in BOOST UNTARGET; do for seed in 0 1; do
  mkdir -p $OUT/rep$seed
  cp $OUT/instructions.json $OUT/rep$seed/instructions.json
  python boost/loop.py --arm $arm --disc $DISC --val $VAL --out $OUT/rep$seed --rounds 6 --P 3 --seed $seed > $OUT/logs/${arm}_rep$seed.log 2>&1 &
done; done
wait
echo "$(date) stage1 v1 done" >> $OUT/logs/DONE
