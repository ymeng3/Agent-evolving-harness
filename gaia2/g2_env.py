"""Gaia2 (ARE 1.2.0) environment for the BIT pipeline: deterministic synchronous simulation (GAIA2_ADAPTER_PLAN §0-2, U1).

ARE's clock is wall-clock based and its event loop runs in a thread. Here the thread is never started:
 - VirtualTimeManager replaces TimeManager (pure counter; pause/resume are no-ops; add_offset advances it, never backwards),
 - the harness drives env.tick() itself (G2Env.advance / tick / idle_until_message),
 - uuid.uuid4 in are.simulation.* is a seeded shim (begin_episode), time.time in are.simulation.apps.* reads the virtual clock,
 - datetime.now() default arguments frozen at ARE import time (email_client / messaging *_with_time) are rewritten to the scenario start,
 - the event log orders equal-time events by insertion (a cell runs at one virtual instant; ARE's heap is not stable on ties).
So the state trajectory is a function of (scenario, tid, seed, gen_seconds, code sequence) once PYTHONHASHSEED=0 (App.set_seed uses hash()).

Validation is ARE's own online judge (preprocess_scenario -> GraphPerEventJudge); the judge engine is passed in (CachedJudgeEngine, or
StubJudgeEngine for tests). validate() adds G = write-action multiset overlap with the oracle, which needs no LLM.

usage (server, are-env python):
  PYTHONHASHSEED=0 python -m gaia2.g2_env --tid <tid> --script [--seed 0] [--gen-seconds 1.0] [--json-out out.json]
  PYTHONHASHSEED=0 python -m gaia2.g2_env --tid <tid> --list-tools
env: G2_SCEN_DIR (default /root/autodl-tmp/cc/gaia2/scenarios), G2_INDEX (default <G2_SCEN_DIR>/index.json, else <G2_SCEN_DIR>/../data/index.json)"""
import gzip, hashlib, inspect, json, logging, os, random, re, sys, time as _real_time, uuid as _real_uuid
from collections import Counter
from datetime import datetime, timezone

try:
    from are.simulation.time_manager import TimeManager as _ARETimeManager
except ImportError:  # module stays importable without ARE (local tests); G2Env needs ARE
    _ARETimeManager = object

HIDDEN_AUI_TOOLS = {"AgentUserInterface__get_last_message_from_user", "AgentUserInterface__get_last_message_from_agent",
                    "AgentUserInterface__get_last_unread_messages", "AgentUserInterface__get_all_messages"}
APPS_TO_SKIP = ["SandboxLocalFileSystem"]  # = are.simulation.benchmark.scenario_loader.APPS_TO_SKIP
AUI_SEND = "send_message_to_user"
DEFAULT_SCEN_DIR = "/root/autodl-tmp/cc/gaia2/scenarios"

_ACTIVE_TM = None  # the VirtualTimeManager last reset (= the running env's clock); read by the apps' time shim


class VirtualTimeManager(_ARETimeManager):
    """Drop-in for are.simulation.time_manager.TimeManager without wall clock: time() = start_time + offset."""

    def __init__(self):
        self.real_start_time = 0.0
        self.start_time = 0.0
        self.offset = 0.0
        self.is_paused = False
        self.pause_real_start_time = None
        self.pause_passed_time = None
        self.pause_offset = 0.0
        self.clamped_negative = 0  # backwards jumps refused (diagnostic)

    def time(self):
        return self.start_time + self.offset

    def time_passed(self):
        return self.offset

    def real_time_passed(self):
        return self.offset

    def reset(self, start_time=None):
        global _ACTIVE_TM
        self.start_time = float(start_time) if start_time is not None else 0.0
        self.real_start_time = 0.0
        self.offset = 0.0
        self.is_paused = False
        self.pause_real_start_time = None
        self.pause_passed_time = None
        _ACTIVE_TM = self

    def pause(self):
        pass

    def resume(self):
        pass

    def set_offset(self, offset):
        self.offset = float(offset)

    def add_offset(self, offset):
        if offset > 0:
            self.offset += offset
        elif offset < 0:
            self.clamped_negative += 1


class _UuidShim:
    """Stands in for the `uuid` module attribute of are.simulation.* modules; uuid4() is drawn from a per-episode RNG."""

    def __init__(self):
        self.rng = random.Random(0)

    def uuid4(self):
        return _real_uuid.UUID(int=self.rng.getrandbits(128), version=4)

    def __getattr__(self, name):
        return getattr(_real_uuid, name)


