"""Cached LLM judge engine for Gaia2 (ARE) validation (plan U3).

ARE's judges call engine(messages, additional_trace_tags=[...]) -> (text, metadata) (validation/judge.py,
validation/utils/llm_utils.py) and parse [[Success]]/[[Failure]] (or [[True]]/[[False]]) out of the text.
Validation runs online inside env.tick(), so replays only reproduce verdicts if the judge is deterministic:
CachedJudgeEngine serves every repeated prompt from a persistent on-disk cache (key = sha256 of
json{model, messages, temperature, max_tokens, think}; atomic writes to <dir>/<k[:2]>/<k>.json).
Thinking off (chat_template_kwargs.enable_thinking=False) unless think=True, temperature 0, <think> stripped.
Failures (exhausted retries) raise and are never cached.

env: G2_JUDGE_BASE_URL / G2_JUDGE_MODEL / G2_JUDGE_KEY (fallback BOS_BASE_URL / BOS_MODEL / BOS_API_KEY, then the
file /root/autodl-tmp/vllm_api_key), G2_JUDGE_CACHE, G2_JUDGE_MAX_TOKENS (1024), G2_JUDGE_THINK (0),
G2_JUDGE_TIMEOUT (BOS_TIMEOUT, else 120).
Local: py gaia2/g2_judge.py --selftest (fake client, no network). Server: python g2_judge.py --live (one call)."""
import hashlib, json, os, re, sys, tempfile, threading, time

try:  # subclass ARE's base when importable so isinstance checks / model_name behave as for LiteLLMEngine
    from are.simulation.agents.llm.llm_engine import LLMEngine, LLMEngineException
except Exception:  # ARE absent (local tests): same call signature as are.simulation.agents.llm.llm_engine
    class LLMEngineException(Exception):
        def __init__(self, message, inner_exception=None):
            super().__init__(message)
            self.inner_exception = inner_exception

    class LLMEngine:
        def __init__(self, model_name):
            self._model_name = model_name

        @property
        def model_name(self):
            return self._model_name

        def __call__(self, messages, stop_sequences=[], **kwargs):
            return self.chat_completion(messages, stop_sequences, **kwargs)

        def chat_completion(self, messages, stop_sequences=[], **kwargs):
            raise NotImplementedError()

        def simple_call(self, prompt):
            raise NotImplementedError()

KEY_FILE = "/root/autodl-tmp/vllm_api_key"
SERVER_CACHE = "/root/autodl-tmp/cc/gaia2/judge_cache"
RETRIES = 6  # retries after the first attempt; backoff 2,4,8,16,30,30 s
_THINK_RE = re.compile(r"<think>.*?</think>", re.S)


def strip_think(text):
    """Drop <think>...</think> blocks and any leading reasoning ended by a bare </think> (Qwen templates that
    pre-open the think tag); an unterminated <think> (truncated reasoning) is cut off."""
    if text is None:
        return None
    s = _THINK_RE.sub("", text)
    if "</think>" in s:
        s = s.rsplit("</think>", 1)[1]
    if "<think>" in s:
        s = s.split("<think>", 1)[0]
    return s.strip()


