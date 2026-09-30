EDITS = [
    {
        "id": "e1",
        "capability": "Planning",
        "impl": "ControlFlow",
        "trigger": "After adding all items to the cart and before a complete_task call.",
        "depends": [],
        "expected_effect": "Ensure apis.supervisor.complete_task() is called after adding products to the cart.",
        "side_effect_risk": "Minimal. It forces completion only if the harness failed to handle it initially."
    }
]

def e1_pre_complete(code, state):
    # Check if the last operation involved adding to cart without task completion.
    if "add_product_to_cart" in code and "apis.supervisor.complete_task()" not in code:
        # Append a call to complete the task to ensure the operation is finalized.
        code += "\nresult = apis.supervisor.complete_task()"
    return code
