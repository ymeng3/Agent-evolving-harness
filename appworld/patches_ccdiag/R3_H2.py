EDITS = [
    {"id": "e1", "capability": "Verification", "impl": "Prompt",
     "trigger": "rubric D10' answer on an action task: complete_task(answer=A) with A not None (checked at run time) and no question cue in the "
                "task (cues: a '?' outside quotes, 'tell me / let me know / give me / find out / how many / how much ...', or an opening "
                "interrogative word); blocks ONCE with the complete_task spec rule, the next call goes through unchanged",
     "depends": [], "expected_effect": "action tasks completed with answer=None (H1 disc: 4-5/8 losses, H2 disc: 3/13)",
     "side_effect_risk": "a question task without a cue loses one step"},
    {"id": "e2", "capability": "Verification", "impl": "Prompt",
     "trigger": "rubric D11 unchecked cart: amazon.place_order about to run and the episode never showed or cleared the cart "
                "(show_cart / clear_cart / clear_cart_first); blocks ONCE and prints the current cart, the next call goes through",
     "depends": [], "expected_effect": "no stale items ordered (H2 disc: 2/13 losses)", "side_effect_risk": "one extra step on amazon orders"},
]
# Round 3 (docs/design/diagnosis_2026-10-03/H2_disc_failures.md). The refined cue rule overlaps the val-informed A16 candidate (prereg A19).


def e1_setup():
    return '''
_cc_state = {"ans_warned": False}
def _cc_complete(*a, **k):
    ans = k.get("answer", a[0] if a else None)
    if ans is not None and not _cc_state["ans_warned"]:
        _cc_state["ans_warned"] = True
        print(f"[harness note] complete_task was NOT called yet. Its specification says: pass answer 'if and only if the task requests an "
              f"answer'; 'if the task is not a question ... the answer must be left to the default value, i.e., None'. This task asks you to do "
              f"something, and you passed answer={ans!r}. If the task is done, call apis.supervisor.complete_task() with no answer. "
              f"(If the task really asks for this value, call complete_task with it again.)")
        return None
    return apis.supervisor.complete_task(*a, **k)
'''


def e1_pre_call(prompt, state):
    if "_task" not in state:
        state["_task"] = prompt.split("Task:", 1)[1].strip() if "Task:" in prompt else ""
    return prompt


def e1_pre_complete(code, state):
    import re
    task = re.sub(r'"[^"]*"|“[^”]*”|(?<![A-Za-z])\'[^\']{1,200}\'(?![A-Za-z])', " ", state.get("_task", ""))
    cue = re.search(r"\?|\b(tell me|let me know|give me|find out|how many|how much|how long|what is|what are|what was|what's|which one)\b", task, re.I) \
        or re.match(r"\s*(what|which|who|whom|when|where|how|is|are|do|does|did|can|could|should|was|were)\b", task, re.I)
    if cue:
        return code
    return re.sub(r"apis\.supervisor\.complete_task\s*\(", "_cc_complete(", code)


def e2_setup():
    return '''
_cc_cart = {"warned": False}
def _cc_place_order(*a, **k):
    if not _cc_cart["warned"]:
        _cc_cart["warned"] = True
        try: cart = apis.amazon.show_cart(access_token=k.get("access_token"))
        except Exception as e: cart = f"(could not show the cart: {e})"
        print(f"[harness note] place_order was NOT executed yet: this episode never looked at the cart, which may still hold items from "
              f"before. Current cart: {cart}. If it holds exactly what the task needs, call place_order again; otherwise fix the cart first.")
        return None
    return apis.amazon.place_order(*a, **k)
'''


def e2_post_exec(code, out, state):
    import re
    if re.search(r"apis\.amazon\.(show_cart|clear_cart)\s*\(|clear_cart_first\s*=\s*True", code or ""):
        state["cart_seen"] = True


def e2_post_parse(code, state):
    import re
    if state.get("cart_seen") or re.search(r"apis\.amazon\.(show_cart|clear_cart)\s*\(|clear_cart_first\s*=\s*True", code):
        return code
    return re.sub(r"apis\.amazon\.place_order\s*\(", "_cc_place_order(", code)
