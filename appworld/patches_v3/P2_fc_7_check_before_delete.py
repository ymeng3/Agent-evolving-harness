EDITS = [
    {
        "id": "e1",
        "capability": "Planning",
        "impl": "ControlFlow",
        "trigger": "pre_call when calling delete_product_from_cart without previously ensuring preferred color items",
        "depends": [],
        "expected_effect": "Prevent deletion of products from cart if no preferred color items are already in cart and not yet added.",
        "side_effect_risk": "If the entire cart contains only unwanted items with no attempt to check for preferred colors, deletion might be blocked unnecessarily."
    }
]

def e1_pre_call(prompt, state):
    if "delete_product_from_cart" in prompt:
        # Check if the last action was not checking or adding preferred color items
        last_action = state.get("last_action", "")
        if "check_color_availability" not in last_action and "add_preferred_items" not in last_action:
            # Block the deletion request
            return "// Deletion blocked: Ensure preferred items are checked/added before deleting\n" + prompt
    # Update last action
    state["last_action"] = "delete_product_from_cart"
    return prompt
