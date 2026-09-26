#!/usr/bin/env python3
"""CLOSED-LOOP DRIVER. Implements hag/CLOSED_LOOP_PREREG_v2.1.md (sha f02984c01c87d725) verbatim.
Two arms (naive, ours), T=5, K=4, n_val=96, finalist-only Credit V1, frozen stopping policy on candidate
validation, blind held-out test writer with NO reader, guards G1-G6. Resumable: state after every step.
--dry-run: builds prompts, computes Stage 0 on F_0, simulates scheduling with fabricated results,
makes ZERO API calls and ZERO sbatch submissions."""
import json, os, sys, re, time, math, random, hashlib, subprocess, glob, itertools
R = "/net/scratch/ymeng3/bos_alfworld"; H = "/net/scratch/ymeng3/bos_screens/hag"
sys.path.insert(0, R); sys.path.insert(0, H)
DRY = "--dry-run" in sys.argv
import ops6_prompts as O                      # menus, evidence blocks, DEDICATED prompts, ARTIFACT format
from scaling_census import units, drop
from b2_smoke import smoke
from bos_alfworld import validate_patch
if not DRY: from bos_alfworld import gpt4o

PREREG_SHA = "f02984c01c87d725"; T = int(os.environ.get("BOS_T", "5")); K = 4; NVAL = 96; BATCH = 9; Z = 1.0; F0_MARGIN = 2.0
GUARD_USD = "202"; PASS_CEIL = 2.47; CREDIT_CAP = 6; STAGE3_CAP = 1
VAL_MAN = f"{R}/slices/validation_train96.txt"; TEST_MAN = f"{R}/slices/test_validseen140.txt"
STATE = os.environ.get("BOS_STATE", f"{R}/closedloop_state.json"); ARMS = tuple(os.environ.get("BOS_ARMS", "naive,ours").split(","))  # namespace/arm selection (2026-09-20); defaults unchanged
PATCH_DIR = os.environ.get("BOS_PATCH_DIR", f"{R}/patches_loop"); MAN_DIR = os.environ.get("BOS_MAN_DIR", f"{R}/slices/batches"); BANK_DIR = f"{R}/banks"
PREFETCHED = set()   # tags whose passes were submitted speculatively (scheduler amendment 2026-09-20)
LOOKAHEAD = int(os.environ.get("BOS_LOOKAHEAD", "2"))   # scheduler v2: batches in flight beyond the consumed frontier
os.makedirs(PATCH_DIR, exist_ok=True); os.makedirs(MAN_DIR, exist_ok=True)
VAL_GAMES = [l.strip() for l in open(VAL_MAN) if l.strip()]; assert len(VAL_GAMES) == NVAL
SYS = ("You are a coding agent improving an LLM text-agent harness for embodied household tasks (ALFWorld). You may only change "
       "the harness through the hook API given below; the model, environment and scoring are fixed. Follow the output format exactly.")
F0_SRC = ""                                   # F_0 is the released harness: empty patch

def sha(s): return hashlib.sha256(s.encode()).hexdigest()[:16]
def STATIC(src):
    import ast as A, builtins
    B = set(dir(builtins))
    try: t = A.parse(src)
    except SyntaxError: return False
    mod = set()
    for n in t.body:
        if isinstance(n, A.Assign):
            for tg in n.targets:
                if isinstance(tg, A.Name): mod.add(tg.id)
        if isinstance(n, (A.Import, A.ImportFrom)):
            for a in n.names: mod.add((a.asname or a.name).split(".")[0])
        if isinstance(n, A.FunctionDef): mod.add(n.name)
    for fn in [n for n in t.body if isinstance(n, A.FunctionDef)]:
        loc = set(a.arg for a in fn.args.args) | set(mod)
        for n in A.walk(fn):
            if isinstance(n, (A.Import, A.ImportFrom)):
                for a in n.names: loc.add((a.asname or a.name).split(".")[0])
            if isinstance(n, A.Assign):
                for tg in n.targets:
                    if isinstance(tg, A.Name): loc.add(tg.id)
            if isinstance(n, A.For) and isinstance(n.target, A.Name): loc.add(n.target.id)
            if isinstance(n, (A.ListComp, A.GeneratorExp, A.SetComp, A.DictComp)):
                for g in n.generators:
                    for e in A.walk(g.target):
                        if isinstance(e, A.Name): loc.add(e.id)
            if isinstance(n, A.Lambda): loc.update(a.arg for a in n.args.args)
            if isinstance(n, A.ExceptHandler) and n.name: loc.add(n.name)
        for n in A.walk(fn):
            if isinstance(n, A.Name) and isinstance(n.ctx, A.Load) and n.id not in loc and n.id not in B: return False
    return True
