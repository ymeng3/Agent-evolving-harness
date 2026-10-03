EDITS = [
    {"id": "e1", "capability": "Verification", "impl": "Prompt",
     "trigger": "every step (control for ANSWER_CHECK_H1: the same rule as always-on advice, not triggered by the D10 detector)", "depends": [],
     "expected_effect": "same content, no targeting", "side_effect_risk": "question tasks completed without their answer"},
]


def e1_pre_call(prompt, state):
    return prompt + ("\n\n[harness note] General advice: pass answer=... to apis.supervisor.complete_task only if the task asks a question; "
                     "for tasks that ask you to do something, call apis.supervisor.complete_task() with no answer (not an id or a confirmation sentence).")
