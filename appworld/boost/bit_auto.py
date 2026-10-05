"""Unattended driver for one BIT boosting round after the proposer job has been queued (no idle GPU between steps).
Steps: wait proposer -> screen -> branch build (base trees active) -> parallel branch run -> pooled estimate -> candidate-level active
sampling (4-rep rebuild for undecided candidates) -> admission (A26) -> validation arm queued -> wait -> readout -> summary file.
Runs on the server inside appworld/ (e.g. in a screen session):
  python boost/bit_auto.py --round R2 --base-specs bit/R2/base_tree1.json,bit/R2/base_tree2.json --base-val results/A.json,results/B.json"""
import argparse, glob, json, os, subprocess, sys, time

Q = "/root/autodl-tmp/cc/queue"; PAR = os.path.join(Q, "par_run.sh")


def log(msg, out):
    line = time.strftime("%F %T ") + msg; print(line, flush=True); open(out, "a").write(line + "\n")


def sh(cmd, out):
    log("$ " + cmd[:300], out); r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    open(out, "a").write((r.stdout or "")[-6000:] + (r.stderr or "")[-2000:] + "\n"); return r


def wait_history(pattern, n, out, poll=60):
    while True:
        h = open(os.path.join(Q, "history.tsv")).read()
        if h.count(pattern) >= n: return
        time.sleep(poll)


def run_par(jobs_txt, name, out, P=4):
    d = os.path.join(Q, "par_" + name); os.makedirs(d, exist_ok=True)
    for i, line in enumerate(open(jobs_txt).read().splitlines(), 1):
        if line.strip(): open(os.path.join(d, f"x{i:04d}_{line.split()[2]}.job"), "w").write(" ".join(line.split()[3:]) + "\n")
    sh(f"bash {PAR} {d} {P}", out)   # blocks until all jobs of the directory are done


def lowrank(builds, runs, instr, js, out):
    sh(f"python boost/bit_lowrank.py --builds {builds} --results results --runs {runs} --instr {instr} --json-out {js}", out)
    return json.load(open(js)) if os.path.exists(js) else []


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--round", required=True); ap.add_argument("--base-specs", required=True)
    ap.add_argument("--base-val", required=True); ap.add_argument("--instr", default="results/instructions_all100.json")
    ap.add_argument("--k-active", type=int, default=3); a = ap.parse_args()
    R = f"bit/{a.round}"; out = f"{R}/auto.log"; runs = open(f"{R}/runs.txt").read().strip(); env = f"{R}/base_env.txt"
    log(f"auto driver start: round {a.round}", out)
    wait_history(f"CC_BIT_{a.round}_propose_P2", 1, out); log("proposer done", out)
    sh(f"python boost/bit_screen.py --cands {R}/cands_P2.jsonl --runs {runs} --instr {a.instr} --tree {R}/tree.json --out {R}/screen.json", out)
    sh(f"python boost/bit_branch.py build --screen {R}/screen.json --cands {R}/cands_P2.jsonl --runs {runs} --instr {a.instr} --out {R}/branch "
       f"--round {a.round} --reps 2 --env-file {env} --base-specs {a.base_specs}", out)
    run_par(f"{R}/branch/jobs.txt", a.round, out); log("branch pass 1 done", out)
    rows = lowrank(f"{R}/branch", runs, a.instr, f"{R}/lowrank1.json", out)
    und = [r["cid"] for r in sorted(rows, key=lambda r: -(r["a_hi90"] - r["a_lo90"])) if 0.3 <= r["p_pos"] < 0.9 and r["states"] >= 4][:a.k_active]
    builds = f"{R}/branch"
    if und:   # candidate-level active sampling: 4 more reps for the undecided ones
        sc = json.load(open(f"{R}/screen.json")); sc["kept"] = und; json.dump(sc, open(f"{R}/screen_x4.json", "w"))
        sh(f"python boost/bit_branch.py build --screen {R}/screen_x4.json --cands {R}/cands_P2.jsonl --runs {runs} --instr {a.instr} "
           f"--out {R}/branch_x4 --round {a.round}X --reps 4 --env-file {env} --base-specs {a.base_specs}", out)
        run_par(f"{R}/branch_x4/jobs.txt", a.round + "X", out); builds += f",{R}/branch_x4"; log(f"active reps done for {und}", out)
    rows = lowrank(builds, runs, a.instr, f"{R}/lowrank.json", out)
    sc = {c["cid"]: c for c in json.load(open(f"{R}/screen.json"))["candidates"]}
    adm = [r for r in rows if r["p_pos"] >= 0.90 and r["a_bar"] > 0 and r["states"] >= 4 and not (sc.get(r["cid"]) or {}).get("memo_flag")]
    cands = {json.loads(l)["cid"]: json.loads(l) for l in open(f"{R}/cands_P2.jsonl")}
    json.dump({"rule": "A26 pooled", "admitted": [{"cid": r["cid"], "a_bar": r["a_bar"], "p_pos": r["p_pos"], "spec": cands[r["cid"]]["spec"]}
                                                  for r in adm]}, open(f"{R}/admitted.json", "w"), indent=1)
    log(f"admitted: {[r['cid'] for r in adm]}", out)
    if not adm: log("nothing admitted; round ends without a validation arm", out); return
    sh(f"python boost/bit_branch.py valarm --admitted {R}/admitted.json --round {a.round} --env-file {env} --base-specs {a.base_specs} "
       f"--base-val {a.base_val}", out)
    tag = f"CC_BIT_{a.round}_ADM_val"; cmd = open(env).read().split(" python ")[0].replace("tasks_challenge50.json", "tasks_challenge_val50.json")
    for s in (1, 2):
        open(os.path.join(Q, "pending", f"20261006-000000-1000000{s}_{tag}.job"), "w").write(
            f"{cmd} python bos_appworld_v3.py eval --patch patches_ccbit/{a.round}_ADMITTED.py --seed {s} --tag {tag} --workers 8\n")
    wait_history(tag, 2, out)
    sh(f"python boost/multi_metric_readout.py --base BASE={a.base_val} --arm {a.round}_ADM=results/{tag}_seed1.json,results/{tag}_seed2.json", out)
    log("round complete", out)


if __name__ == "__main__":
    main()