def VALID(src): return bool(src) and validate_patch(src)[0] and STATIC(src) and smoke(src, "x")["smoke_verdict"] == "PASS"
def log(*a): print(time.strftime("%H:%M:%S"), *a, flush=True)
def load_state():
    if os.path.exists(STATE): return json.load(open(STATE))
    return {"prereg": PREREG_SHA, "round": 1, "arms": {a: {"F": {"src": F0_SRC, "name": "F0", "sha": sha(F0_SRC)},
            "memory": [], "archive": [], "history": [], "no_commit_streak": 0} for a in ARMS},
            "cache": {}, "spent": 0.0, "halted": None, "log": []}
def save_state(S): json.dump(S, open(STATE, "w"), indent=1)

# ---------------- SLURM plumbing (the only place jobs are submitted) ----------------
def submit(jobs, manifest, label):
    """jobs: list of (tag, patch_path_or_none, seed). Returns job id. Never reads TESTBLIND results."""
    jf = f"{R}/jobs_loop_{label}.txt"
    open(jf, "w").write("".join(f"{t} {p or 'none'} {s}\n" for t, p, s in jobs))
    if DRY: log("  [dry] would submit", label, len(jobs), "passes on", os.path.basename(manifest)); return f"DRY{label}"
    out = subprocess.check_output(["sbatch", "--parsable", f"--array=0-{len(jobs)-1}", "--time=04:00:00",
        f"--export=ALL,JOBS_FILE={jf},BOS_MANIFEST={manifest},BOS_GUARD_USD={GUARD_USD}", f"{R}/{os.environ.get('BOS_SBATCH', 'b2_run_aops08.sbatch')}"]).decode().strip()  # BOS_SBATCH=run_eval_local.sbatch routes the backbone to the self-hosted endpoint
    log("  submitted", label, out); return out
def wait(jobids):
    if DRY: return
    ids = [j for j in jobids if j]
    while True:
        q = subprocess.check_output(["squeue", "-h", "-u", "ymeng3", "-o", "%i"]).decode()
        if not any(j in q for j in ids): return
        time.sleep(90)
def ensure_result(tag, path, seed, manifest, label):
    """infra retry (2026-09-20): resubmit ONCE, unchanged, if the SLURM job died before writing its result."""
    if DRY or os.path.exists(f"{R}/results/{tag}_seed{seed}.json"): return
    log("  infra retry: missing result for", tag); wait([submit([(tag, path, seed)], manifest, f"{label}_retry")])
def result(tag, seed):
    """Reads a VALIDATION/echo result. Refuses TESTBLIND tags (G6)."""
    assert not tag.startswith("TESTBLIND_"), "G6: driver may not read held-out results"
    p = f"{R}/results/{tag}_seed{seed}.json"
    if DRY: return {"won": [random.Random(tag).random() < 0.4 for _ in range(BATCH)], "cost_usd": 0.15, "hook_effects": {"retry_calls": 100, "steps": 300, "prompt_changed": 0, "action_changed_by_parse": 0, "memory_calls": 0}, "calls": 400}
    return json.load(open(p))
def guard_pass_cost(S, d, ngames):
    S["spent"] += d.get("cost_usd", 0.0)
    full_equiv = d.get("cost_usd", 0.0) * (NVAL / max(ngames, 1))
    if full_equiv > PASS_CEIL: S["halted"] = f"G2 per-pass ceiling: {full_equiv:.2f} > {PASS_CEIL}"; save_state(S); raise SystemExit(S["halted"])

# ---------------- batch manifests for the stopping policy ----------------
def cand_order(tag): return random.Random(f"order:{tag}").sample(VAL_GAMES, NVAL)
def batch_manifest(tag, b):
    order = cand_order(tag); games = order[b*BATCH:(b+1)*BATCH]
    p = f"{MAN_DIR}/{tag}_b{b}.txt"; open(p, "w").write("\n".join(games) + "\n"); return p, games
def stats(wins):
    n = len(wins); p = sum(wins) / n if n else 0.0; se = math.sqrt(max(p*(1-p), 1e-9)/n) if n else 1.0
    return p, p - Z*se, p + Z*se

