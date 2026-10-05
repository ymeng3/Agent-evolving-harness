# Gaia2 (ARE 1.2.0) adapter for the BIT pipeline: implementation plan (planner, 2026-10-06)

The ARE source is copied locally at scratchpad/are_src/are/simulation/. On the server ARE lives in /root/autodl-tmp/cc/are-env (python 3.12), and the data in /root/autodl-tmp/cc/gaia2/data/<config>/validation-00000-of-00001.parquet, with configs execution, search, adaptability, time, ambiguity, mini and demo. Each row has id, scenario_id, split, and data (the scenario JSON).

## 0. ARE facts the design rests on
- **Clock.** The clock is wall-clock based and non-deterministic. TimeManager (time_manager.py) returns real elapsed time plus an offset. Environment.start() runs _time_based_loop in a thread with time.sleep(1). **Decision:** never start that thread. We drive env.tick() ourselves under a virtual clock.
- **Validation is online.** preprocess_scenario (scenarios/scenario_imported_from_json/utils.py) does three things: an oracle run (oracle_run_event_log), building a GraphPerEventJudge, and scenario.initialize_turns(trigger_condition=judge.trigger_condition, validation_fn=judge.validate, is_end_of_turn_event=is_send_message_to_user).
  - In multi-turn scenarios, a ConditionCheckEvent ("condition_turn_i") calls the **LLM judge inside env.tick()** once the count of AUI send_message_to_user reaches i. On rejection it calls env.stop().
  - The last turn is judged by scenario.validate(env), which goes through BaseJudge.validate to validate_current_turn.
  - Consequence: **the judge must be cached** so that replays reproduce the verdicts.
- **Judge** (validation/judge.py):
  - Agent events pass EnvAgentEventFilter, so only AGENT **WRITE** events that did not fail count. Reads are free.
  - preliminary_checks: the Counter of write-tool names must equal the oracle's; send_message_to_user may be the oracle count or the oracle count + 1.
  - Then each oracle event is matched in topological order: hard checkers, LLM soft checkers ([[Success]]/[[Failure]]), causality, and timing (pre 10 s / post 25 s).
  - Rationale is str(judgment.failure), e.g. ToolCallCountsFailure "Agent and oracle counters do not match ...", or OracleEventMatchingFailure, which includes the oracle args.
- **Judge engine interface:** engine(messages, additional_trace_tags=[...]) -> (text, metadata). It is passed via GraphPerEventJudgeConfig(engine=...) -> AgentEventJudgeConfig -> MildToolJudgeConfig (event_judge.py:85).
- **Non-determinism sources:**
  - App.set_seed uses hash(f"{seed}_{name}") (apps/app.py:65), so **PYTHONHASHSEED=0** is required.
  - uuid.uuid4() is used for event ids (types.py:1446) and in app dataclass defaults.
  - time.time() is called in apps.
  - datetime.now() appears as a default argument (email_client.py:347, messaging.py:563).
- **Built-in replay is not usable for branching.** replay.replay_logs replays only agent ActionLogs with is_replaying=True (no notifications or validators) and calls time_manager.reset per log. **We implement our own replay:** re-execute the logged cells under the same clock schedule.
- **User and notifications:**
  - The USER event AgentUserInterface.send_message_to_agent goes to notification_system.message_queue as USER_MESSAGE.
  - ENV notifications go through VerboseNotificationSystem(VerbosityLevel.MEDIUM).
  - env.stop() posts ENVIRONMENT_STOP.
  - SystemApp.wait_for_notification(timeout) jumps time and ticks.
- **Hidden tools.** Hide the same tools the default agent hides: AUI get_last_message_from_user, get_last_message_from_agent, get_last_unread_messages, get_all_messages. Also set aui.wait_for_user_response = False.
- **Durations:** MAX_SCENARIO_DURATION = 1800, MAX_TIME_SCENARIO_DURATION = 420 (scenarios/config.py, get_scenario_duration).
- **Loading:** JsonScenarioImporter().import_from_json_to_benchmark(json_str, apps_to_skip=["SandboxLocalFileSystem"], load_completed_events=False) returns (scenario, completed, _). extract_tasks(scenario) (validation/utils/scenario_utils.py) gives the user message per turn.
- **What BIT tools assume:**
  - load_episodes keys: games, won, traj, crashed, G, tag, seed, harness_h1; per step: step, code, out, replayed, no_exec, resp.
  - err = out.startswith("Execution failed").
  - bit_rubric hard-codes "complete_task" as the pre_complete marker.
  - bit_branch hard-codes `python bos_appworld_v3.py` and requires harness_h1.
  - bos_appworld_v3.py cannot be imported in are-env (it reads BOS_TASKS and the instructions file at import time), so Gaia2 needs its own copy of load_v3.

