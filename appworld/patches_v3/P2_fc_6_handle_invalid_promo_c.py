EDITS = [
    {
        "id": "e1",
        "capability": "Recovery",
        "impl": "ControlFlow",
        "trigger": "Execution failed with status code 422 during place_order API call",
        "depends": [],
        "expected_effect": "Removes invalid promo code when a place_order API call fails due to a 422 error.",
        "side_effect_risk": "Minimal; this edit only fires after a specific 422 error is encountered, which indicates an issue that needs correction."
    }
]

def e1_post_exec(code, out, state):
    # Detect if the execution was a place_order attempt and failed with a 422 error.
    if "place_order" in code and "Response status code is 422" in out:
        # Inject code to remove the invalid promo code.
        return """
promo_result = apis.amazon.remove_promo_code_from_cart(access_token=login_result['access_token'])
print("Attempting to remove invalid promo code:", promo_result)
""" + code
    return code
