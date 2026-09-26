#!/usr/bin/env python3
"""KG-A LABEL SUPPLY: run the EXISTING, UNMODIFIED b2_smoke.smoke() over every candidate patch on
disk. Zero API calls. Records verdicts; NEVER repairs anything. Per-patch wall timeout so a
pathological candidate cannot hang the sweep (timeout is recorded as its own verdict, not dropped)."""
import json, os, sys, glob, hashlib, signal
sys.path.insert(0, "/net/scratch/ymeng3/bos_alfworld")
from b2_smoke import smoke

class TO(Exception): pass
def _h(s, f): raise TO()
signal.signal(signal.SIGALRM, _h)

pats = sorted(glob.glob("/net/scratch/ymeng3/bos_alfworld/patches*/**/*.py", recursive=True))
out = []
for p in pats:
    src = open(p).read()
    rel = os.path.relpath(p, "/net/scratch/ymeng3/bos_alfworld")
    rec = {"path": rel, "group": rel.split("/")[1] if "/" in rel.split("/", 1)[1] else rel.split("/")[0],
           "name": os.path.basename(p)[:-3], "sha": hashlib.sha256(src.encode()).hexdigest()[:16],
           "nbytes": len(src)}
    signal.alarm(5)
    try:
        r = smoke(src, rec["name"])
        rec.update({k: r[k] for k in ("smoke_verdict", "validator_ok", "exec_ok", "hooks_defined",
                                      "crashed_hooks", "never_invoked_hooks", "no_effect_hooks",
                                      "total_exceptions", "constants", "constants_in_range")})
        rec["final_state_keys"] = r.get("final_state_keys", [])
        rec["per_hook"] = r.get("per_hook", {})
    except TO:
        rec["smoke_verdict"] = "TIMEOUT"
    except Exception as e:
        rec["smoke_verdict"] = "HARNESS_ERROR"; rec["harness_error"] = f"{type(e).__name__}: {e}"
    finally:
        signal.alarm(0)
    out.append(rec)
json.dump(out, open("/net/scratch/ymeng3/bos_screens/hag/smoke_all.json", "w"), indent=1)
print("labelled", len(out), "patches")
