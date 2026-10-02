"""CC-BOOST v2 blind semantic judge (prereg A2): local Codex CLI, one trajectory prefix + one criterion per call ->
{evidence_cell, present in {0,1}}. Two votes per item, a third only on disagreement or a failed vote; majority. The judge never sees
outcomes, goal checks, other criteria or weights. Any vote whose event stream shows a command execution is discarded. Votes are
cached on disk per (criterion, item, vote index), so re-runs and crashes do not re-pay for judging."""
import hashlib, json, os, random, shutil, subprocess, tempfile, threading, time
from concurrent.futures import ThreadPoolExecutor

MODEL = os.environ.get("JUDGE_MODEL", "gpt-5.6-luna"); EFFORT = os.environ.get("JUDGE_EFFORT", "high")
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["evidence_cell", "present"],
          "properties": {"evidence_cell": {"type": "integer", "minimum": -1, "maximum": 30}, "present": {"type": "integer", "minimum": 0, "maximum": 1}}}


def prompt(criterion, task, cells_text):
    return ("You are a strict, blind rater. Do NOT run any commands or read any files; everything you need is below.\n"
            "The trajectory shows the first cells of an LLM agent solving an AppWorld task (the code it executed and the first 200 characters of each output).\n"
            f"CRITERION: {criterion}\n"
            "Read every cell. First find the cell that best shows the criterion (evidence_cell, -1 if none). Then answer present = 1 if the criterion "
            "clearly holds in this trajectory, else 0. Return JSON {\"evidence_cell\": <int>, \"present\": <0|1>}. No explanations.\n\n"
            f"TASK: {task}\n{cells_text}")


class Judge:
    def __init__(self, cache_dir, workers=12):
        self.cache_dir = cache_dir; os.makedirs(cache_dir, exist_ok=True); self.workers = workers; self.lock = threading.Lock()
        self.work = tempfile.mkdtemp(prefix="ccjudge_")   # empty working dir: nothing but the schema and the judge's own outputs
        self.schema = os.path.join(self.work, "schema.json"); json.dump(SCHEMA, open(self.schema, "w"))
        self.exe = shutil.which("codex") or shutil.which("codex.cmd"); self.mock = os.environ.get("JUDGE_MOCK") == "1"
        self.stats = {"calls": 0, "failed": 0, "discarded_cmd": 0, "secs": 0.0}

    def _cache_path(self, criterion): return os.path.join(self.cache_dir, hashlib.sha1(criterion.encode()).hexdigest()[:16] + ".jsonl")

    def _load(self, criterion):
        p = self._cache_path(criterion); out = {}
        if os.path.exists(p):
            for line in open(p, encoding="utf-8"):
                try: d = json.loads(line); out[(d["item"], d["vote"])] = d
                except Exception: pass
        return out

    def _save(self, criterion, rec):
        with self.lock, open(self._cache_path(criterion), "a", encoding="utf-8") as f: f.write(json.dumps(rec) + "\n")

    def _call(self, text):
        """-> (present or None, evidence_cell or None)"""
        if self.mock:
            h = int(hashlib.sha1(text.encode()).hexdigest(), 16); return int(("page_index" in text) or h % 7 == 0), -1
        out = os.path.join(self.work, f"o_{threading.get_ident()}_{time.time_ns()}.json"); t0 = time.time()
        try:
            r = subprocess.run([self.exe, "exec", "--skip-git-repo-check", "--ephemeral", "-s", "read-only", "-m", MODEL, "-c", f'model_reasoning_effort="{EFFORT}"',
                                "--output-schema", self.schema, "-o", out, "--json", "-"], input=text, capture_output=True, text=True, encoding="utf-8",
                               timeout=600, cwd=self.work)
            with self.lock: self.stats["calls"] += 1; self.stats["secs"] += time.time() - t0
            if '"command_execution"' in r.stdout:
                with self.lock: self.stats["discarded_cmd"] += 1
                return None, None
            d = json.load(open(out, encoding="utf-8")); return int(d["present"]), int(d["evidence_cell"])
        except Exception:
            with self.lock: self.stats["failed"] += 1
            return None, None
        finally:
            if os.path.exists(out): os.remove(out)

    def score(self, criterion, items):
        """items: list of (item_key, task, cells_text). -> list of majority votes in {0,1} or None (unjudgeable), and per-item vote lists."""
        cached = self._load(criterion)
        def vote(job):
            key, task, cells, k = job
            if (key, k) in cached: return key, k, cached[(key, k)]["present"]
            p, cell = self._call(prompt(criterion, task, cells))
            if p is not None: self._save(criterion, {"item": key, "vote": k, "present": p, "cell": cell})
            return key, k, p
        votes = {key: {} for key, _, _ in items}
        with ThreadPoolExecutor(self.workers) as ex:
            for key, k, p in ex.map(vote, [(key, t, c, k) for key, t, c in items for k in (0, 1)]): votes[key][k] = p
            third = [(key, t, c, 2) for key, t, c in items if None in votes[key].values() or len(set(votes[key].values())) > 1]
            for key, k, p in ex.map(vote, third): votes[key][k] = p
        maj = []
        for key, _, _ in items:
            v = [x for x in votes[key].values() if x is not None]
            if not v or (len(v) == 2 and v[0] != v[1]): maj.append(None)   # no valid vote, or an unresolved tie
            else: maj.append(int(2 * sum(v) > len(v)))
        return maj, votes
