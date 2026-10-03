EDITS = [
    {"id": "e1", "capability": "Planning", "impl": "Prompt",
     "trigger": "exactly once, at the first live step after a replayed prefix (the state where a rubric detector fired in the logged run); "
                "the note text comes per task from BOS_HINTS (built by boost/branch_build.py)",
     "depends": [], "expected_effect": "estimates the local effect a_k of ONE nudge at its firing state (MATH_FORMALIZATION sections 2, 4)",
     "side_effect_risk": "none beyond the nudge itself"},
]


def e1_pre_call(prompt, state):
    if state.get("_hint") and not state.get("_b_done") and state.get("_step") == state.get("_replay_len"):
        state["_b_done"] = True
        return prompt + "\n\n[harness note] " + state["_hint"]
    return prompt