## 1. Decisions
1. **Action format: one python code cell per step**, calling tool functions named exactly like ARE tools, App__tool(arg=...).
   - The block_once patch (print(repr(note))) and bit_branch block items work unchanged.
   - Detectors match on code text.
   - Tool names equal the names in the judge rationale.
   - Loops save steps.
2. **Deterministic synchronous simulation.**
   - VirtualTimeManager replaces environment.TimeManager: a pure counter, with pause/resume as no-ops and add_offset advancing it.
   - The env thread is never started; the harness calls env.tick().
   - Every step (live, no_exec or replayed) advances the clock by exactly G2_GEN_SECONDS (default 1.0) before executing.
   - Free re-asks and idle waits cost no steps.
   - The clock trajectory is therefore a function of the code sequence alone.
3. **Randomness per episode.**
   - Re-exec with PYTHONHASHSEED=0.
   - Replace the module attribute `uuid` in loaded are.simulation.* modules by a shim whose uuid4() draws from random.Random(sha256(f"{tid}|{seed}")). Do not patch uuid.uuid4 globally.
   - Replace the module attribute `time` in are.simulation.apps.* by a shim whose .time() returns the virtual clock.
4. **Judge.** The judge is the same local Qwen3.8-27B through CachedJudgeEngine: thinking off, temperature 0, <think> stripped, persistent on-disk cache keyed by prompt hash. This is a stated limitation: the official judge is Llama-3.3-70B.
5. **Scores.**
   - won = scenario.validate(env).success.
   - G = multiset overlap of write-tool names over all turns, sum_t min(a_t, o_t) / max(sum a_t, sum o_t). It needs no LLM.
   - rationale = the official text. If it starts with "Validation called at turn", also store rationale_diag = judge.validate_current_turn(env).rationale.
   - Privileged text for the proposer: the per-tool count lines by default; oracle args only as an ablation.
6. **Episode end:** turns_done >= nb_turns, or env STOPPED/FAILED, or time_up, or the G2_STEPS budget (default 40) is used up.