class _TimeShim:
    """Stands in for the `time` module attribute of are.simulation.apps.* modules; time() is the virtual clock."""

    def time(self):
        return _ACTIVE_TM.time() if _ACTIVE_TM is not None else 0.0

    def __getattr__(self, name):
        return getattr(_real_time, name)


_UUID_SHIM, _TIME_SHIM = _UuidShim(), _TimeShim()
_INSTALLED = False
_DT_DEFAULT_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")


def _patch_modules():
    """Swap uuid / time / TimeManager attributes in every loaded are.simulation module (idempotent; re-run after late imports)."""
    for name, mod in list(sys.modules.items()):
        if mod is None or not name.startswith("are.simulation"):
            continue
        d = getattr(mod, "__dict__", {})
        if d.get("uuid") is _real_uuid:
            mod.uuid = _UUID_SHIM
        if name.startswith("are.simulation.apps") and d.get("time") is _real_time:
            mod.time = _TIME_SHIM
        if _ARETimeManager is not object and d.get("TimeManager") is _ARETimeManager:
            mod.TimeManager = VirtualTimeManager


def _patch_event_log():
    """EventLog orders by event_time only and its heap is not stable on ties; with a discrete clock all calls of one cell share a
    timestamp, so ties are the rule. Order ties by insertion (what ARE gets with strictly increasing wall-clock times)."""
    from heapq import heappush
    from are.simulation import types as T
    from are.simulation.priority_queue import HeapItem, PriorityQueue
    if getattr(T.EventLog, "_g2_patched", False):
        return

    class _SeqHeapItem(HeapItem):  # sort key = (fields..., insertion seq); the event itself is untouched (its __dict__ is reused)
        def __init__(self, item, fields, seq):
            super().__init__(item, fields)
            self.seq = seq

        def get_tuple(self, item):
            return tuple(getattr(item.item, f) for f in self.fields) + (getattr(item, "seq", 0),)

    class _StablePriorityQueue(PriorityQueue):
        def __init__(self, maxsize=0, fields=None):
            super().__init__(maxsize, fields)
            self._seq = 0

        def _put(self, item):
            with self.lock:
                self._seq += 1
                heappush(self.queue, _SeqHeapItem(item, self.fields or [], self._seq))

    orig_init = T.EventLog.__init__

    def __init__(self, *a, **kw):
        orig_init(self, *a, **kw)
        if type(self.past_events) is PriorityQueue and not self.past_events.queue:
            self.past_events = _StablePriorityQueue(fields=list(self.past_events.fields or ["event_time"]))

    T.EventLog.__init__ = __init__
    T.EventLog._g2_patched = True


def install_determinism() -> None:
    """Idempotent. Must run before any ARE object is created: virtual TimeManager, uuid/time shims, stable event log, quiet logs."""
    global _INSTALLED
    if _INSTALLED:
        _patch_modules()
        return
    if _ARETimeManager is object:
        raise ImportError("ARE (are.simulation) is not importable in this python")
    logging.getLogger("are").setLevel(logging.WARNING)
    import are.simulation.time_manager as tm_mod
    import are.simulation.types, are.simulation.apps, are.simulation.environment, are.simulation.notification_system  # noqa: F401
    import are.simulation.data_handler.importer, are.simulation.scenarios.scenario_imported_from_json.utils  # noqa: F401
    import are.simulation.scenarios.config, are.simulation.scenarios.utils.turn_conditions  # noqa: F401
    import are.simulation.validation, are.simulation.validation.configs, are.simulation.validation.utils.scenario_utils  # noqa: F401
    _patch_modules()
    tm_mod.TimeManager = VirtualTimeManager  # late `from ...time_manager import TimeManager` get the virtual one too
    _patch_event_log()
    logging.getLogger("are").setLevel(logging.WARNING)
    _INSTALLED = True


def begin_episode(tid: str, seed: int) -> None:
    """Reseed the uuid shim (and the global random module) from sha256(f"{tid}|{seed}")."""
    s = int.from_bytes(hashlib.sha256(f"{tid}|{seed}".encode()).digest()[:8], "big")
    _UUID_SHIM.rng.seed(s)
    random.seed(s)


