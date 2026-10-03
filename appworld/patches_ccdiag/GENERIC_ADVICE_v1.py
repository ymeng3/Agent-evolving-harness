EDITS = [
    {"id": "e1", "capability": "Planning", "impl": "Prompt", "trigger": "every step (control: the same advice as RUBRIC_NUDGES_v1, always on, not triggered by any rubric detector)", "depends": [],
     "expected_effect": "same content, no targeting", "side_effect_risk": "over-constraining guidance"},
]


def e1_pre_call(prompt, state):
    state["step"] = state.get("step", -1) + 1
    left = 30 - state["step"]
    return prompt + (f"\n\n[harness note] General advice ({left} of 30 cells left): you may look up several APIs' docs in one cell and need not re-read specs you "
                     f"already know; do not repeat a documentation call whose output is above; process lists of items in one loop per cell; public search APIs "
                     f"take no access_token; amazon.place_order needs IDs from amazon.show_addresses / show_payment_cards; when almost out of cells, finish the "
                     f"state-changing calls and call apis.supervisor.complete_task().")