def cache_key(model, messages, temperature, max_tokens, think):
    blob = json.dumps({"model": model, "messages": messages, "temperature": temperature,
                       "max_tokens": max_tokens, "think": bool(think)}, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class CachedJudgeEngine(LLMEngine):
    def __init__(self, model, base_url, api_key, cache_dir, temperature=0.0, max_tokens=1024, think=False,
                 client=None, timeout=120.0, retries=RETRIES):
        super().__init__(model)
        self.model, self.cache_dir = model, cache_dir
        self.temperature, self.max_tokens, self.think = float(temperature), int(max_tokens), bool(think)
        self.retries, self.hits, self.misses = int(retries), 0, 0
        self._lock = threading.Lock()
        if client is None:
            from openai import OpenAI  # lazy: local selftest runs without the openai package
            client = OpenAI(api_key=api_key or "EMPTY", base_url=base_url, timeout=float(timeout), max_retries=0)
        self.client = client
        os.makedirs(cache_dir, exist_ok=True)

    def _path(self, k):
        return os.path.join(self.cache_dir, k[:2], k + ".json")

    def _load(self, k):
        try:
            with open(self._path(k), encoding="utf-8") as f:
                rec = json.load(f)
            return rec if isinstance(rec.get("response"), str) else None
        except (OSError, ValueError, AttributeError):
            return None  # missing or corrupt -> miss (rewritten atomically below)

    def _store(self, k, rec):
        d = os.path.dirname(self._path(k))
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, prefix=".tmp_", suffix=".json")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(rec, f, ensure_ascii=False)
            os.replace(tmp, self._path(k))
        except BaseException:
            try: os.unlink(tmp)
            except OSError: pass
            raise

    def chat_completion(self, messages, stop_sequences=[], **kw):
        # kw carries additional_trace_tags (["judge"] / ["judge_llm"]); it does not change the answer, so not keyed
        msgs = [dict(m) for m in messages]
        k = cache_key(self.model, msgs, self.temperature, self.max_tokens, self.think)
        rec = self._load(k)
        if rec is not None:
            with self._lock: self.hits += 1
            return rec["response"], {"cached": True, "key": k, "model": self.model}
        req = dict(model=self.model, messages=msgs, temperature=self.temperature, max_tokens=self.max_tokens,
                   extra_body={"chat_template_kwargs": {"enable_thinking": self.think}})
        if stop_sequences: req["stop"] = list(stop_sequences)
        err = None
        for i in range(self.retries + 1):
            try:
                r = self.client.chat.completions.create(**req)
                raw = r.choices[0].message.content
                if raw is None: raise ValueError("empty completion (content=None)")
                break
            except Exception as e:  # never cached; after the last retry the caller sees the exception
                err = e
                if i < self.retries: time.sleep(min(2 ** (i + 1), 30))
        else:
            raise LLMEngineException(f"judge call failed after {self.retries + 1} attempts: {err!r}", err)
        text = strip_think(raw)
        usage = getattr(r, "usage", None)
        usage = {a: getattr(usage, a, None) for a in ("prompt_tokens", "completion_tokens")} if usage is not None else None
        self._store(k, {"key": k, "model": self.model, "temperature": self.temperature, "max_tokens": self.max_tokens,
                        "think": self.think, "messages": msgs, "response": text, "raw": raw, "usage": usage,
                        "t": time.time()})
        with self._lock: self.misses += 1
        return text, {"cached": False, "key": k, "model": self.model, "usage": usage}

    def simple_call(self, prompt):
        return self.chat_completion([{"role": "user", "content": prompt}])[0]


def _read_key():
    k = os.environ.get("G2_JUDGE_KEY") or os.environ.get("BOS_API_KEY")
    if k: return k
    try:
        with open(KEY_FILE, encoding="utf-8") as f: return f.read().strip()
    except OSError:
        return None


def judge_engine_from_env(client=None):
    base_url = os.environ.get("G2_JUDGE_BASE_URL") or os.environ.get("BOS_BASE_URL")
    model = os.environ.get("G2_JUDGE_MODEL") or os.environ.get("BOS_MODEL")
    if not model or (client is None and not base_url):
        raise RuntimeError("judge: set G2_JUDGE_BASE_URL/G2_JUDGE_MODEL (or BOS_BASE_URL/BOS_MODEL)")
    cache = os.environ.get("G2_JUDGE_CACHE") or (SERVER_CACHE if os.path.isdir("/root/autodl-tmp")
                                                 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "judge_cache"))
    return CachedJudgeEngine(model, base_url, _read_key(), cache,
                             max_tokens=int(os.environ.get("G2_JUDGE_MAX_TOKENS", "1024")),
                             think=os.environ.get("G2_JUDGE_THINK", "0") == "1",
                             timeout=float(os.environ.get("G2_JUDGE_TIMEOUT") or os.environ.get("BOS_TIMEOUT") or 120),
                             client=client)