## 2. Shared interfaces
**Layout (new dir gaia2/ next to appworld/):**
- g2_env.py (U1)
- g2_exec.py (U2)
- g2_judge.py (U3)
- g2_hooks.py and bos_gaia2.py (U4)
- g2_splits.py (U5)
- g2_failed_checks.py, bit_refs/*.json, test_g2_offline.py, plus edits to appworld/boost/bit_*.py (U6)
- g2_oracle_replay.py (U7)

**Server paths:**
- code: /root/autodl-tmp/cc/Agent-evolving-harness/gaia2/
- results: gaia2/results/
- data: /root/autodl-tmp/cc/gaia2/{data,scenarios,judge_cache}
- python: /root/autodl-tmp/cc/are-env/bin/python

**Environment variables.**
- Reused: BOS_BASE_URL, BOS_API_KEY (fallback file /root/autodl-tmp/vllm_api_key), BOS_MODEL, BOS_MAX_TOKENS (8192), BOS_TIMEOUT, BOS_THINK_OFF, BOS_TASKS (JSON list of tids), BOS_REPLAY, BOS_HINTS, BOS_EDITS_OFF.
- New: G2_SCEN_DIR, G2_INDEX, G2_OUT, G2_STEPS=40, G2_GEN_SECONDS=1.0, G2_HIST=20, G2_JUDGE_BASE_URL/MODEL/KEY, G2_JUDGE_CACHE, G2_EP_TIMEOUT=3600, G2_CELL_TIMEOUT=30, G2_NO_REEXEC (1 for local tests).

**Task ids.** tid = scenario_id. U5 asserts it is unique across the 5 capability configs; if not, use f"{config}__{scenario_id}". A tid never contains "/" or ":".

### U1 g2_env.py
```python
def install_determinism() -> None                 # idempotent; patches environment.TimeManager, uuid/time shims (before any ARE object)
def begin_episode(tid: str, seed: int) -> None    # reseed uuid shim RNG
def load_scenario_json(tid: str) -> tuple[str, str]   # (config, scenario_json) from G2_SCEN_DIR/<tid>.json.gz via G2_INDEX
class G2Env:
    def __init__(self, scenario_json, judge_engine, *, gen_seconds, tid, seed): ...
    nb_turns: int; duration: float; start_time: float; additional_system_prompt: str | None; config: str | None
    def tools(self) -> list            # AppTool objects, hidden AUI tools removed; use tool._public_name
    def now(self) -> float
    def tick(self) -> None
    def advance(self, seconds: float) -> None
    def pull_messages(self) -> dict    # {"user": [...], "notifications": ["[YYYY-mm-dd HH:MM:SS] msg",...], "stop": bool}
    def idle_until_message(self, cap_seconds: float) -> None
    def first_task(self) -> str        # extract_tasks(scenario)[0]
    def turns_done(self) -> int        # AGENT send_message_to_user events
    def stopped(self) -> bool; def time_up(self) -> bool
    def validate(self) -> dict         # {"success","rationale","rationale_diag","G","agent_counts","oracle_counts","n_oracle_writes","exception"}
    def state_hash(self) -> str        # sha256 of canonical JSON: env.get_apps_state() + event projection (no ids) + round(now,3)
```
`__init__` construction order:
1. import_from_json_to_benchmark.
2. preprocess_scenario(scenario, judge_config=GraphPerEventJudgeConfig(engine=judge_engine), max_scenario_duration=get_scenario_duration(...), offline_validation=False, tool_augmentation_config=None, env_events_config=None).
3. Environment(EnvironmentConfig(oracle_mode=False, queue_based_loop=False, start_time=scenario.start_time, time_increment_in_seconds=scenario.time_increment_in_seconds), environment_type=EnvironmentType.CLI, notification_system=VerboseNotificationSystem()).
4. The body of Environment.run without start(): time_manager.reset, duration, delete_all_completed_events, register_apps, schedule(scenario.events), aui.set_cli(True), aui.wait_for_user_response=False, state=RUNNING, prepare_events_for_start(), tick().

Also set logging "are" to WARNING. Never use a2a or noise.

**U1 server verification:** a scripted 3-cell run must give the same state hash across 2 processes. The task must arrive via pull_messages. wait_for_notification(60) must advance the clock by at most 60. send_message_to_user must make turns_done() == 1.

### U2 g2_exec.py
```python
def strip_think(text) -> tuple[str, str]     # (answer after last </think>, thinking); unterminated <think> -> ("", text)
def extract_code(answer) -> str              # = bos_appworld_v3.extract_code_v2
def validate_code(code) -> str               # = bos_appworld_v3.validate_code
def format_tool_index(tools) -> str          # "App__tool(a:str*, b:int=3) -> ret  # desc[:90]" grouped by app
class CodeExecutor:
    def __init__(self, tools, cell_timeout_s=30): ...
    def run(self, code) -> tuple[str, dict]  # (output, {"calls":[...], "writes": int, "exc": str|None})
def readonly(code, write_names) -> bool
```
Executor behaviour:
- The namespace persists across cells.
- stdout is captured, and the value of a final expression is echoed.
- Exceptions produce "Execution failed. Traceback (most recent call last):\n...\n<Type>: <msg>".
- A TypeError raised by a tool appends "\n[harness] Signature (* = required): <line>".
- help("App__tool") prints the full documentation.
- input, exit, quit and open are disabled.
- A cell timeout is enforced via signal.setitimer (POSIX).

Local selftest: use fake duck-typed tools (_public_name, function_description, args[name, arg_type, has_default, default, description], return_type, write_operation, __call__).

### U3 g2_judge.py
```python
class CachedJudgeEngine(LLMEngine):   # fallback base class when ARE is absent
    def __init__(self, model, base_url, api_key, cache_dir, temperature=0.0, max_tokens=1024, think=False, client=None): ...
    def chat_completion(self, messages, stop_sequences=[], **kw) -> tuple[str, dict]
    hits: int; misses: int
def judge_engine_from_env() -> CachedJudgeEngine
```
- The cache key is sha256 of json{model, messages, temperature, max_tokens, think}.
- Writes are atomic to <dir>/<k[:2]>/<k>.json.
- <think> is stripped from responses.
- Up to 6 retries.
- Failures are never cached.

### U4 bos_gaia2.py and g2_hooks.py
**load_v3 copy.** Same semantics as bos_appworld_v3.load_v3, with ALLOWED_IMPORTS, FORBIDDEN and HOOKS copied from alfworld/bos_alfworld.py.

**Hook order (must equal the bit_rubric._simulate rules):**

*Live step k:*
1. Set state _step, _tid and _replay_len.
2. Run pre_call.
3. Call the LLM, with up to 3 free re-asks per step and 12 per episode; the clock does not move.
4. If there is no valid code, this is a no_exec step: advance, tick, pull. Skip post_parse and post_exec.
5. Otherwise run post_parse, then pre_complete if "send_message_to_user" is in the code.
6. Then: env.advance(GEN), ex.run(code), tick. If the turn count grew and turns remain, call idle_until_message. Then pull.
7. out = exec_out + notification block (appended AFTER the output, so the "Execution failed" prefix is preserved). User messages render as "[user message] ...".
8. Run post_exec.

*Replayed step:* no pre_call or post_parse. The same advance/exec/tick/idle/pull sequence runs, and post_exec is called for every item, including "".
- A "" item means no exec: out = "Nothing was executed this step."
- A dict item executes `exec`, shows `shown` in the history, and logs code=exec and shown=shown[:300].

**Prompt and history:**
- state["_instr"] = env.first_task() before step 0, and state["_hint"] = HINTS[tid].
- The user turn at step 0 is f"Current time: {dt}\nTask: {instr}".
- Later user turns are "Output:\n```\n"+out_view+"\n```"+f"\n[{k+1} of {MAX_STEPS} steps used]". out_view is capped at 3000 characters (8000 when the cell calls help) and always carries the H1.1 truncation marker.
- The assistant history contains only the answer text after </think>.

**LLM call.** Same retry/backoff as bos_appworld_v3. extra_body sets enable_thinking=False when BOS_THINK_OFF=1. Read message.content and reasoning_content.

**System message** (a stable prefix, so vLLM prefix caching applies):
- Role and rules: one python block per reply, tools are called as functions, print results, use help().
- AgentUserInterface__send_message_to_user(content=...) is the only way to reply, and it ENDS the turn. Send exactly one message per user request, or one clarifying question if the request is ambiguous.
- Use SystemApp__wait_for_notification(timeout=...) to wait for time-based events.
- The step budget.
- Then: format_tool_index(env.tools()), get_notification_system_prompt(env.notification_system, scenario.apps), and scenario.additional_system_prompt.

**CLI:**
- `eval --patch P|none --seed S --tag T --workers W [--n-games N] [--replay-only]`, with tasks taken from BOS_TASKS.
- `selftest --result R.json [--n 10] [--twice]` replays logged items with --replay-only and compares per-step t_sim and out[:200], the final state_hash, won and rationale. --twice runs two replays against each other. It writes results/selftest_<tag>.json and exits 1 on any mismatch.

**Execution setup.** Re-exec with PYTHONHASHSEED=0 unless G2_NO_REEXEC=1. Use ProcessPoolExecutor(spawn, max_tasks_per_child=1). Each worker calls install_determinism() and begin_episode(). An exception marks the episode crashed. The episode wall timeout is checked between steps.

**Result JSON** (G2_OUT/results/{tag}_seed{seed}.json): all AppWorld keys plus:
- Run level: "bench":"gaia2", harness_v2/h1/h11/no_eval true, max_steps, gen_seconds, think, judge_model, judge_hits, judge_misses.
- Per episode: configs, instr, rationale, rationale_diag, end_reason ∈ {turns_done, env_stopped, time_up, budget, crashed}, nb_turns, turns_done, state_hash, agent_counts, oracle_counts, fired.
- Per traj step: step, code, out[:200], resp[-600:], exec_error, replayed, no_exec, shown?, code_final[:300], free_retries, invalid_code?, edit_err?, t_sim, notif[:300], calls, writes, api_retries?, pc, gp=None, gf=None.

**Local test test_g2_harness_fake.py.** Uses FakeG2Env (2 toy apps) and a scripted fake LLM. It checks:
- the result keys;
- load_episodes reads the file;
- BOS_REPLAY items of type str, dict and "";
- --replay-only;
- the hook order against bit_rubric.simulate (same fire k for null_note-at-step-3 and for a block_once spec);
- selftest.

### U5 g2_splits.py
- `index --data /root/autodl-tmp/cc/gaia2/data` writes G2_SCEN_DIR/<tid>.json.gz and index.json {tid: {config, row_id, scenario_id, universe}}. It reports the counts and how mini/demo overlap the other configs.
- `preflight --workers 8` uses G2Env with a stub judge and records: ok/err, nb_turns, n_oracle_writes, apps, n_tools, index_chars, tags, duration, first task.
- `make` writes the split files and instructions_all.json.

### U6 BIT tool generalisation
- **bit_common:** add ep["bench"] = d.get("bench","appworld"). Fall back to d["instr"][i] when instr lacks a tid.
- **bit_rubric._simulate:** the marker is "send_message_to_user" when bench == gaia2, otherwise "complete_task". For gaia2 the k=0 prompt proxy is "Current time: (t)\nTask: {instr}".
- **bit_propose:**
  - --bench {auto,appworld,gaia2}.
  - Gaia2 harness description: a simulated phone with apps; python cells calling App__tool(...); the turn ends with AgentUserInterface__send_message_to_user; multi-turn scenarios and time events (SystemApp__wait_for_notification); the verifier counts write actions per tool, then checks arguments, partly with an LLM.
  - Outcome lines report turns done, sent message and end_reason. G is described as "write-action overlap with the oracle".
  - The privileged section is headed "verifier rationale".
  - Gaia2 format example: the same failing tool call 3 times leads to a note to read help(...). Never a send-message rule.
- **bit_branch and bit_active:** add --harness-cmd (default "python bos_appworld_v3.py"), shlex-split into the job lines. For Gaia2 use "env -u PYTHONPATH /root/autodl-tmp/cc/are-env/bin/python ../gaia2/bos_gaia2.py" (jobs run with cwd appworld/; never put cd in the job line).
- **New files:**
  - gaia2/g2_failed_checks.py --tree --runs --out [--with-args]: per-tool count lines taken from the logged rationale (no replay).
  - gaia2/bit_refs/null_note_step3.json and gaia2/bit_refs/send_before_write.json (block_once: send_message_to_user while no earlier write-like call exists).
  - gaia2/test_g2_offline.py: a synthetic Gaia2 result fixture run through bit_tree -> simulate(refs) -> bit_propose (BOOST_MOCK=1 --bench gaia2) -> bit_screen -> bit_branch build (--harness-cmd ...). Also re-run appworld/boost/test_bit_offline.py so AppWorld stays unchanged.

### U7 g2_oracle_replay.py (wave 2)
- BOS_REPLAY items are built from the scenario's OracleEvents in topological/turn order, as App__fn(**args) cells from event.action_desc.
- SystemApp__wait_for_notification is inserted where the delay exceeds the generation time.
- Scenarios with {{event_id}} placeholders are skipped or resolved.
- Run with eval --replay-only.
- Target: success >= 80% on 20 execution + 20 search scenarios, with every failure explained. Then selftest --twice.

## 4. Splits
- **Pool:** the 5 capability configs (execution, search, adaptability, time, ambiguity) of validation. U5 confirms the counts.
- **Excluded:** mini, demo, duplicates, preflight failures. No a2a and no noise.
- **Ordering:** within each config, sort by sha256("g2split:"+tid), then round-robin over universes.
- **Per config:** disc 60, val 30, test the rest (about 300 / 150 / 350 overall).
- **Subsets:** tasks_pilot (10 per config = 50) and tasks_disc_core (30 per config = 150).
- **Freeze before any proposer run.** The test split is touched once.

## 5. Verification sequence
**Local (no ARE):**
1. U2 selftest.
2. U3 fake-client test.
3. U4 fake-env test.
4. U6 test_g2_offline + appworld test_bit_offline.
5. compile_patch output loads in g2_hooks.load_v3.

**Server:**
1. U5 index -> preflight -> make.
2. U1 two-process hash.
3. U3 live judge call.
4. U7 oracle replay + selftest --twice.
5. Pilot run (50 tasks).
6. selftest on the pilot.
7. Live vs simulate fidelity for null_note_step3.
8. disc_core x 2 seeds -> BIT round.

## 6. Risks
- **Determinism holes:** datetime.now() defaults, event ordering at equal timestamps, judge pause/resume requiring state RUNNING. PYTHONHASHSEED=0 is mandatory.
- **Time scenarios:** scores depend on gen_seconds, so record it and keep it fixed.
- **Turn semantics:** two messages within one turn shift turns. The prompt says "exactly one message per request".
- **Judge:** the local Qwen judge is a limitation. Later, measure agreement with Llama-3.3-70B. Never cache errors.
- **Privileged leakage:** OracleEventMatchingFailure contains oracle args. The default proposer input is count lines only.
- **Throughput:** episodes are long. Use disc_core for round 1 and compare BOS_THINK_OFF on the pilot. Never enable MTP; use concurrency.
- **Prompt size:** about 100+ tools makes a 10–15k-character index, kept in the system prefix. Trim if p95 exceeds 20k.
- **Executor safety:** cell timeout, disabled builtins, one process per episode.
- **Queue:** use `env -u PYTHONPATH` with the are-env python. Results go to gaia2/results, so pass that to readout and lowrank via --results.
