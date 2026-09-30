EDITS = [
    {
        "id": "e1",
        "capability": "Recovery",
        "impl": "ControlFlow",
        "trigger": "code contains 'apis.amazon.place_order' and 'Execution failed' in out",
        "depends": [],
        "expected_effect": "Retry placing order after removing any invalid promo code, avoiding failure due to promo code errors.",
        "side_effect_risk": "Might retry unnecessarily if the failure is unrelated to promo codes."
    }
]

def e1_post_exec(code, out, state):
    if "apis.amazon.place_order" in code and "Execution failed" in out:
        # Check for promo code issue
        if '"promo_valid": false' in state['cart_info']:
            # Retry logic: removing promo code and attempting order again
            recovery_code = """
promo_result = apis.amazon.remove_promo_code_from_cart(access_token=login_result['access_token'])
print(promo_result)

order_result = apis.amazon.place_order(
    payment_card_id=204,
    address_id=91,
    access_token=login_result['access_token']
)
print(order_result)
"""
            state['recovery_attempt'] = True
            return recovery_code
    return ""

def e1_pre_call(prompt, state):
    # Maintain state info about cart details
    if "show_cart" in prompt:
        state['cart_info'] = prompt
    return prompt