def _selftest():
    import shutil
    from types import SimpleNamespace as NS

    class Fake:
        def __init__(self, replies):
            self.replies, self.calls = list(replies), []
            self.chat = NS(completions=NS(create=self.create))

        def create(self, **req):
            self.calls.append(req)
            x = self.replies.pop(0)
            if isinstance(x, Exception): raise x
            return NS(choices=[NS(message=NS(content=x))], usage=NS(prompt_tokens=10, completion_tokens=3))

    d = tempfile.mkdtemp(prefix="g2judge_")
    try:
        msgs = [{"role": "system", "content": "judge"}, {"role": "user", "content": "did it work?"}]
        fk = Fake(["<think>x</think>[[Failure]]"])
        e = CachedJudgeEngine("m", None, None, d, client=fk, retries=0)
        a = e(msgs, additional_trace_tags=["judge"])
        b = e(msgs, additional_trace_tags=["judge_llm"])
        assert a[0] == b[0] == "[[Failure]]", (a, b)
        assert (e.misses, e.hits, len(fk.calls)) == (1, 1, 1), (e.misses, e.hits, len(fk.calls))
        assert a[1]["cached"] is False and b[1]["cached"] is True
        req = fk.calls[0]
        assert req["temperature"] == 0.0 and req["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
        assert "stop" not in req
        k = cache_key("m", msgs, 0.0, 1024, False)
        assert os.path.isfile(os.path.join(d, k[:2], k + ".json")) and a[1]["key"] == k
        assert not [f for _, _, fs in os.walk(d) for f in fs if f.startswith(".tmp_")]
        # survives a new instance; different settings / prompt -> different key
        e2 = CachedJudgeEngine("m", None, None, d, client=Fake([]), retries=0)
        assert e2(msgs)[0] == "[[Failure]]" and (e2.hits, e2.misses) == (1, 0)
        assert cache_key("m", msgs, 0.0, 1024, True) != k and cache_key("m2", msgs, 0.0, 1024, False) != k
        # think=True flips the template flag
        f3 = Fake(["[[Success]]"])
        CachedJudgeEngine("m", None, None, d, client=f3, think=True, retries=0)(msgs)
        assert f3.calls[0]["extra_body"]["chat_template_kwargs"]["enable_thinking"] is True
        # failures are never cached; a later success is
        m2 = [{"role": "user", "content": "other"}]
        f4 = Fake([RuntimeError("boom")])
        e4 = CachedJudgeEngine("m", None, None, d, client=f4, retries=0)
        try:
            e4(m2); raise AssertionError("expected failure")
        except LLMEngineException:
            pass
        k2 = cache_key("m", m2, 0.0, 1024, False)
        assert not os.path.exists(os.path.join(d, k2[:2], k2 + ".json")) and (e4.hits, e4.misses) == (0, 0)
        # retries recover (content=None counts as failure); backoff patched out
        real_sleep, time.sleep = time.sleep, lambda s: None
        try:
            f5 = Fake([RuntimeError("drop"), None, "[[True]]"])
            e5 = CachedJudgeEngine("m", None, None, d, client=f5, retries=6)
            assert e5(m2)[0] == "[[True]]" and len(f5.calls) == 3 and e5.misses == 1
        finally:
            time.sleep = real_sleep
        # strip variants
        assert strip_think("reasoning...\n</think>\n\n[[Success]]") == "[[Success]]"
        assert strip_think("<think>a</think>A<think>b</think> [[True]] ") == "A [[True]]"
        assert strip_think("<think>unterminated") == "" and strip_think("[[False]]") == "[[False]]"
        # env factory with injected client
        os.environ.update(G2_JUDGE_MODEL="envm", G2_JUDGE_CACHE=d)
        ee = judge_engine_from_env(client=Fake([]))
        assert ee.model_name == "envm" and ee.cache_dir == d and ee.think is False and ee.max_tokens == 1024
        print("g2_judge selftest OK (base=%s)" % LLMEngine.__module__)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def _live():
    e = judge_engine_from_env()
    msgs = [{"role": "system", "content": "You are a strict judge. Answer with exactly [[Success]] or [[Failure]]."},
            {"role": "user", "content": "Task: send Bob the word 'hello'. Agent sent Bob: 'hello'. Did the agent succeed?"}]
    t = time.time()
    text, meta = e(msgs, additional_trace_tags=["judge"])
    print(json.dumps({"text": text, "meta": meta, "hits": e.hits, "misses": e.misses, "sec": round(time.time() - t, 2),
                      "base": LLMEngine.__module__, "cache": e.cache_dir}, ensure_ascii=False))


if __name__ == "__main__":
    if "--selftest" in sys.argv: _selftest()
    elif "--live" in sys.argv: _live()
    else: print(__doc__)
