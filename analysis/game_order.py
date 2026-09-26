"""Recover the actual per-slot gamefile order for (manifest, seed) by rebuilding the env (no LLM calls)."""
import sys, os, json
SEED_ROOT="/home/ymeng3/llm_agent_opd/external/SEED"; sys.path.insert(0,SEED_ROOT); sys.path.insert(0,f"{SEED_ROOT}/scripts/sft/_common")
from pipeline import build_manager
manifest, seed, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
games=[l.strip() for l in open(manifest) if l.strip()]
mgr=build_manager(game_files=games, alf_config_path=f"{SEED_ROOT}/agent_system/environments/env_package/alfworld/configs/config_tw.yaml", seed=seed, history_length=5)
obs,infos=mgr.reset({})
actual=[str((infos[i] or {}).get("extra.gamefile","")) for i in range(len(games))]
json.dump({"manifest":manifest,"seed":seed,"games_manifest":games,"games_actual":actual}, open(out,"w"), indent=0)
same=sum(1 for a,b in zip(actual,games) if a==b); print(f"seed {seed}: {same}/{len(games)} slots match manifest order; sample actual[:3] = {[a.split('/')[-3] for a in actual[:3]]}")
