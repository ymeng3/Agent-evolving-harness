EDITS = [
    {"id": "e1", "capability": "Verification", "impl": "Prompt",
     "trigger": "rubric D10 'answer on an action task': complete_task(answer=A) where the task has no question cue and A is an id returned by "
                "an earlier successful state-changing call, or a sentence (> 8 words). Checked at run time inside the sandbox (A may be a "
                "variable); blocks ONCE with a grounded note, the agent's next complete_task goes through unchanged.",
     "depends": [], "expected_effect": "action tasks completed with no answer (diagnosis H1 disc s1: 4-5 of 8 failures)",
     "side_effect_risk": "a question task misclassified as an action task loses one step (the second call goes through)"},
]
# Designed on discovery (docs/design/diagnosis_2026-10-03/H1_disc_s1_failures.md); tested on validation only (prereg A15).


def e1_setup():
    return '''
_cc_state = {"warned": False}
def _cc_complete(*a, _cc_ids=(), **k):
    ans = k.get("answer", a[0] if a else None)
    why = ""
    if ans is not None and not _cc_state["warned"]:
        if str(ans).strip() in set(str(x) for x in _cc_ids): why = f"{ans!r} is an id returned by one of your own state-changing calls"
        elif isinstance(ans, str) and len(ans.split()) > 8: why = "it is a sentence"
    if why:
        _cc_state["warned"] = True
        print(f"[harness note] complete_task was NOT called yet: this task asks you to DO something, not to answer a question, and the answer you "
              f"passed is not a requested value ({why}). Action tasks are graded with no answer. If the task is done, call "
              f"apis.supervisor.complete_task() with no answer now. (If the task really asks for this value, call complete_task with it again.)")
        return None
    return apis.supervisor.complete_task(*a, **k)
'''


def e1_pre_call(prompt, state):
    if "_task" not in state:
        state["_task"] = prompt.split("Task:", 1)[1].strip() if "Task:" in prompt else ""
    return prompt


def e1_post_exec(code, out, state):
    import re
    w = re.compile(r"apis\.(?!api_docs|supervisor)[a-z_]+\.(create|add|update|delete|remove|send|post|place|like|follow|move|mark|reply|pay|"
                   r"request|approve|deny|set|play|upload|rate|review|cancel|return|transfer|book)[a-z_]*\s*\(")
    if w.search(code or "") and not (out or "").startswith("Execution failed"):
        ids = state.setdefault("ids", [])
        for v in re.findall(r"""['"][a-z_]*_id['"]\s*:\s*(\d+)""", out or ""):
            if v not in ids: ids.append(v)


def e1_pre_complete(code, state):
    import re
    task = state.get("_task", "")
    if re.search(r"\?|\b(tell me|let me know|what|how many|how much|which|who|whom|when|where|find out|give me|report|answer)\b", task, re.I):
        return code   # question cue: never interfere
    ids = state.get("ids", [])
    return re.sub(r"apis\.supervisor\.complete_task\s*\(", "_cc_complete(_cc_ids=" + repr(ids) + ", ", code)
