EDITS = [
    {"id": "e1", "capability": "Planning", "impl": "Prompt", "trigger": "every step (control: the same advice as RUBRIC_NUDGES_H1, always on, not triggered by any rubric detector)", "depends": [],
     "expected_effect": "same content, no targeting", "side_effect_risk": "over-constraining guidance"},
]


def e1_pre_call(prompt, state):
    return prompt + ("\n\n[harness note] General advice: look up several APIs in one cell (or use api_index(app_name) once per app) and call APIs you "
                     "already know without re-reading their spec; process lists of items in one loop per cell; amazon.place_order needs IDs from "
                     "amazon.show_addresses / show_payment_cards; when almost out of steps, finish the state-changing calls and call "
                     "apis.supervisor.complete_task().")
