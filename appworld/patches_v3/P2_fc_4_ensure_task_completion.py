EDITS = [
    {
        "id": "e1",
        "capability": "ControlFlow",
        "impl": "ControlFlow",
        "trigger": "Cell 28 contains successfully placed order message",
        "depends": [],
        "expected_effect": "Automatically call the complete_task function after placing the order.",
        "side_effect_risk": "May complete the task prematurely if additional steps are required post-order."
    }
]

def e1_pre_complete(code, state):
    # Check the last execution result to see if the order was successfully placed
    last_cell = state.get('last_cell_execution', '')
    if "ORDER RESULT: {'message': 'Successfully placed the order." in last_cell:
        # Append the necessary call to complete the task
        return f"{code}\napis.supervisor.complete_task()"
    return code