# ---------------- F_0 anchors on the validation slice ----------------
def f0_val():
    if DRY: return 0.40, {g: 1 if random.Random(g).random() < .4 else 0 for g in VAL_GAMES}
    ds = [json.load(open(f)) for f in sorted(glob.glob(f"{R}/results/F0VAL96_seed*.json"))]
    assert len(ds) >= 3, "F0VAL96 3 seeds required"
    games = [l.strip() for l in open(ds[0]["manifest"]) if l.strip()]
    mean = sum(d["success_rate"] for d in ds) / len(ds)
    per_game_s1 = dict(zip(games, [1 if w else 0 for w in [d for d in ds if d["seed"] == 1][0]["won"]]))
    return mean, per_game_s1

# ---------------- variation (evidence-routed, dedicated operator, structured artifact) ----------------
def evidence_blocks(arm, S, Fres):
    h = Fres["hook_effects"]; calls = max(Fres.get("calls", 1), 1)
    fail = ("EXECUTION EVIDENCE (current parent on the 96-game validation slice): retry_policy fired on %d of %d model calls (%.0f%%); "
            "parse_action changed the raw action %d times; format_prompt altered the prompt on %.1f%% of steps.\n"
            % (h["retry_calls"], calls, 100*h["retry_calls"]/calls, h["action_changed_by_parse"], 100*h["prompt_changed"]/max(h["steps"],1)))
    arch = S["arms"][arm]["archive"][-2:]
    comp = "" if len(arch) < 2 else ("TWO VALIDATED ENTRIES with distinct mechanisms:\n" + "".join(
        "  %s (%+.2f pp):\n```python\n%s\n```\n" % (e["name"], e["delta"], e["src"]) for e in arch))
    mem = ""
    if arm == "ours" and S["arms"][arm]["memory"]:
        mem = "PRIOR COMPONENT CREDIT (behavioural counterfactuals, earlier rounds):\n" + "".join(
            "  round %d  %-16s gamma %+.2f pp  closure %s  -> %s\n" % (m["round"], m["unit"], m["gamma"], "+".join(m["closure"]), m["decision"]) for m in S["arms"][arm]["memory"][-12:])
    elif S["arms"][arm]["history"]:
        mem = "CANDIDATE HISTORY:\n" + "".join("  round %d  %s  %+.2f pp  %s\n" % (x["round"], x["name"], x["delta"], x["decision"]) for x in S["arms"][arm]["history"][-8:])
    return fail, comp, mem
def route(arm, S, Fres):
    if os.environ.get("BOS_FORCE_OP"): return os.environ["BOS_FORCE_OP"]   # Loop-2 pilot: dedicated Compose every round
    h = Fres["hook_effects"]; calls = max(Fres.get("calls", 1), 1)
    if h["retry_calls"] / calls > 0.25: return "Repair"
    if len(S["arms"][arm]["archive"]) >= 2: return "Compose"
    if S["arms"][arm]["no_commit_streak"] >= 2: return "Explore"
    return "Induce"
MENU_ONE = {"Repair": O.DEDICATED["Repair"], "Contrast": O.DEDICATED["Contrast"], "Induce": O.DEDICATED["Induce"],
            "Compose": "TRANSFORMATION (mandatory): COMPOSE. Implement the two validated entries' mechanisms together in one patch so that they act jointly.",
            "Explore": "TRANSFORMATION (mandatory): EXPLORE. Introduce a mechanism not represented in the parent or the history, aimed at a failure the existing attempts do not address."}
TAGP = os.environ.get("BOS_TAG_PREFIX", "CL"); BLINDP = "" if TAGP == "CL" else TAGP + "_"   # Loop-2 namespace (default unchanged)
MENU_ONE["ComposePool"] = ("TRANSFORMATION: COMPOSE. Select at least two source mechanisms from the MECHANISM POOL (or one pool mechanism plus one mechanism you derive "
    "from a specific failure in the evidence) that have a reason to interact or complement each other, and implement their composition as one patch. "
    "Each constituent must remain an identifiable executable unit (a hook or constant). Do not add edits that are not part of the composition.")
