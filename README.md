# harness-evolution

Research code for **self-evolving LLM-agent harnesses with persistent-component credit** (ALFWorld main line; AppWorld and ScienceWorld as second environments).
Written for: a collaborator who wants to run the harness, evaluate patches, and reproduce the credit experiments on the UChicago cluster (or adapt the paths to another machine).

## What is here

| dir | what |
|---|---|
| `alfworld/bos_alfworld.py` | the harness. A *patch* is a small Python module that may define 5 hooks (`format_prompt`, `parse_action`, `retry_policy`, `memory_update`, `choose_fallback`) and 2 constants (`HISTORY_LENGTH`, `TEMPERATURE`). `python bos_alfworld.py eval --patch P --seed S --tag T [--n-games N] [--workers W]` runs one pass and writes `results/T_seedS.json` with per-step logs. |
| `alfworld/closedloop.py` | the closed evolution loop (propose -> validate -> paired evaluation -> credit -> inherit). Frozen preregs in `docs/preregs/`. |
| `alfworld/run_eval_local.sbatch`, `run_cmd_local.sbatch` | SLURM launchers that open an ssh tunnel to a self-hosted vLLM endpoint (see `local_llm/`) and run one pass / one command. Job lines: `TAG PATCH SEED [N_GAMES]`. |
| `alfworld/patches_*` | every patch that was ever proposed or hand-written (LLM-generated candidates, LOO variants, edits, rescues). Useful as examples of the hook API. |
| `alfworld/slices/` | game manifests (`validation_train96.txt`, `train48.txt`, `heldout48.txt`, ...). |
| `alfworld/*.sh` | unattended pipelines (Phase 2 local counterfactuals, Phase 3, failure-driven operator evolution, rubric A/B/C). They are cluster-specific but show the exact experiment order. |
| `analysis/` | scoring and probe builders: `build_probeL.py` (replay to a component's first activation, branch OFF), `p2_score.py`/`p3_score.py` (local CF vs global gamma), `phase3_offline.py` (adaptive-allocation replay), `prm_test.py` (blind promise/progress judge), `failure_map96.py`, `gen_alts.py` / `fd_*.py` (failure-driven rescue), `rubric_abc.py`. |
| `appworld/bos_appworld_v2.py` | same 5-hook API on AppWorld (ReAct code agent, per-step goal-test logging, prefix replay, hint injection). `run_aw_local.sbatch`, `pilot_*.py`. |
| `sciworld/` | same API on ScienceWorld (shelved: 4% base rate). |
| `local_llm/` | how the backbone is served: `install.sh` / `download.sh` / `serve.sh` for a rented A800 (vLLM 0.29, Qwen3-30B-A3B-Instruct-2507, bf16), `serve_qwen30b.sbatch` for the cluster. |
| `docs/preregs/` | every preregistration / frozen protocol (read `POSTMORTEM_LOOP1.md`, `CREDIT_REGIME_QUAL.md`, `LOCALCF_PHASE1_FROZEN.md` first). |

## Environment switches the harness understands

- Backbone: `BOS_BASE_URL`, `BOS_API_KEY` (OpenAI-compatible; default OpenRouter with `OPENROUTER_API_KEY` or `~/.config/openrouter/key`), `BOS_MODEL`, `BOS_TOP_P`, `BOS_TOP_K`, `BOS_MAX_TOKENS` (default 512; see the truncation finding below), `BOS_PROVIDER`.
- Games: `BOS_MANIFEST` (file of gamefile paths), `--n-games`, `--seed` (the env permutes games per seed; `games_actual` in the result records the real order).
- Replay / probes: `BOS_REPLAY` = json `{gamefile: [actions...]}` replayed without LLM calls (deterministic env); `BOS_REPLAY_ONLY=1` ends an episode when the prefix is exhausted; `BOS_HINTS` = json `{gamefile: text}` exposed to patches as `state["_hint"]`; `BOS_LOG_RAW=1` logs the last 300 chars of each raw reply.
- Spend guard: `BOS_GUARD_USD` (hard cap on API spend for a job).

## Running one evaluation (cluster)

```bash
# 1. serve the model somewhere (local_llm/serve.sh on the GPU box; write "host port" to local_llm/host)
# 2. one pass of a patch on 48 games, seed 1, 24 workers
printf "MYTAG patches_phased/hit40_A_ctrl/hit40_A_ctrl_21_adaptive_action_guide.py 1 48\n" > jobs.txt
sbatch --array=0-0 --export=ALL,JOBS_FILE=$PWD/jobs.txt,BOS_MANIFEST=$PWD/slices/train48.txt,BOS_HOST_FILE=/path/to/host,BOS_TOP_P=1.0,BOS_TOP_K=-1,BOS_WORKERS=24 run_eval_local.sbatch
# result: results/MYTAG_seed1.json  (won[], steps[], traj[] with per-step action/obs/admissible/hook flags)
```

The ALFWorld env comes from the SEED repo (`/home/ymeng3/llm_agent_opd/external/SEED`, `pipeline.build_manager`); paths are hard-coded at the top of `bos_alfworld.py` and in the sbatch files. Change `SEED_ROOT`, `OUT`, the conda/venv `PATH` lines, and the host file to your setup.

## Findings that shape the code (Sept 2026, local Qwen3-30B-A3B backbone)

- Paired evaluation (same games, same seed) has ~0.4x the variance of independent evaluation; all component credit uses it.
- Local counterfactuals (replay to first activation, branch OFF) rank fallback/retry components correctly (fallback 3/3, retry 6/7 across seeds) but not history/format/temperature components; those need full paired LOO.
- Adaptive across-component allocation buys ~20% compute at equal decision accuracy (`analysis/phase3_offline.py`).
- A blind LLM promise/progress judge (AgentPRM-style) is not a usable credit signal (unstable across game batches, cannot see delayed harm from fallbacks) — kept only as an observation.
- The bare harness truncates 16-36% of replies at `max_tokens=512` (long `<think>`, no `<action>`), producing an inadmissible action and a dead loop; harnesses with a fallback/parse hook convert those steps into admissible actions, which is a large part of what "fallback credit" measures.
- Rescue tests: injecting a strategy from a failure state rescues some episodes (8/29 for ctrl21), but turning those strategies into unconditional rules hurt on the full game set; the per-episode failure map is in `analysis/failure_map96.py`.

## Not in the repo

Results, SLURM logs, probe replays, the method ledger and any keys. Ask for `results/` if you need the raw per-episode logs.