def _fix_datetime_defaults(start_time: float) -> int:
    """datetime.now() default arguments are evaluated at ARE import (email_client.create_and_add_email_with_time,
    messaging.add_message_with_time): rewrite every 'YYYY-mm-dd HH:MM:SS' string default of app methods to the scenario start."""
    ts = datetime.fromtimestamp(start_time or 0.0, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    n = 0
    for name, mod in list(sys.modules.items()):
        if mod is None or not name.startswith("are.simulation.apps"):
            continue
        for cls in list(vars(mod).values()):
            if not isinstance(cls, type) or getattr(cls, "__module__", None) != name:
                continue
            for attr in list(vars(cls).values()):
                try:
                    fn = inspect.unwrap(attr) if callable(attr) else None
                except Exception:
                    fn = None
                dflt = getattr(fn, "__defaults__", None)
                if not dflt:
                    continue
                new = tuple(ts if isinstance(x, str) and _DT_DEFAULT_RE.match(x) else x for x in dflt)
                if new != dflt:
                    fn.__defaults__ = new
                    n += 1
    return n


def _scen_paths():
    """G2_INDEX default: <G2_SCEN_DIR>/index.json if present, else <G2_SCEN_DIR>/../data/index.json (where g2_splits index writes it)."""
    sdir = os.environ.get("G2_SCEN_DIR", DEFAULT_SCEN_DIR)
    index = os.path.join(sdir, "index.json")
    if not os.path.exists(index): index = os.path.join(os.path.dirname(os.path.abspath(sdir)), "data", "index.json")
    return sdir, os.environ.get("G2_INDEX", index)


def load_scenario_json(tid: str) -> tuple:
    """(config, scenario_json) from G2_SCEN_DIR/<tid>.json.gz; config from G2_INDEX {tid: {"config": ...}}."""
    sdir, index = _scen_paths()
    config = None
    if os.path.exists(index):
        with open(index, encoding="utf-8") as f:
            config = (json.load(f).get(tid) or {}).get("config")
    with gzip.open(os.path.join(sdir, f"{tid}.json.gz"), "rt", encoding="utf-8") as f:
        return config, f.read()


class StubJudgeEngine:
    """Judge engine for tests: accepts every soft check. ARE calls engine(messages, additional_trace_tags=[...]) -> (text, meta);
    content checkers look for [[Success]], signature/sanity/cab/tone checkers for [[True]]."""
    model_name = "stub"
    hits = misses = 0

    def chat_completion(self, messages, stop_sequences=[], **kw):
        self.misses += 1
        return "[[Success]] [[True]]", {}

    def __call__(self, messages, stop_sequences=[], **kw):
        return self.chat_completion(messages, stop_sequences, **kw)


def _public_tool_name(event):
    """Agent-facing tool name App.name__function (the judge's event.tool_name uses the app CLASS name instead)."""
    a = event.action
    app = getattr(a, "app", None)
    return f"{getattr(app, 'name', None) or event.app_class_name()}__{event.function_name()}"


WAIT_TOOL = "SystemApp__wait_for_notification"


class _WaitTool:
    """SystemApp__wait_for_notification as the agent sees it: first set aside the messages already due (G2Env.stash_messages),
    then ARE's tool. Every other attribute is the wrapped AppTool's."""

    def __init__(self, tool, g2env):
        self._tool, self._g2env = tool, g2env

    def __getattr__(self, name):
        return getattr(self._tool, name)

    def __call__(self, *args, **kwargs):
        self._g2env.stash_messages()
        return self._tool(*args, **kwargs)


class G2Env:
    """One Gaia2 scenario under the virtual clock. Construction (plan §2 U1): import -> preprocess_scenario (oracle run, judge,
    turn triggers) -> Environment(CLI, VerboseNotificationSystem) -> body of Environment.run without start() -> first tick."""

    def __init__(self, scenario_json, judge_engine, *, gen_seconds=1.0, tid="", seed=0, config=None):
        install_determinism()
        begin_episode(tid, seed)
        from are.simulation.apps.agent_user_interface import AgentUserInterface
        from are.simulation.data_handler.importer import JsonScenarioImporter
        from are.simulation.environment import Environment, EnvironmentConfig
        from are.simulation.notification_system import VerboseNotificationSystem
        from are.simulation.scenarios.config import MAX_SCENARIO_DURATION, MAX_TIME_SCENARIO_DURATION
        from are.simulation.scenarios.scenario_imported_from_json.utils import get_scenario_duration, preprocess_scenario
        from are.simulation.types import EnvironmentState, EnvironmentType
        from are.simulation.validation.configs import GraphPerEventJudgeConfig
        self.tid, self.seed, self.gen_seconds = tid, seed, float(gen_seconds)
        if isinstance(scenario_json, bytes):
            scenario_json = scenario_json.decode("utf-8")
        if config is None:
            try:
                config = json.loads(scenario_json)["metadata"]["definition"].get("config")
            except Exception:
                config = None
        self.config = config
        scenario, _, _ = JsonScenarioImporter().import_from_json_to_benchmark(
            scenario_json, apps_to_skip=APPS_TO_SKIP, load_completed_events=False)
        _patch_modules()  # catch modules imported lazily by the importer
        self.n_datetime_defaults_fixed = _fix_datetime_defaults(scenario.start_time or 0.0)
        preprocess_scenario(scenario, judge_config=GraphPerEventJudgeConfig(engine=judge_engine),
                            max_scenario_duration=get_scenario_duration(scenario, MAX_TIME_SCENARIO_DURATION, MAX_SCENARIO_DURATION),
                            offline_validation=False, tool_augmentation_config=None, env_events_config=None)
        tinc = scenario.time_increment_in_seconds or 1
        env = Environment(EnvironmentConfig(oracle_mode=False, queue_based_loop=False, start_time=scenario.start_time,
                                            time_increment_in_seconds=tinc),
                          environment_type=EnvironmentType.CLI, notification_system=VerboseNotificationSystem())
        # = Environment.run(scenario, wait_for_end=False) minus start(): no event-loop thread
        env.time_manager.reset(start_time=env.start_time)
        env.duration = scenario.duration
        env.time_increment_in_seconds = tinc
        env.delete_all_completed_events()
        env.register_apps(scenario.apps if scenario.apps else [])
        env.schedule(scenario.events)
        aui = env.get_app_with_class(AgentUserInterface)
        if aui is not None:
            aui.set_cli(is_cli=True)
            aui.wait_for_user_response = False
        env.state = EnvironmentState.RUNNING
        env.prepare_events_for_start()
        self.env, self.scenario, self.judge = env, scenario, getattr(scenario, "judge", None)
        self.notification_system = env.notification_system
        self._EnvironmentState = EnvironmentState
        self.nb_turns = int(scenario.nb_turns or 1)
        self.duration = float(scenario.duration) if scenario.duration is not None else float("inf")
        self.start_time = float(env.start_time)
        self.additional_system_prompt = scenario.additional_system_prompt
        self._tools = None
        self._validation = None
        self._stash = None
        # judge tool names use the app CLASS (EmailClientV2__send_email); agents see app names (Emails__send_email). Two apps can share
        # a class (Messages and Chats are both MessagingAppV2): the judge then conflates them, and the name becomes "Chats|Messages__fn"
        cls_apps = {}
        for name, app in env.apps.items(): cls_apps.setdefault(type(app).__name__, set()).add(getattr(app, "name", None) or name)
        self.judge_class_names = {c: "|".join(sorted(ns)) for c, ns in cls_apps.items()}
        for app in env.apps.values():
            if hasattr(app, "local_fs") and isinstance(getattr(app, "tmpdir", None), str): self._virtualize_fs(app)
        self.tick()

    def _virtualize_fs(self, app):
        """The Files app (SandboxLocalFileSystem) is a real mkdtemp dir: info() / ls(detail=True) report wall-clock created / mtime /
        atime and inode numbers, which leak into outputs and the event log. Patch its local_fs (below ARE's event registration):
        a timestamp from before the episode becomes the scenario start; a later one (a file the agent created or changed) becomes
        the virtual time at which this (path, timestamp) was first reported, deterministic given the call sequence; ino becomes a
        hash of the relative path."""
        fs, root, t_built, seen = app.local_fs, app.tmpdir, _real_time.time(), {}
        orig_info, orig_ls = fs.info, fs.ls

        def fix(d):
            if not isinstance(d, dict): return d
            rel = str(d.get("name", ""))
            rel = rel[len(root):] if rel.startswith(root) else rel
            for k in ("created", "mtime", "atime"):
                v = d.get(k)
                if isinstance(v, (int, float)):
                    d[k] = self.start_time if v <= t_built else seen.setdefault((rel, k, v), self.now())
            if "ino" in d: d["ino"] = int(hashlib.sha256(rel.encode()).hexdigest()[:12], 16)
            return d

        def info(path, **kw): return fix(orig_info(path, **kw))

        def ls(path, detail=True, **kw):
            r = orig_ls(path, detail=detail, **kw)
            return [fix(x) for x in r] if isinstance(r, list) else r
        fs.info, fs.ls = info, ls

    # ---- tools / clock -------------------------------------------------------------------------------------------------------
    def tools(self) -> list:
        """AppTool objects of all registered apps minus the AUI tools the default ARE agent hides; names are tool._public_name.
        SystemApp__wait_for_notification is wrapped (_WaitTool) so that it first sets aside the messages already due."""
        if self._tools is None:
            self._tools = [_WaitTool(t, self) if t._public_name == WAIT_TOOL else t for t in self.env.get_tools()
                           if t._public_name not in HIDDEN_AUI_TOOLS and t.name not in HIDDEN_AUI_TOOLS]
        return self._tools

    def now(self) -> float:
        return self.env.time_manager.time()

    def tick(self) -> None:
        """One env tick at the current virtual time (no-op once the env is stopped, like ARE's loop after stop)."""
        if self.stopped():
            return
        self.env.tick()
        self.env.tick_count += 1

    def advance(self, seconds: float) -> None:
        if seconds and seconds > 0:
            self.env.time_manager.add_offset(float(seconds))

    def _pending(self):
        """messages due now: set aside during the cell (stash_messages) or still queued."""
        st = self._stash or {}
        ts = datetime.fromtimestamp(self.now(), tz=timezone.utc)
        return list(st.get("user") or []) + list(st.get("notifications") or []) + (["stop"] if st.get("stop") else []) + \
            [m for m in self.env.notification_system.message_queue.list_view() if m.timestamp <= ts]

    def pull_messages(self) -> dict:
        """Drain messages due at now(): {"user": [content,...], "notifications": ["[YYYY-mm-dd HH:MM:SS] msg",...], "stop": bool},
        preceded by those set aside during the cell (stash_messages)."""
        st, self._stash = self._stash, None
        m = self._drain()
        if st: m = {"user": st["user"] + m["user"], "notifications": st["notifications"] + m["notifications"], "stop": st["stop"] or m["stop"]}
        return m

    def stash_messages(self) -> None:
        """Set aside the messages due now (shown after the cell by pull_messages). ARE's wait_for_notification returns at once while
        an undrained notification is queued; ARE's agent drains the queue between its one-tool steps, but a cell can call the tool
        repeatedly (a polling loop then spun until the wall-clock cell timeout: non-deterministic)."""
        m = self._drain()
        if self._stash: m = {"user": self._stash["user"] + m["user"], "notifications": self._stash["notifications"] + m["notifications"],
                             "stop": self._stash["stop"] or m["stop"]}
        self._stash = m

    def _drain(self) -> dict:
        from are.simulation.notification_system import MessageType
        msgs = self.env.notification_system.message_queue.get_by_timestamp(datetime.fromtimestamp(self.now(), tz=timezone.utc))
        user, notes, stop = [], [], False
        for m in msgs:
            if m.message_type == MessageType.USER_MESSAGE:
                mm = re.search(r"\nMessage: (.*)\nAlready read: ", m.message, re.S)
                user.append(mm.group(1) if mm else m.message)
            elif m.message_type == MessageType.ENVIRONMENT_NOTIFICATION:
                notes.append(f"[{m.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {m.message}")
            elif m.message_type == MessageType.ENVIRONMENT_STOP:
                stop = True
        return {"user": user, "notifications": notes, "stop": stop or self.stopped()}

    def idle_until_message(self, cap_seconds: float) -> None:
        """Jump from event to event (like Environment.wait_for_next_notification) until any message (user, notification, stop)
        is due, the env stops, time is up, or cap_seconds of virtual time have passed. Used between turns (ARE's agent loop
        also resumes on user messages or notifications). Costs no step."""
        deadline = min(self.now() + max(0.0, float(cap_seconds)), self.start_time + self.duration + 1.0)
        while not self.stopped() and not self.time_up() and not self._pending():
            if self.now() >= deadline:
                break
            nxt = self.env.get_next_event_time()
            target = deadline if nxt is None or nxt > deadline else max(nxt, self.now())
            self.advance(target - self.now())
            self.tick()

    def first_task(self) -> str:
        from are.simulation.validation.utils.scenario_utils import extract_tasks
        return extract_tasks(self.scenario)[0].rstrip("\n")

    def turns_done(self) -> int:
        """Number of AGENT AgentUserInterface.send_message_to_user events (ARE's turn counter in turn_condition_wrapper)."""
        from are.simulation.scenarios.utils.turn_conditions import is_send_message_to_user
        return sum(1 for e in self.env.event_log.list_view() if is_send_message_to_user(e))

    def stopped(self) -> bool:
        return self.env.state in (self._EnvironmentState.STOPPED, self._EnvironmentState.FAILED)

    def time_up(self) -> bool:
        return self.env.time_manager.time_passed() > self.duration

    # ---- scoring -------------------------------------------------------------------------------------------------------------
    def _write_counts(self):
        """Per-turn Counters of successful AGENT write events (the judge's EnvAgentEventFilter restricted to AGENT), agent vs oracle,
        keyed by agent-facing tool names. Agent turns split after each send_message_to_user, like extract_agent_events."""
        from are.simulation.scenarios.utils.turn_conditions import is_send_message_to_user
        from are.simulation.types import EventType
        from are.simulation.validation.utils.event_utils import EnvAgentEventFilter
        flt = EnvAgentEventFilter()
        ag = sorted([e for e in self.env.event_log.list_view() if e.event_type == EventType.AGENT and flt(e)],
                    key=lambda e: e.event_time)
        a_turns, t = [], 0
        for e in ag:
            while len(a_turns) <= t:
                a_turns.append(Counter())
            a_turns[t][_public_tool_name(e)] += 1
            if is_send_message_to_user(e):
                t += 1
        o_turns = [Counter() for _ in range(self.nb_turns)]
        e2t = self.scenario.event_id_to_turn_idx or {}
        for e in self.scenario.oracle_run_event_log or []:
            if e.event_type == EventType.AGENT and flt(e):
                k = e2t.get(e.event_id, 0)
                while len(o_turns) <= k:
                    o_turns.append(Counter())
                o_turns[k][_public_tool_name(e)] += 1
        return a_turns, o_turns

    def validate(self) -> dict:
        """Official verdict scenario.validate(env) (calls the judge; call once: the judge state advances per call) + G.
        rationale_diag = judge.validate_current_turn(env).rationale when the episode ended before the last turn."""
        if self._validation is not None:
            return self._validation
        out = {"success": False, "rationale": "", "rationale_diag": None, "G": 0.0, "agent_counts": {}, "oracle_counts": {},
               "n_oracle_writes": 0, "exception": None}
        try:
            a_turns, o_turns = self._write_counts()
            n = max(len(a_turns), len(o_turns))
            a_turns += [Counter()] * (n - len(a_turns)); o_turns += [Counter()] * (n - len(o_turns))
            ov = sum(min(a[k], o[k]) for a, o in zip(a_turns, o_turns) for k in set(a) | set(o))
            na, no = sum(sum(a.values()) for a in a_turns), sum(sum(o.values()) for o in o_turns)
            out["G"] = 1.0 if max(na, no) == 0 else ov / max(na, no)
            out["agent_counts"] = dict(sorted(sum(a_turns, Counter()).items()))
            out["oracle_counts"] = dict(sorted(sum(o_turns, Counter()).items()))
            out["n_oracle_writes"] = no
        except Exception as e:
            out["exception"] = f"counts: {type(e).__name__}: {e}"
        try:
            res = self.scenario.validate(self.env)
            out["success"] = bool(res.success)
            out["rationale"] = "" if res.rationale is None else str(res.rationale)
            if res.exception is not None:
                out["exception"] = f"{type(res.exception).__name__}: {res.exception}"
            if out["rationale"].startswith("Validation called at turn") and self.judge is not None:
                diag = self.judge.validate_current_turn(self.env)
                out["rationale_diag"] = "" if diag.rationale is None else str(diag.rationale)
        except Exception as e:
            out["exception"] = f"{type(e).__name__}: {e}"
        # the judge names tools by app CLASS (EmailClientV2__send_email); the agent sees app names (Emails__send_email).
        # Rewrite rationales into agent-facing names (what the proposer and g2_failed_checks consume); keep the raw text.
        out["rationale_raw"], out["rationale_diag_raw"] = out["rationale"], out["rationale_diag"]
        out["rationale"] = self.agent_tool_names(out["rationale"])
        if out["rationale_diag"]: out["rationale_diag"] = self.agent_tool_names(out["rationale_diag"])
        self._validation = out
        return out

    def agent_tool_names(self, text):
        """Class__fn -> App__fn in a judge text (Chats|Messages__fn when a class backs several apps; covers ENV-only tools too)."""
        m = getattr(self, "judge_class_names", {})
        return re.sub(r"\b([A-Za-z]\w*?)__(\w+)", lambda g: f"{m[g.group(1)]}__{g.group(2)}" if g.group(1) in m else g.group(0), text)

    def _project(self, e):
        from are.simulation.utils import make_serializable
        a = e.action
        args = getattr(a, "args", None) or {}
        md = e.metadata
        return [e.event_type.value, None if e.event_time is None else round(e.event_time, 3), type(e).__name__,
                type(a).__name__, _public_tool_name(e) if hasattr(a, "app") else getattr(a, "function_name", None),
                make_serializable({k: v for k, v in args.items() if k != "self"}),
                make_serializable(getattr(md, "return_value", None)),
                None if md is None or md.exception is None else re.sub(r" at 0x[0-9a-f]+", "", str(md.exception))]

    def state_hash(self) -> str:
        """sha256 of canonical JSON: env.get_apps_state() + event-log projection (no ids) + round(now, 3).
        G2_DUMP_STATE_DIR (debugging selftest mismatches): also write the canonical JSON to <dir>/<tid>_<hash12>.json."""
        s = self.canonical_state(); h = hashlib.sha256(s.encode("utf-8")).hexdigest()
        d = os.environ.get("G2_DUMP_STATE_DIR")
        if d:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"{self.tid}_{h[:12]}.json"), "w", encoding="utf-8") as f: f.write(s)
        return h

    def _sandbox_dirs(self):
        """real directories of the Files app (per-process mkdtemp names), longest first."""
        return sorted({p for app in self.env.apps.values() if isinstance(getattr(app, "tmpdir", None), str)
                       for p in (app.tmpdir, os.path.dirname(app.tmpdir))}, key=len, reverse=True)

    def scrub(self, text: str) -> str:
        """agent-visible text without the Files app's real paths (error messages, file objects): the sandbox root becomes "" (paths
        read as the app shows them, e.g. /Documents/x) and its parent session dir "<sandbox>"; memory addresses are dropped."""
        if not text: return text
        dirs = self._sandbox_dirs()
        for d in dirs[:1] if dirs else []:
            text = text.replace(d, "")
        for d in dirs[1:]:
            if len(d) > 4: text = text.replace(d, "<sandbox>")
        return re.sub(r" at 0x[0-9a-fA-F]+", "", text)

    def canonical_state(self) -> str:
        from are.simulation.utils import make_serializable
        payload = {"apps": make_serializable(self.env.get_apps_state()),
                   "events": [self._project(e) for e in self.env.event_log.list_view()], "now": round(self.now(), 3)}
        s = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        # the Files app (SandboxLocalFileSystem; APPS_TO_SKIP matches app names, so "Files" is kept, as in ARE's benchmark)
        # lives in a per-process mkdtemp dir that appears in its state and in paths: mask it
        for d in self._sandbox_dirs():
            if len(d) > 4:
                s = s.replace(d, "<sandbox>")
        return re.sub(r" at 0x[0-9a-fA-F]+", "", s)   # reprs of objects in return values (e.g. a file object from Files__open)