ART_COMPOSE = ("Output format, exactly:\nDESIGN_INTENT: <one sentence>\nSOURCE_A: <pool entry name, or 'derived'>\nEVIDENCE_A: <which evidence lines>\n"
    "SOURCE_B: <pool entry name, or 'derived'>\nEVIDENCE_B: <which evidence lines>\nSOURCE_C: <optional>\nEVIDENCE_C: <optional>\n"
    "COMPOSITION_HYPOTHESIS: <why these constituents interact or complement each other; name the shared state or control flow>\n"
    "MECHANISM: <the hooks/constants you change and how>\nNAME: <short_snake_case>\n```python\n<patch module>\n```")
def pool_block(arm, S):
    """MECHANISM POOL = seed pool (env BOS_SEED_POOL json, identical for all arms) + this arm's validated candidates so far."""
    ents = []
    sp = os.environ.get("BOS_SEED_POOL")
    if sp and os.path.exists(sp): ents += [(e["name"], e["evidence"], e["src"]) for e in json.load(open(sp))]
    A = S["arms"][arm]
    for x in A["history"]:
        if x["name"] in ("none",) : continue
        p = f"{PATCH_DIR}/{x['name'].replace('_S','')}.py"
        if os.path.exists(p):
            g = [m for m in A["memory"] if m["round"] == x["round"]]
            ev = f"finalist round {x['round']}, validation delta vs parent {x['delta']:+.2f} pp, {x['decision']}" + ("; Credit: " + ", ".join(f"{m['unit']} gamma {m['gamma']:+.1f} ({m['decision']})" for m in g) if g else "")
            ents.append((x["name"], ev, open(p).read().strip()))
    if not ents: return "MECHANISM POOL: (empty at this round: derive both constituents from distinct failures in the evidence)\n"
    return "MECHANISM POOL (validated mechanisms with evidence; compose from these or derive one from the evidence):\n" + "".join(f"  [{n}] {e}\n```python\n{src}\n```\n" for n, e, src in ents[-8:])
def build_prompt(arm, S, Fres, op, attempt, names):
    import b2_prompts as BP, phasec_prompts as PC
    F = S["arms"][arm]["F"]; fail, comp, mem = evidence_blocks(arm, S, Fres)
    arch = ("ARCHIVE.\nThe archive's current entry, which your proposal descends from:\n\n```python\n" + (F["src"] or "# released harness: no patch") + "\n```\n")
    ev = fail + ("\n" + comp if op == "Compose" else "") + ("\n" + O.population_block() if op == "Induce" else "") + ("\n" + mem if mem else "")
    if op == "ComposePool": ev += "\n" + pool_block(arm, S)
    return (f"[proposal attempt {attempt}]\n" + BP.header() + "\n" + arch + "\n" + ev + "\n" + MENU_ONE[op] + "\n" + (ART_COMPOSE if op == "ComposePool" else O.ARTIFACT) + "\n"
            + PC.FOOT.replace("{names}", names) + PC.DESC_TASK)
FIELDS = {k: re.compile(k + r":\s*([^\n]+)") for k in ("DESIGN_INTENT", "MECHANISM", "EVIDENCE_USED")}
def propose(arm, S, Fres, op, t):
    bank = f"{BANK_DIR}/{TAGP}_{arm}_r{t}.json" if TAGP != "CL" else f"{BANK_DIR}/{arm}_r{t}.json"
    if os.path.exists(bank):
        cands = json.load(open(bank)); log(f"  {arm}: round-{t} bank REUSED from {os.path.basename(bank)} ({len(cands)} cands, generated before any round-{t} result)"); return cands
    cands, att = [], 0
    while len(cands) < K and att < 2*K:
        att += 1; user = build_prompt(arm, S, Fres, op, att, json.dumps([c["name"] for c in cands]))
        if DRY: src = "HISTORY_LENGTH = 10\n\ndef retry_policy(attempt, response, action, admissible, state):\n    return {'extra_instruction': 'pick an admissible action'} if attempt < 3 else None\n"; resp = "DESIGN_INTENT: x\nMECHANISM: retry_policy\nEVIDENCE_USED: y\nNAME: dry%d\n```python\n%s```" % (att, src)
        else:
            try: resp = gpt4o([{"role": "system", "content": SYS}, {"role": "user", "content": user}])
            except Exception as e:
                if "402" in str(e): raise SystemExit("FATAL 402")
                time.sleep(5); continue
        m = re.search(r"```(?:python)?\s*(.*?)```", resp, re.S); nm = re.search(r"NAME:\s*([A-Za-z0-9_\-]+)", resp)
        src = m.group(1).strip() if m else None
        if not VALID(src): continue
        name = f"{TAGP}_{arm[0].upper()}_r{t}_c{len(cands)+1}"; p = f"{PATCH_DIR}/{name}.py"; open(p, "w").write(src + "\n")
        cands.append({"name": name, "path": p, "src": src, "sha": sha(src), "op": op,
                      **{k: (rx.search(resp).group(1).strip() if rx.search(resp) else "") for k, rx in FIELDS.items()}})
    return cands

