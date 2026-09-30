EDITS = [
    {
        "id": "e1",
        "capability": "Verification",
        "impl": "ControlFlow",
        "trigger": "before complete_task to ensure proper product selection",
        "depends": [],
        "expected_effect": "Prevent completion unless there are exactly two of the preferred color and size shirts in the cart.",
        "side_effect_risk": "May prevent completion if no desired products can be verified."
    }
]

def e1_pre_complete(code, state):
    if "complete_task" in code:
        # Extract cart information from the state if available.
        cart = state.get("cart_items", [])
        
        # Check for two similar colored shirts of the right kind in the cart.
        def verify_cart_items(cart):
            preferred_colors = ["red", "black", "navy blue"]
            item_counts = {color: 0 for color in preferred_colors}
            target_product_name = "Hanes Men's ComfortSoft Short Sleeve T-Shirt"
            
            for item in cart:
                if target_product_name in item['product_name']:
                    for color in preferred_colors:
                        if color in item['product_name'] and item['size'] == "extra-large":
                            item_counts[color] += 1
            
            # Check that the highest-preference color has exactly two items in cart.
            for color in preferred_colors:
                if item_counts[color] >= 2:
                    return True
            return False
        
        if not verify_cart_items(cart):
            raise RuntimeError("Verification failed: The cart does not contain two of the preferred color and size of shirts.")
    
    return code
