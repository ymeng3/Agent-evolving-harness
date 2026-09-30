# two-layer smoke patch: three edits with one dependency
EDITS = [
    {"id": "e1", "capability": "ToolUse", "impl": "Code", "trigger": "any cell calling a paginated list API with page_index=0 only", "depends": []},
    {"id": "e2", "capability": "Memory", "impl": "State", "trigger": "after every executed cell", "depends": []},
    {"id": "e3", "capability": "Verification", "impl": "ControlFlow", "trigger": "first complete_task", "depends": ["e2"]},
]
def e1_post_parse(code, state):
    import re
    # harness-side pagination: if the model requests only page_index=0 of a list API and assigns the result, rewrite into a loop that collects all pages
    m = re.search(r"^(\w+)\s*=\s*(apis\.\w+\.\w+)\((.*?)page_index\s*=\s*0(.*?)\)\s*$", code, re.M)
    if not m: return code
    var, fn, pre, post = m.groups()
    loop = (f"{var} = []\nfor _pi in range(60):\n    _r = {fn}({pre}page_index=_pi{post})\n    if not _r: break\n    {var}.extend(_r if isinstance(_r, list) else [_r])\n")
    state["_e1_fired"] = state.get("_e1_fired", 0) + 1
    return code.replace(m.group(0), loop.rstrip(), 1)
def e2_post_exec(code, out, state):
    import re
    state.setdefault("mut", 0)
    if not out.startswith("Execution failed") and re.search(r"apis\.(?!api_docs|supervisor)\w+\.(create|update|delete|send|add|remove|pay|post|reply|move|archive|change|reset|cancel|renew|upload|order|buy|set|transfer|book|import|attach)\w*\(", code): state["mut"] += 1
def e3_pre_complete(code, state):
    if state.get("mut", 0) == 0 and not state.get("_e3_fired"):
        state["_e3_fired"] = 1
        return 'print("No state-changing API call has succeeded yet; make sure every required action of the task was actually performed before completing.")'
    return code