# ---------------- candidate validation with the frozen stopping policy (3a, 3b) ----------------
def validate_bank(S, cands, f0mean, label):
    """Returns (finalist or None, per-candidate {tag, wins:{game:0/1}}). Batches of 9; drop if UCB<best LCB or UCB<F0-2pp.
    SCHEDULER v2 (hag/SCHEDULER_AMENDMENT_v2.md): priority-aware bounded lookahead. Each alive candidate may have at most
    LOOKAHEAD batches in flight beyond its consumed frontier; frontier batches are awaited first; on elimination the
    candidate's in-flight batches are cancelled; results computed but not consumed are masked and never read."""
    alive = {c["name"]: {"c": c, "wins": {}, "b": 0, "he": {}, "calls": 0} for c in cands}; done = {}
    def acc(a, d):
        for k, v in d.get("hook_effects", {}).items(): a["he"][k] = a["he"].get(k, 0) + v
        a["calls"] += d.get("calls", 0)
    NB = (NVAL + BATCH - 1) // BATCH; pre = {}; jid = {}; consumed = set()
    def ensure(n, b):
        if (n, b) in jid or b >= NB: return
        if (n, b) not in pre: pre[(n, b)] = batch_manifest(n, b)
        jid[(n, b)] = submit([(f"{n}_b{b}", alive[n]["c"]["path"], 1)], pre[(n, b)][0], f"{label}_{n}_b{b}"); PREFETCHED.add(f"{n}_b{b}")
    def cancel(n):
        ids = [j for (m, b), j in jid.items() if m == n and f"{m}_b{b}" not in consumed and not str(j).startswith("DRY")]
        if ids: subprocess.call(["scancel"] + [str(j) for j in ids])
    while True:
        ready = {n: a for n, a in alive.items() if a["b"]*BATCH < NVAL}
        if not ready: break
        for n, a in ready.items():                      # frontier first, then bounded lookahead
            for k in range(LOOKAHEAD + 1): ensure(n, a["b"] + k)
        wait([jid[(n, a["b"])] for n, a in ready.items()])
        for n, a in ready.items():                      # infra retry, once, unchanged
            tag = f"{n}_b{a['b']}"
            if not DRY and not os.path.exists(f"{R}/results/{tag}_seed1.json"):
                log("  infra retry: missing result for", tag); wait([submit([(tag, a["c"]["path"], 1)], pre[(n, a["b"])][0], f"{label}_{tag}_retry")])
        mans = {n: pre[(n, a["b"])] for n, a in ready.items()}
        for n, a in ready.items():
            d = result(f"{n}_b{a['b']}", 1); consumed.add(f"{n}_b{a['b']}"); guard_pass_cost(S, d, len(mans[n][1])); acc(a, d)
            for g, w in zip(mans[n][1], d["won"]): a["wins"][g] = 1 if w else 0
            a["b"] += 1
        # elimination
        st_ = {n: stats(list(a["wins"].values())) for n, a in alive.items()}
        best_lcb = max(v[1] for v in st_.values())
        for n in list(alive):
            p, lcb, ucb = st_[n]
            if ucb < best_lcb - 1e-12 or ucb < f0mean - F0_MARGIN/100:
                done[n] = alive.pop(n); done[n]["eliminated"] = True; cancel(n)
        if len(alive) == 1: break
        # stability stop
        order = sorted(alive, key=lambda n: -st_[n][0])
        if len(alive) >= 2 and getattr(validate_bank, "prev", None) == order and st_[order[0]][1] > st_[order[1]][2]:
            break
        validate_bank.prev = order
    validate_bank.prev = None
    def mask_unconsumed():
        if DRY: return
        md = f"{R}/results/masked/{label}"; os.makedirs(md, exist_ok=True)
        for (n, b) in list(pre):
            tag = f"{n}_b{b}"; f = f"{R}/results/{tag}_seed1.json"
            if tag not in consumed and os.path.exists(f): os.replace(f, f"{md}/{tag}_seed1.json")
    if not alive: mask_unconsumed(); return None, {**done}
    # E3: complete the finalist to the full 96 (required evidence: all remaining batches at once, consumed in order)
    order = sorted(alive, key=lambda n: (-stats(list(alive[n]["wins"].values()))[0], n))
    fin = alive[order[0]]
    for n in alive:
        if n != order[0]: cancel(n)                     # non-finalist survivors: their lookahead is speculative waste now
    for b in range(fin["b"], NB): ensure(order[0], b)
    wait([jid[(order[0], b)] for b in range(fin["b"], NB)])
    while fin["b"]*BATCH < NVAL:
        b = fin["b"]; man, games = pre[(order[0], b)]
        ensure_result(f"{order[0]}_b{b}", fin["c"]["path"], 1, man, f"{label}_fin_b{b}")
        d = result(f"{order[0]}_b{b}", 1); consumed.add(f"{order[0]}_b{b}"); guard_pass_cost(S, d, len(games)); acc(fin, d)
        for g, w in zip(games, d["won"]): fin["wins"][g] = 1 if w else 0
        fin["b"] += 1
    mask_unconsumed()
    fin["finalist"] = True; return order[0], {**done, **alive}