# ---- check entry point -------------------------------------------------------------------------------------------------------
def _call(tools, name, **kw):
    t = tools.get(name)
    if t is None:
        return f"<missing tool {name}>"
    try:
        return t(**kw)
    except Exception as e:
        return f"Execution failed. {type(e).__name__}: {e}"


def _pick(tools, prefs):
    for p in prefs:
        if p in tools:
            return p
    return None


def script_check(tid, seed=0, gen_seconds=1.0, dump_state=""):
    """Scripted 3-cell run (read; write + wait_for_notification(60); send_message_to_user) with the stub judge.
    Each cell follows the harness order: advance(gen) -> exec -> tick -> [idle if a turn ended and turns remain] -> pull."""
    config, sj = load_scenario_json(tid)
    t0 = _real_time.time()
    env = G2Env(sj, StubJudgeEngine(), gen_seconds=gen_seconds, tid=tid, seed=seed, config=config)
    rep = {"tid": tid, "config": env.config, "seed": seed, "gen_seconds": gen_seconds, "build_s": round(_real_time.time() - t0, 2),
           "nb_turns": env.nb_turns, "duration": env.duration, "start_time": env.start_time, "n_tools": len(env.tools()),
           "n_datetime_defaults_fixed": env.n_datetime_defaults_fixed}
    tools = {t._public_name: t for t in env.tools()}
    rep["hidden_tools_present"] = sorted(HIDDEN_AUI_TOOLS & set(tools))
    rep["pull0"] = env.pull_messages()
    rep["first_task"] = env.first_task()
    rep["pull0_has_task"] = any(rep["first_task"].strip()[:80] in u for u in rep["pull0"]["user"])
    cells = []

    def cell(fn):
        env.advance(env.gen_seconds)
        tb, nb = env.now(), env.turns_done()
        r = fn()
        env.tick()
        if env.turns_done() > nb and env.turns_done() < env.nb_turns:
            env.idle_until_message(env.duration)
        p = env.pull_messages()
        cells.append({"t_exec": tb - env.start_time, "t_after": env.now() - env.start_time, "ret": str(r)[:300], "pull": p,
                      "turns_done": env.turns_done(), "stopped": env.stopped(), "hash": env.state_hash()})

    read = _pick(tools, ["Contacts__get_contacts", "Emails__list_emails", "Calendar__get_calendar_events_from_to"])
    write = _pick(tools, ["Contacts__add_new_contact", "Emails__send_email", "Calendar__add_calendar_event"])
    rep["read_tool"], rep["write_tool"] = read, write
    cell(lambda: _call(tools, read, offset=0) if read == "Contacts__get_contacts" else _call(tools, read))
    wait_info = {}

    def c2():
        if write == "Contacts__add_new_contact":
            r = _call(tools, write, first_name="Gtwo", last_name="Probe", phone="+10000000000")
        elif write == "Emails__send_email":
            r = _call(tools, write, recipients=["probe@example.com"], subject="probe", content="probe")
        else:
            r = _call(tools, write)
        w0 = env.now()
        _call(tools, "SystemApp__wait_for_notification", timeout=60)
        wait_info.update(dt=env.now() - w0)
        return r

    cell(c2)
    rep["wait_dt"] = wait_info.get("dt")
    cell(lambda: _call(tools, "AgentUserInterface__send_message_to_user", content="Done."))
    rep["cells"] = cells
    rep["turns_done"] = env.turns_done()
    rep["hash_before_validate"] = env.state_hash()
    rep["validate"] = env.validate()
    rep["hash_after_validate"] = env.state_hash()
    rep["now_rel"] = env.now() - env.start_time
    rep["clamped_negative"] = env.env.time_manager.clamped_negative
    rep["n_events"] = len(env.env.event_log.list_view())
    if dump_state:
        with open(dump_state, "w", encoding="utf-8") as f:
            f.write(env.canonical_state())
    rep["checks"] = {"task_via_pull": rep["pull0_has_task"], "wait_le_60": rep["wait_dt"] is not None and 0 <= rep["wait_dt"] <= 60,
                     "turns_done_eq_1": rep["turns_done"] == 1, "no_hidden_tools": not rep["hidden_tools_present"],
                     "validate_keys": set(rep["validate"]) >= {"success", "rationale", "rationale_diag", "G", "agent_counts",
                                                               "oracle_counts", "n_oracle_writes", "exception"}}
    return rep


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--tid", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--gen-seconds", type=float, default=float(os.environ.get("G2_GEN_SECONDS", "1.0")))
    ap.add_argument("--script", action="store_true", help="scripted 3-cell determinism / API check (stub judge)")
    ap.add_argument("--list-tools", action="store_true")
    ap.add_argument("--json-out", default="")
    ap.add_argument("--dump-state", default="", help="--script: write the final canonical state JSON (what state_hash hashes)")
    a = ap.parse_args()
    if os.environ.get("PYTHONHASHSEED") != "0":
        print("[g2_env] WARNING: PYTHONHASHSEED != 0, App seeds (hash()) are not reproducible", file=sys.stderr)
    if a.list_tools:
        config, sj = load_scenario_json(a.tid)
        env = G2Env(sj, StubJudgeEngine(), gen_seconds=a.gen_seconds, tid=a.tid, seed=a.seed, config=config)
        for t in env.tools():
            print(t._public_name, "W" if t.write_operation else "R", [x.name for x in t.args])
        return
    rep = script_check(a.tid, a.seed, a.gen_seconds, a.dump_state)
    s = json.dumps(rep, indent=1, default=str, ensure_ascii=False)
    if a.json_out:
        with open(a.json_out, "w", encoding="utf-8") as f:
            f.write(s)
    print(s)


if __name__ == "__main__":
    main()
