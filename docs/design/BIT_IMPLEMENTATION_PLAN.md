# BIT implementation plan (Boosted Intervention Trees + hindsight self-proposer), round 1

The design is in BOOSTED_INTERVENTION_TREES_v0.md. Paths are relative to the repo root; `appworld/...` is the harness dir.

Local data dir `CCD` = C:\Users\Owner\AppData\Local\Temp\claude\C--Projects-Cleanup-Archives-2026-08-27-Local-Latex-Files-Local-Latex-Files-Agent-evolving-harness\57e9c937-6acb-4624-9f6e-81989b534107\scratchpad\ccdata.
It holds `CC_H1_F0_disc_seed{1,2}.json`, `CC_H1origP_disc_seed{1,2}.json` (= H2 base), val runs, and `instructions_all100.json` (tid -> instruction).

## Findings that shape the design
1. **What the logs contain vs. how hooks are called.**
   - `traj[k]["code"]` is the executed code, i.e. after post_parse/pre_complete rewrites.
   - `out` is truncated to 200 chars.
   - `no_exec`/empty-code steps never reach post_exec online, but pre_call does run for them.
   - Replayed steps reach post_exec only.
   - `state["_step"]` is set only at live steps.
   - The offline simulator must reproduce these rules exactly.
2. **Bug: the task text is lost after a replay.** At the first live step after a replay, `prompt` is the last output, not the task, so `ANSWER_CHECK_H1`/`R3_H2` see `state["_task"]==""`. Fix (Unit A): the harness sets `state["_instr"]`.
3. **block_once needs a conditioned replay.** The causal contrast is "logged cell k executed" vs "logged cell k blocked (note shown)". Unit A adds a replay item that shows one code text and executes another.
4. **Reuse existing code.** `branch_build`/`BRANCH_NOTE` (note-kind branches), `edits.structure_check`, and `loop_pw.make_pairs` plus its gain (copy them, don't import loop_pw). Statistics helpers come from `branch_readout`/`rubric_check`.

## Key decision: the proposer writes a constrained spec; a compiler emits the v3 patch
The proposer outputs only `NOTE`, a pure `def detect(view)`, and a kind (`note` or `block_once`). A fixed template compiles this into a v3 patch.

This gives:
- identical behaviour offline and online;
- a detector that is prefix-only by construction;
- robust validation.

The cost: no run-time variable inspection (the detector reads the pending code text instead).

### Interface 1: `view`, the only thing `detect` sees
```python
view = {"task": str,            # instruction (state["_instr"])
        "step": int,            # harness step index about to run (counts no_exec steps)
        "max_steps": 30,
        "cells": [{"code": str, "out": str, "error": bool}, ...],  # executed cells so far, in order (no_exec skipped); out <= 200 chars
        "pending": str | None}  # block_once: code about to execute; note: None
# detect(view) -> falsy (no fire) | True (fire with NOTE) | non-empty str (fire with this note, <= 600 chars)
```
### Interface 2: `spec`, one candidate
```python
{"name": snake_case<=40, "kind": "note"|"block_once", "cls": "control_flow"|"task_knowledge",
 "hypothesis": str, "note": str, "detect_src": "def detect(view):\n ...",   # imports/helpers nested inside detect
 "origin": {"case_id": str|None, "run": str|None}}
```
### Interface 3: compiled patch skeleton (one edit `eK` per spec, in priority order)
**`eK_post_exec`**
- Append `{"code", "out": out[:200], "error": out.startswith("Execution failed")}` to `state["_cc_hist_eK"]`.

**`eK_pre_call`** (kind `note`)
- Return the prompt unchanged if `state["_cc_done_eK"]` is set.
- Build the view:
  - `task = state.get("_instr")`, falling back to parsing "Task:" at step 0;
  - `step = state.get("_step")`.
- Call the nested `_detect` inside try/except.
- On a fire:
  - set the done flag;
  - append `"\n\n[harness note] " + note`;
  - skip the append if `state["_cc_noted"] == step`, so at most one note per step;
  - append `{"eid","step","kind","note"}` to `state["_cc_fired"]`.

**`eK_post_parse`** (kind `block_once`)
- Same as the note case, with `pending=code`.
- Never block when `step >= max_steps-1`.
- On a fire, return `"print(" + repr("[harness note] Your cell was NOT executed. " + note) + ")"`.

All literals are emitted via `repr`. The patch must pass `edits.structure_check`: only top-level `<id>_<point>` functions, everything else nested. Patch imports are limited to re/json/math/random/collections/itertools/string, inside functions. The names open/exec/eval/getattr/setattr/globals/... are forbidden. Hooks always return a str.

### Interface 4: replay item (harness change)
- A `BOS_REPLAY` list element may be a `str` (as today) or `{"exec": str, "shown": str}`.
- The harness executes `exec`.
- The assistant history shows `` "```python\n" + shown + "\n```" ``.
- The trajectory logs `code=exec` and `shown=shown[:300]`.

## Work units
### Unit A: harness changes and common helpers (land first)
**`appworld/bos_appworld_v3.py`**
- In `play()`, just before `for step in range(MAX_STEPS)`, set `state["_instr"] = world.task.instruction`.
- In the replay branch, support the dict item:
  - use `exec` for `world.execute`, `done_codes`, `post_exec` and the trajectory;
  - use `shown` in `hist`.
- Change nothing else.

**New `appworld/boost/bit_common.py`**
```python
def load_episodes(paths, instr) -> list[dict]
#  ep = {"eid": f"{tag}_s{seed}:{tid}", "task","tag","seed","won":bool,"G":float|None,"instr":str,"harness_h1":bool,
#        "crashed":bool,"has_replay":bool,"steps":[{"k","code","out","err","no_exec","replayed","resp"}]}
def make_pairs(eps) -> (I, J, T)                       # same-task (winner, loser) index pairs (copy of loop_pw.make_pairs)
def pair_gain(phi, I, J, lam=1.0) -> (gain, n_discordant, direction)
#  d = phi[I]-phi[J]; g=-0.5, h=0.25; gain=(sum g*d)^2/(2*(sum h*d^2+lam)); direction=sign(sum(phi[J]-phi[I])) (+1 = fires on losers)
def within_ic(phi, eps, B=2000) -> (ic, lo90, hi90)     # mean over mixed tasks of mean phi|lost - mean phi|won; task bootstrap
def beta_stats(a, b) -> {"p","var","g","h","priority"} # Beta(1+a,1+b); g=p-1, h=p(1-p), priority=|g|*h*var
def signflip(x, B=20000, seed=0); def boot(x, B=5000, seed=0)
```
**Verify**
- `bos_appworld_v3.py` parses.
- `load_episodes` on `CCD/CC_H1_F0_disc_seed1.json` gives 50 episodes, 42 of them won.
- `beta_stats(1,1)["priority"] ≈ 0.0104`.

### Unit B: memory tree and residual report (`appworld/boost/bit_tree.py`)
**CLI:**
```
--runs A,B --instr ... --out bit/<R>/tree.json [--top 20] [--max-per-task 2] [--exclude tids] [--branch-meta ...]
```
**Trie construction**
- One trie per task, keyed on `(" ".join(code.split()), out[:200])` per logged step.
- Crashed episodes are excluded.
- Each node stores `n_win`/`n_loss` over descendant episodes, the eids, and its children.

**Cases**
- There is one case per lost episode. Its won sibling is the same-task won episode with the longest common prefix, or null if none exists.
- `fork_depth` is the length of the common prefix.
- Priority is the `beta_stats` priority of the deepest shared node, or root priority × 0.5 if there is no sibling.
- Sort cases descending and keep the top N, at most `--max-per-task` per task.

**`tree.json` schema**
```json
{"runs":[...], "episodes":{eid:{"task","tag","seed","won","G","n_steps"}},
 "tasks":{tid:{"n","wins","mixed","p","g","h","var","priority","eids"}},
 "nodes":[{"node":"tid/<depth>/<hash8>","task","depth","n_win","n_loss","p","g","h","var","priority","eids_won","eids_lost"}],
 "cases":[{"case_id":"c01","task","lost":eid,"won":eid|null,"fork_depth":int,"priority":float}]}
```
**Verify**
- On H1 disc s1+s2, root wins equal the total wins and every loss is in the cases.
- On H2 disc there are 15 losses.

### Unit C: spec parser, compiler, offline simulator (`appworld/boost/bit_rubric.py`)
Refs in `appworld/boost/bit_refs/`:
- `D10_ref.json`: block_once; fires when the pending code calls `apis.supervisor.complete_task` with a non-None answer and the task has no question cue. Use the R3_H2 cue rule verbatim.
- `null_note.json`: fires at step 5.

```python
def parse_proposals(text) -> list[dict]       # sections "NAME:", KIND/CLASS/HYPOTHESIS fields + section's last ```python block; NOTE via ast
def validate_spec(spec) -> None                # ValueError on: enums; note 20..600 chars; detect_src ast rules (allowed imports, forbidden names,
                                               #   no dunder), exactly one top-level def detect(view), only NOTE assignment besides
def compile_patch(specs, max_steps=30) -> str  # skeleton above; e1..eN; runs edits.structure_check before returning
def simulate(patch_src, eps, stop_at_first=True, timeout_s=120) -> {eid: {"fires":[{"eid","k","kind","note","pending"}], "hook_errors":int}}
```
**Simulator rules**
- Each episode starts with `state={"_instr": instr}`.
- For each step k:
  - Replayed step: post_exec only.
  - Otherwise: set `_step=k`, `_tid`, `_replay_len=0`, then run `pre_call(prompt_proxy)`.
    - If the step is `no_exec`, stop here (continue to the next step).
    - Else run `post_parse(code)`; then `pre_complete` if `"complete_task" in code`; then `post_exec(logged code, logged out)`.
- Fires are read from `state["_cc_fired"]`.
- Generic patches without `_cc_fired` count a fire whenever the prompt or code changed (an upper bound).
- Stop evaluating an edit after its first fire.
- Run each simulation in a multiprocessing worker with a wall timeout, so a looping detector is rejected.

**Verify**
- `compile_patch([D10_ref])` passes `structure_check`.
- `simulate` on H1 disc s1 fires on e7f15ba, 4242c97, d9987f6, 77bcb81, b6d1f70 (5/8 losses) and on 0/42 wins.
- `R3_H2.py` on H2 disc gives roughly e1 3/15 losses, 0/85 wins.
- `while True` is killed.

### Unit D: hindsight self-proposer (`appworld/boost/bit_propose.py`)
**CLI**
```
--tree ... --runs ... --instr ... --out cands_<run>.jsonl --run-id P1 [--n-cases 20 --k-per-case 2 --no-sibling --outcome-detail {won,G} --failed-tests path --workers 6 --max-tokens 16000]
```
Calls are made with `proposer.chat` (`BOOST_MOCK=1` for offline runs).

**Prompt:** one call per case. The user turn contains:
1. **Harness description:** AppWorld, a 30-step budget, code cells, `complete_task`.
2. **The view schema,** with the hard rule spelled out: the detector cannot see reasoning, outputs beyond 200 chars, the task id, or anything that happens later.
3. **Kind semantics:**
   - `note`: appended to the next prompt, once.
   - `block_once`: the pending cell is not executed and the note is shown; the second attempt goes through.
4. **The case:**
   - task instruction, outcome, steps used, `G` (explained);
   - the common prefix, collapsed;
   - both runs, step by step: `[step k] code (<=800) -> out (<=200)`, plus `[reasoning tail, NOT visible to the detector] resp[-400:]`;
   - optionally, the failed-test names.
5. **What to write:** first, the decisive step and mechanism in at most 3 sentences. Then k candidates that fire at or before the decisive step of the failed run and not on the won run. Candidates must be general: no task-specific names, ids or long literals. The note is factual, actionable, and must not contain the solution.
6. **Output format,** per candidate: `NAME:`, `KIND:`, `CLASS:`, `HYPOTHESIS:`, then a python block containing `NOTE = "..."` and `def detect(view):`.
7. **One format example** on an unrelated mechanism: the same failing call 3 times in a row → note. **Never a D10-like example.**

**Per candidate**
1. Run `validate_spec`, then `compile_patch`.
2. Self-check by running `simulate` on the case's lost and won episodes. Required: it fires on the lost episode, and does not fire on the won episode if one exists.
3. If a step fails, retry at most twice, passing back the exact reason.
4. If the reply is empty with `finish=length`, retry once at effort medium.

**JSONL line:**
```json
{"cid":"<run>_<case>_<j>","run","case_id","task","spec","valid","why","self_check":{"fires_lost","k_lost","fires_won"},"patch_path","usage","raw"}
```

### Unit E: screening (`appworld/boost/bit_screen.py`)
**Inputs:** base discovery episodes, not crashed and with no replayed steps. φ_e = 1 if the candidate fired anywhere in episode e.

**Per candidate, compute:**
- `n_fire`, `s`, `P(fire|lost)`, `P(fire|won)`;
- `within_ic` with its CI;
- `gain_within` = `pair_gain` (set to 0 if `dir <= 0`);
- `gain_raw` = `(Σ_fired g)^2/(Σ h + λ)`, with g, h taken from the trie node at the fire depth;
- steps left at the fire (median);
- hook errors;
- rates on tasks that were not shown to the proposer;
- memorization flags: a ≥3-word string or ≥3-digit number copied from the shown cases, or a candidate that fires only on its own case's task.

**Dedupe:** if the Jaccard similarity of two candidates' fired-eid sets is ≥ 0.8, keep the one with the higher `gain_within`.

**Keep:** the top `k_within` by `gain_within`, plus the top `k_raw` by `gain_raw` among those with `P(fire|won) <= max_won_fire`. Reference specs are scored with `"ref": true` and never kept.

**Output:** `screen.json` with `{"params","candidates":[...],"kept":[cid...]}`.

**Verify:**
- `D10_ref` has the top `gain_raw` and a positive IC.
- An "always fires at step 0" candidate gets `gain_within = 0`.
- A "fires on '?'" candidate has `dir < 0`.

### Unit F: branch-at-fire build, readout, admission, validation arm (`appworld/boost/bit_branch.py`)
**`build`**
- Base logs must be `harness_h1`.
- For each kept candidate and each firing (eid, k), grouped by origin seed:
  - **note:** `replay = codes[:k]` for both arms. The cand arm is `BRANCH_NOTE` with `BOS_HINTS = {tid: note}`; the none arm is `--patch none`.
  - **block_once:**
    - `replay_none = codes[:k+1]`;
    - `replay_cand = codes[:k] + [{"exec": print(<block note>), "shown": codes[k]}]`;
    - both arms run with `--patch none`.
- Each `<cid>_o<seed>/` directory holds `tasks.json`, `replay_none.json`, `replay_cand.json`, `[hints_cand.json]`, and `meta.json`.
- Also write `manifest.json` and `jobs.txt` (qsub lines, tags `CC_BIT_<R>_...`).
- Keep the first firing per (tid, seed).

**`readout`**
- Per state: `d = cand - none` on won, and also on G.
- Take the task mean, then report `ā`, a bootstrap 90% CI, sign-flip p, Holm p across the K candidates, a logged won/lost split, and a manipulation check.
- `τ = s·ā`.
- Admission rule: lo90 > 0, mean > 0, n_tasks >= 3.

**`valarm`**
- Compile the admitted specs into a single patch.
- Print the qsub lines for val seeds 1 and 2, and the `multi_metric_readout` command.

### Unit G: D10 rediscovery benchmark, offline end-to-end test, round script
**Gold set** (frozen before any proposer run): the lost episodes in `CC_H1_F0_disc_seed{1,2}` whose final executed cell calls `complete_task` with a non-None answer on a task with no question cue. Seed 1 should give {e7f15ba, 4242c97, d9987f6, 77bcb81, b6d1f70}.

**Rediscovery test.** A candidate rediscovers D10 iff all of the following hold:
- recall >= 0.6;
- precision >= 0.5;
- at most 2 won episodes fired;
- the firing step is the final `complete_task` step for block_once, or at most 2 steps before it for note.

**Report:**
- exposure: whether the proposer was shown any gold case;
- rediscovery at three levels: any valid candidate / kept by screening / top-1;
- ablations: `--outcome-detail won`, `--no-sibling`, `--failed-tests`.

`appworld/boost/test_bit_offline.py` runs B → D (mock) → E → F build on the CCD H1 disc files.

## Order
1. **Wave 1, in parallel:** A, B, C.
2. **Wave 2, in parallel:** D, E, F, G.
3. **Integration:**
   1. Sync to the server.
   2. Run the A smoke test (block-item replay on e7f15ba) and the C fidelity smoke test.
   3. Write prereg A23 (gold set, rediscovery criteria, keep/admit rules) before the first proposer job.
   4. Run the benchmark round on H1 disc.
   5. Run the real round on the H2 disc base.

## Risks
1. **Leakage or detectors that can only fire after the fact.** Mitigations: memorization flags, rates on unshown tasks, steps-left at fire. The real gate is branch-at-fire.
2. **Offline fidelity.** The simulation is exact only for template patches. Generic patches give upper bounds.
3. **Small samples.** There are about 10 mixed tasks over 2 seeds, which is why `gain_raw` is kept. Consider a third discovery seed.
4. **Proposer cost with thinking on.** About 60–120 calls; cap concurrency at 6; run through qsub. Never enable MTP.
5. **Admission power.** The minimum sign-flip p is 2^-n, so admission gates on the bootstrap lower bound. The validation arm is the final guard.
6. **Patched bases.** Avoid them in round 1 by using unpatched bases.
