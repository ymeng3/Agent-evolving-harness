#!/usr/bin/env bash
# CC-BOOST Stage 1 v1, iteration 2 (prereg A3 + A6): BOOST and UNTARGET, seed 0 only, on the 4 thinking-ON discovery passes.
# Validation is re-scored afterwards with rescore.py on CC_T1_F0_val seeds 1-4.
# usage (on the box): screen -dmS ccboost2 bash appworld/boost/run_stage1_v1_it2.sh
source /root/autodl-tmp/cc/Agent-evolving-harness/tools/queue/ccenv.sh
cd $CC_REPO/appworld; R=$CC_REPO/appworld/results; OUT=boost/out/s1v1_it2; mkdir -p $OUT/logs $OUT/rep0
export BOS_TASKS=tasks_challenge50.json BOOST_EFFORT=medium
DISC=$R/CC_F0_orig_seed1.json,$R/CC_F0_fix_seed1.json,$R/CC_T1_F0_disc_seed2.json,$R/CC_T1_F0_disc_seed3.json; VAL=$R/CC_T1_F0_val_seed1.json
cp boost/out/s1v1/instructions.json $OUT/rep0/instructions.json
for arm in BOOST UNTARGET; do
  python boost/loop.py --arm $arm --disc $DISC --val $VAL --out $OUT/rep0 --rounds 6 --P 3 --seed 0 > $OUT/logs/${arm}_rep0.log 2>&1 &
done
wait
echo "$(date) stage1 v1 iteration 2 done" >> $OUT/logs/DONE