def full96(tag, path, S, label):
    """Full-slice single pass (used for Credit probes and for F_t re-measurement). Cached by patch sha."""
    key = sha(open(path).read().strip()) if path else "F0"
    if key in S["cache"]: return S["cache"][key]
    if tag in PREFETCHED and (DRY or os.path.exists(f"{R}/results/{tag}_seed1.json")): pass   # already computed speculatively
    else: jid = submit([(tag, path, 1)], VAL_MAN, label); wait([jid]); ensure_result(tag, path, 1, VAL_MAN, label)
    d = result(tag, 1) if not DRY else {"won": [random.Random(tag).random() < .42 for _ in range(NVAL)], "cost_usd": 1.5, "hook_effects": {"retry_calls": 100, "steps": 300, "prompt_changed": 0, "action_changed_by_parse": 0, "memory_calls": 0}, "calls": 400}
    guard_pass_cost(S, d, NVAL)
    games = VAL_GAMES if DRY else [l.strip() for l in open(d["manifest"]) if l.strip()]
    rec = {"wins": dict(zip(games, [1 if w else 0 for w in d["won"]])), "hook_effects": d["hook_effects"], "calls": d.get("calls", 0)}
    S["cache"][key] = rec; save_state(S); return rec

# ---------------- commit rule (paired game bootstrap on the 96 games, seed 1 both sides) ----------------
def paired_lcb(wx, wf, n=3000, seed=20260916):
    games = [g for g in VAL_GAMES if g in wx and g in wf]; rng = random.Random(seed); ds = []
    for _ in range(n):
        idx = [rng.choice(games) for _ in games]; ds.append(100*(sum(wx[g] for g in idx) - sum(wf[g] for g in idx))/len(idx))
    ds.sort(); pt = 100*(sum(wx[g] for g in games) - sum(wf[g] for g in games))/len(games)
    return pt, ds[int(.025*n)]
def commits(wx, wf): pt, lcb = paired_lcb(wx, wf); return (pt > 0 and lcb > -F0_MARGIN), pt, lcb

