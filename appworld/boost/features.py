"""CC-BOOST v2 programmatic rubric candidates (prereg A2): a fixed feature grammar over the first L cells, no LLM.
Vocabulary (apps / API names) is fixed from the DISCOVERY set and reused unchanged on validation."""
import collections, math, re
import numpy as np

API = re.compile(r"apis\.([a-z_]+)\.([a-z_]+)\s*\(")
DOC_APP = re.compile(r"app_name\s*=\s*['\"]([a-z_]+)['\"]")
META_APPS = {"api_docs", "supervisor"}
AUTH = {"login", "logout", "signup", "show_account", "show_profile", "send_verification_code", "verify_account", "send_password_reset_code",
        "reset_password", "delete_account", "update_account_name"}
BASE_DESC = {
    "err_count": "number of failed cells", "err_streak": "longest run of consecutive failed cells", "err_after_err": "failed cells right after a failed cell",
    "docs_cells": "cells that query api_docs", "docs_unused_lookups": "api_docs lookups about apps never called with a task API",
    "docs_unused_apps": "apps looked up in api_docs but never called with a task API", "distinct_apps": "distinct apps called with a task API",
    "work_calls": "task API calls (not docs, auth or supervisor)", "first_work_cell": "index of the first cell with a task API call (L if none)",
    "auth_calls": "login/account API calls", "supervisor_calls": "supervisor API calls other than complete_task", "repeat_max": "most repeats of one identical cell",
    "distinct_cell_rate": "fraction of distinct cells", "empty_out": "cells whose output is empty, None, [] or {}", "err_kw_out": "outputs mentioning an exception or error",
    "pagination": "uses page_index / pagination", "loop_cells": "cells containing a for/while loop", "early_work": "task API calls in the first 5 cells",
    "late_work": "task API calls in the last 5 cells of the prefix", "code_len": "mean characters per cell", "print_only": "cells that only print/inspect a variable",
}


def _calls(code): return [(a, f) for a, f in API.findall(code)]


def base_feats(cells, L):
    n = max(1, len(cells)); f = {}
    errs = [bool(c["error"]) for c in cells]; f["err_count"] = sum(errs)
    best = cur = 0
    for e in errs: cur = cur + 1 if e else 0; best = max(best, cur)
    f["err_streak"] = best; f["err_after_err"] = sum(1 for a, b in zip(errs, errs[1:]) if a and b)
    used, doc_apps, docs_unused, work, auth, sup, first, early, late = set(), [], 0, 0, 0, 0, L, 0, 0
    for k, c in enumerate(cells):
        cs = _calls(c["code"]); w = [(a, x) for a, x in cs if a not in META_APPS and x not in AUTH]
        if "api_docs" in c["code"]: doc_apps += DOC_APP.findall(c["code"])
        work += len(w); auth += sum(1 for a, x in cs if x in AUTH); sup += sum(1 for a, x in cs if a == "supervisor" and x != "complete_task")
        used.update(a for a, _ in w)
        if w and first == L: first = k
        if k < 5: early += len(w)
        if k >= n - 5: late += len(w)
    f["docs_cells"] = sum(1 for c in cells if "api_docs" in c["code"]); f["docs_unused_lookups"] = sum(1 for a in doc_apps if a not in used)
    f["docs_unused_apps"] = len(set(doc_apps) - used); f["distinct_apps"] = len(used); f["work_calls"] = work; f["first_work_cell"] = first
    f["auth_calls"] = auth; f["supervisor_calls"] = sup
    norm = collections.Counter(" ".join(c["code"].split()) for c in cells); f["repeat_max"] = max(norm.values()) if norm else 0
    f["distinct_cell_rate"] = len(norm) / n
    f["empty_out"] = sum(1 for c in cells if c["out"].strip() in ("", "None", "[]", "{}"))
    f["err_kw_out"] = sum(1 for c in cells if re.search(r"exception|error", c["out"], re.I))
    f["pagination"] = int(any("page_index" in c["code"] for c in cells)); f["loop_cells"] = sum(1 for c in cells if re.search(r"\b(for|while)\b", c["code"]))
    f["early_work"] = early; f["late_work"] = late; f["code_len"] = sum(len(c["code"]) for c in cells) / n
    f["print_only"] = sum(1 for c in cells if re.fullmatch(r"\s*print\([A-Za-z_][A-Za-z0-9_\[\]'\". ]*\)\s*", c["code"]) is not None)
    return f


def vocab(recs, min_frac=0.05):
    """apps / API names used (as task calls) in >= min_frac of discovery trajectories."""
    app_c, api_c = collections.Counter(), collections.Counter()
    for r in recs:
        cs = [x for c in r["cells"] for x in _calls(c["code"])]
        app_c.update({a for a, x in cs if a not in META_APPS}); api_c.update({x for a, x in cs if a not in META_APPS and x not in AUTH})
    k = min_frac * len(recs)
    return sorted(a for a, v in app_c.items() if v >= k), sorted(x for x, v in api_c.items() if v >= k)


def pool(recs, L, voc, behavior_only=False):
    """-> (names, descriptions, matrix n x m). Counts are log1p-transformed; rates kept as is.
    behavior_only drops the per-app / per-API counts, which encode WHICH task it is rather than how the agent behaves (prereg A4)."""
    apps, apis = voc; rows = []
    for r in recs:
        f = base_feats(r["cells"], L); cs = [x for c in r["cells"] for x in _calls(c["code"])]
        if not behavior_only:
            for a in apps: f[f"app_{a}"] = sum(1 for aa, x in cs if aa == a and x not in AUTH)
            for x in apis: f[f"api_{x}"] = sum(1 for aa, xx in cs if xx == x and aa not in META_APPS)
        rows.append(f)
    names = list(rows[0].keys()) if rows else []
    desc = {**BASE_DESC, **{f"app_{a}": f"task API calls to the {a} app" for a in apps}, **{f"api_{x}": f"calls to the {x} API" for x in apis}}
    rate = {"distinct_cell_rate", "code_len"}
    M = np.array([[float(r[k]) if k in rate else math.log1p(max(0.0, float(r[k]))) for k in names] for r in rows], dtype=float).reshape(len(rows), len(names))
    return names, [desc.get(k, k) for k in names], M
