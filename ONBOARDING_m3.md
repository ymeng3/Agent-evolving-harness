# Onboarding: the shared GPU box (AppWorld + Qwen3.8-27B)

Written for: a collaborator who wants to run the AppWorld experiments without setting anything up.

## Login

```
ssh -p 39563 root@connect.nma1.seetacloud.com
```

Everything lives under `/root/autodl-tmp/`:

| path | what |
|---|---|
| `Agent-evolving-harness/` | this repository (copy of GitHub `ymeng3/Agent-evolving-harness`) |
| `appworld_repo/`, `appworld_root/` | AppWorld source and its data (`APPWORLD_ROOT`) |
| `aw-env/` | Python venv with AppWorld and the harness dependencies |
| `qwen3.8-27b/`, `vllm-env/`, `serve27.sh` | the model, the vLLM env, and the serve script |
| `vllm_api_key` | the API key the local server expects |

## The model server (shared — do not stop it)

A vLLM server serves `qwen/qwen3.8-27b` on `http://127.0.0.1:6006/v1` (OpenAI-compatible, bf16, 32k context, tool calling on).
Other experiments also use this server through ssh tunnels, so:

- do not kill or restart the `vllm.entrypoints.openai.api_server` process;
- do not load another model on the GPU (the 27B uses ~76 GB of the 80 GB);
- if it is ever down, restart it with `/root/autodl-tmp/restart27.sh` and wait ~4 min (`tail -f /root/autodl-tmp/vllm27.log`).

Quick check:

```
curl -s -H "Authorization: Bearer $(cat /root/autodl-tmp/vllm_api_key)" http://127.0.0.1:6006/v1/models | head -c 200
```

## Run one AppWorld evaluation

```
source /root/autodl-tmp/env.sh        # activates the venv and exports every BOS_* / APPWORLD_ROOT variable
cd /root/autodl-tmp/Agent-evolving-harness/appworld
export BOS_TASKS=$PWD/tasks_challenge50.json      # or tasks50.json (normal split), tasks_challenge_val50.json
python bos_appworld_v3.py eval --patch none --seed 1 --tag MY_F0 --n-games 3 --workers 3
```

`env.sh` sets: `APPWORLD_ROOT`, `BOS_OUT` (where results/ go), `BOS_ALF_OUT`, `BOS_TMPDIR`, `BOS_AW_INSTR` (the ReAct
instruction template), `BOS_BASE_URL`/`BOS_API_KEY` (the local server), `BOS_MODEL=qwen/qwen3.8-27b`, `BOS_THINK_OFF=1`,
`BOS_TIMEOUT=240`, `BOS_TOP_P=1.0`, `BOS_TOP_K=-1`, `BOS_AW_STEPS=30`. Override any of them after sourcing.

Results land in `results/MY_F0_seed1.json` (per task: `won`, `G` = fraction of goal checks passed, `traj` with every cell,
its output, goal-check counts and hook flags). Bare 27B on the 50 challenge tasks scores 18/50 and 19/50 (seeds 1, 2), 30 steps.
Use 8-12 workers for a full pass (~25-40 min); more than ~16 on one box makes the server queue.

## Patches (what you evolve)

Two formats are accepted by `bos_appworld_v3.py`:

1. Legacy 5-hook module: any of `format_prompt`, `parse_action`, `retry_policy`, `memory_update`, `choose_fallback`,
   plus `HISTORY_LENGTH`, `TEMPERATURE`, `SETUP_CODE` (sandbox code run once before step 0). Examples in `patches/` and
   `patches_phase1/`.
2. Two-layer edits: `EDITS = [{"id": "e1", "capability": ..., "impl": ..., "trigger": ..., "depends": [...]}, ...]` with functions
   `e1_setup() -> code`, `e1_pre_call(prompt, state)`, `e1_post_parse(code, state)`, `e1_post_exec(code, out, state)`,
   `e1_pre_complete(code, state)`. `BOS_EDITS_OFF=e2` disables an edit and everything that depends on it (this is how
   component credit is measured). Examples in `patches_v3/`.

Allowed imports inside patches: re, json, math, random, collections, itertools, string. No file or network access.

## Data splits (do not mix them)

- `tasks_challenge50.json` — Discovery (used for failure analysis and proposals).
- `tasks_challenge_val50.json` — Validation (new task families; bare 27B 14/50, 10/50).
- `tasks_challenge_TESTSEALED50.json` — sealed test. Do not run it until a method is frozen.

## Useful scripts

- `phase2/dryrun.py` — replay logged trajectories through a patch's edits offline and count where they would fire (free; use it
  before spending a pass).
- `analysis/` — scoring and diagnostics from the ALFWorld/AppWorld lines; `docs/preregs/` — every preregistration.

Questions: justin.mengj@gmail.com