# ---------------- Credit V1 on the finalist (frozen; cache; Stage3<=1; cap 6 probes) ----------------
def credit_v1(S, fin, t):
    src = fin["c"]["src"]; U, _ = units(src); Q_C = fin["wins"]; probes = 0
    S["cache"].setdefault(sha(src), {"wins": Q_C, "hook_effects": fin.get("he", {}), "calls": fin.get("calls", 0)})
    def V(s): return VALID(s)
    def rm(us):
        s = src
        for u in us: s = drop(s, u)
        return s
    clos = {}
    for u in U:
        if V(rm([u])): clos[u] = [u]; continue
        fixed = None
        for k in range(1, len(U)):
            for extra in itertools.combinations([x for x in U if x != u], k):
                if V(rm([u] + list(extra))): fixed = [u] + list(extra); break
            if fixed: break
        clos[u] = fixed or list(U)
    abl = {u: c for u, c in clos.items() if set(c) != set(U)}
    measured = {"C": Q_C}; gam = {}
    loo = [(u, c) for u, c in list(abl.items())[:max(CREDIT_CAP - 2, 0)]]     # exactly the LOO probes the sequential rule would run
    todo = []
    for u, c in loo:
        s_ = rm(c); p_ = f"{PATCH_DIR}/{fin['c']['name']}_loo_{u[:6]}.py"; open(p_, "w").write(s_ + "\n")
        if sha(s_) not in S["cache"]: todo.append((f"{fin['c']['name']}_loo_{u[:6]}", p_))
    if todo:
        wait([submit([(tg, p_, 1)], VAL_MAN, f"credit_r{t}_{tg}") for tg, p_ in todo])
        for tg, p_ in todo: ensure_result(tg, p_, 1, VAL_MAN, f"credit_r{t}_{tg}"); PREFETCHED.add(tg)
    for u, c in abl.items():
        if probes >= CREDIT_CAP - 2: break               # leave room for additivity + stage 3
        s = rm(c); p = f"{PATCH_DIR}/{fin['c']['name']}_loo_{u[:6]}.py"; open(p, "w").write(s + "\n")
        rec = full96(f"{fin['c']['name']}_loo_{u[:6]}", p, S, f"credit_r{t}"); probes += 1
        measured[u] = rec["wins"]; gam[u] = 100*(sum(Q_C.values()) - sum(rec["wins"].values()))/NVAL
    D = [u for u, g in gam.items() if g < 0]
    best_name, best_w = "C", Q_C
    for u in gam:
        if sum(measured[u].values()) > sum(best_w.values()): best_name, best_w = u, measured[u]
    joint = None
    if D:
        drops = sorted({x for u in D for x in abl[u]}); s = rm(drops); p = f"{PATCH_DIR}/{fin['c']['name']}_joint.py"; open(p, "w").write(s + "\n")
        if V(s) and probes < CREDIT_CAP:
            rec = full96(f"{fin['c']['name']}_joint", p, S, f"credit_r{t}"); probes += 1; joint = rec["wins"]
            if sum(joint.values()) > sum(best_w.values()): best_name, best_w = "joint", joint
            elif probes < CREDIT_CAP and STAGE3_CAP > 0:   # bounded repair: the single add-back with largest |gamma| not already measured
                for u in sorted(D, key=lambda u: -abs(gam[u])):
                    back = sorted(set(drops) - set(abl[u])); s2 = rm(back); k2 = sha(s2)
                    if k2 in S["cache"] or not V(s2): continue
                    p2 = f"{PATCH_DIR}/{fin['c']['name']}_add_{u[:6]}.py"; open(p2, "w").write(s2 + "\n")
                    rec = full96(f"{fin['c']['name']}_add_{u[:6]}", p2, S, f"credit_r{t}"); probes += 1
                    if sum(rec["wins"].values()) > sum(best_w.values()): best_name, best_w = "add_" + u, rec["wins"]
                    break
    # materialise S*
    if best_name == "C": s_src = src
    elif best_name == "joint": s_src = rm(sorted({x for u in D for x in abl[u]}))
    elif best_name.startswith("add_"): u = best_name[4:]; s_src = rm(sorted({x for v in D for x in abl[v]} - set(abl[u])))
    else: s_src = rm(abl[best_name])
    mem = [{"round": t, "unit": u, "gamma": round(g, 2), "closure": abl[u], "decision": "dropped" if (u in D and best_name != "C") else "kept"} for u, g in gam.items()]
    return {"src": s_src, "wins": best_w, "name": f"{fin['c']['name']}_S", "sha": sha(s_src), "gamma": gam, "probes": probes, "memory": mem,
            "hitchhikers_removed": len(D) if best_name != "C" else 0}

# ---------------- held-out test writer (G6: submit only, never read) ----------------
def blind_test(arm, S, t, seeds):
    F = S["arms"][arm]["F"]; p = None
    if F["src"]:
        p = f"{PATCH_DIR}/{F['name']}.py"; open(p, "w").write(F["src"] + "\n")
    submit([(f"TESTBLIND_{BLINDP}{arm}_F{t}", p, s) for s in seeds], TEST_MAN, f"testblind_{arm}_F{t}")

