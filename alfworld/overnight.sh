#!/usr/bin/env bash
# Executes hag/OVERNIGHT_TREE_2026-09-21.md (sha 85098a30d48fdfba). Unattended. Logs to overnight.log; ledger lines appended.
cd /net/scratch/ymeng3/bos_alfworld; export PATH=/net/scratch/ymeng3/llm_agent_opd/envs/seed/bin:$PATH
LED=/home/ymeng3/agent_knowledge/validation_line/METHOD_REGISTRY.md; L=overnight.log; say(){ echo "$(date '+%F %H:%M') $*" | tee -a $L; }
# STEP 0: wait for the 7 seed-2 files
while [ $(ls results/P1B_*_seed2.json 2>/dev/null | wc -l) -lt 7 ]; do sleep 120; done
say "seed-2 files complete; running pooled analysis"
if python /net/scratch/ymeng3/bos_screens/hag/p1b_pool.py >> $L 2>&1; then GATE=PASS; else GATE=FAIL; fi
{ echo "$(date '+%F %H:%M') OVERNIGHT STEP 0 — SEED-2 POOLED RESULT (unattended, rule frozen 23:00):"; cat /net/scratch/ymeng3/bos_screens/hag/p1b_pool_result.txt; } >> $LED
[ "$GATE" = "PASS" ] || { say "GATE FAIL -> STOP (nothing launched)"; echo "$(date '+%F %H:%M') OVERNIGHT: GATE FAIL -> stopped; no GPU spent beyond seed 2." >> $LED; exit 0; }
# STEP 1..3: Loop-2 pilot, one round at a time
export BOS_STATE=$PWD/closedloop_state_loop2.json BOS_PATCH_DIR=$PWD/patches_loop2 BOS_MAN_DIR=$PWD/slices/batches_loop2 BOS_TAG_PREFIX=L2 BOS_FORCE_OP=ComposePool
export BOS_SEED_POOL=$PWD/banks/loop2_seed_pool.json BOS_SKIP_F0_BLIND=1 BOS_SBATCH=run_eval_local.sbatch BOS_GUARD_USD=202 BOS_TOP_P=1.0 BOS_TOP_K=-1 BOS_LOOKAHEAD=2
mkdir -p patches_loop2 slices/batches_loop2; rm -f closedloop_state_loop2.json
for T in 1 2 3; do
  say "launching Loop-2 pilot round $T (BOS_T=$T)"; echo "$(date '+%F %H:%M') OVERNIGHT: Loop-2 pilot round $T launched (paired structured-Compose; W=naive, K=ours; tags L2_*)." >> $LED
  BOS_T=$T python closedloop.py >> closedloop_loop2.log 2>&1; rc=$?
  ev=$(python - <<PY
import json; S=json.load(open("closedloop_state_loop2.json")); x=[e for e in S["log"] if e["arm"]=="ours" and e["round"]==$T]
print(int(bool(x) and (x[0].get("hitchhikers",0)>=1 or x[0].get("salvage",False))) if x else -1)
PY
)
  say "round $T finished rc=$rc credit_event=$ev"
  summ=$(python - <<PY
import json; S=json.load(open("closedloop_state_loop2.json"))
print(" | ".join(f"{e['arm']} r{e['round']} fin={e.get('finalist')} pt={e.get('pt',0):+.2f} lcb={e.get('lcb',0):+.2f} commit={e.get('commit')} hitch={e.get('hitchhikers','')} salvage={e.get('salvage','')} gamma={ {k:round(v,1) for k,v in (e.get('gamma') or {}).items()} }" for e in S["log"] if e["round"]==$T))
PY
)
  echo "$(date '+%F %H:%M') OVERNIGHT: round $T done. $summ. credit_event=$ev" >> $LED
  [ "$rc" = "0" ] || { say "driver rc=$rc -> STOP"; echo "$(date '+%F %H:%M') OVERNIGHT: driver exited rc=$rc -> stopped (NO-AUTOFIX)." >> $LED; exit 1; }
  [ "$ev" = "1" ] || { say "no credit event in round $T -> STOP per tree"; echo "$(date '+%F %H:%M') OVERNIGHT: no credit event in round $T -> stopped per tree." >> $LED; exit 0; }
done
say "3 rounds complete with persistent credit events"; echo "$(date '+%F %H:%M') OVERNIGHT: rounds 1-3 complete, credit events in every round." >> $LED