# ---------------- one round ----------------
def run_round(S, t, f0mean, f0wins):
    log(f"===== ROUND {t} =====")
    shared = None
    for arm in ARMS:
        A = S["arms"][arm]; F = A["F"]
        Fres = S["cache"].get(F["sha"]) or full96(f"{TAGP}_{arm[0].upper()}_r{t}_F", (f"{PATCH_DIR}/{F['name']}.py" if F["src"] else None), S, f"F_r{t}_{arm}")
        if F["src"] and not os.path.exists(f"{PATCH_DIR}/{F['name']}.py"): open(f"{PATCH_DIR}/{F['name']}.py", "w").write(F["src"] + "\n")
        if t == 1 and shared is not None: cands, res, fin_name = shared          # round-1 bank shared, validated once
        else:
            op = route(arm, S, Fres); cands = propose(arm, S, Fres, op, t); log(f"  {arm}: op={op} K={len(cands)}")
            fin_name, res = validate_bank(S, cands, f0mean, f"val_r{t}_{arm}")
            if t == 1: shared = (cands, res, fin_name)
        rec = {"round": t, "op": cands[0]["op"] if cands else None, "n_cands": len(cands), "finalist": fin_name, "commit": False, "salvage": False}
        if fin_name is None:
            A["no_commit_streak"] += 1; A["history"].append({"round": t, "name": "none", "delta": 0.0, "decision": "no_finalist"}); rec["no_finalist"] = True
        else:
            fin = res[fin_name]; Fw = Fres["wins"]
            if arm == "naive":
                ok, pt, lcb = commits(fin["wins"], Fw); rec.update(pt=pt, lcb=lcb, commit=ok)
                if ok:
                    A["F"] = {"src": fin["c"]["src"], "name": fin_name, "sha": fin["c"]["sha"]}; A["archive"].append({"name": fin_name, "delta": pt, "src": fin["c"]["src"]}); A["no_commit_streak"] = 0
                    S["cache"][fin["c"]["sha"]] = {"wins": fin["wins"], "hook_effects": fin["he"], "calls": fin["calls"]}
                else: A["no_commit_streak"] += 1
                A["history"].append({"round": t, "name": fin_name, "delta": pt, "decision": "committed" if ok else "rejected"})
            else:
                okC, ptC, _ = commits(fin["wins"], Fw)
                cr = credit_v1(S, fin, t); rec.update(probes=cr["probes"], gamma=cr["gamma"], hitchhikers=cr["hitchhikers_removed"])
                ok, pt, lcb = commits(cr["wins"], Fw); rec.update(pt=pt, lcb=lcb, commit=ok, salvage=(ok and not okC))
                A["memory"].extend(cr["memory"])
                if ok:
                    A["F"] = {"src": cr["src"], "name": cr["name"], "sha": cr["sha"]}; A["archive"].append({"name": cr["name"], "delta": pt, "src": cr["src"]}); A["no_commit_streak"] = 0
                    if cr["sha"] not in S["cache"]: S["cache"][cr["sha"]] = {"wins": cr["wins"], "hook_effects": fin["he"], "calls": fin["calls"]}
                else: A["no_commit_streak"] += 1
                A["history"].append({"round": t, "name": cr["name"], "delta": pt, "decision": "committed" if ok else "rejected"})
        S["log"].append({"arm": arm, **rec}); save_state(S)
        blind_test(arm, S, t, [1] if t < T else [4, 5, 6])       # G6: written, never read
        log(f"  {arm}: round {t} done; cumulative ${S['spent']:.2f}")     # G3

if __name__ == "__main__":
    assert open(f"{H}/CLOSED_LOOP_PREREG.sha").read().strip() == PREREG_SHA, "PREREG SHA DRIFT"
    S = load_state()
    if S.get("halted"): raise SystemExit("halted: " + S["halted"])
    f0mean, f0wins = f0_val(); S["cache"].setdefault(sha(F0_SRC), {"wins": f0wins, "hook_effects": {"retry_calls": 0, "steps": 1, "prompt_changed": 0, "action_changed_by_parse": 0, "memory_calls": 0}, "calls": 1})
    while S["round"] <= T:                                                    # G5
        run_round(S, S["round"], f0mean, f0wins); S["round"] += 1; save_state(S)
    if not DRY and os.environ.get("BOS_SKIP_F0_BLIND") != "1": submit([("TESTBLIND_F0", None, s) for s in (5, 6)], TEST_MAN, "testblind_F0_extra")   # F_0 to 3 seeds at the end
    log("LOOP COMPLETE. Unblinding is a separate, registered event.")
