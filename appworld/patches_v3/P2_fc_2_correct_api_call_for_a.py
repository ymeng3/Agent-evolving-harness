EDITS = [
    {
        "id": "e1",
        "capability": "ToolUse",
        "impl": "Code",
        "trigger": "api_name parameter in show_api_doc() call, during pre_call, matches 'add_to_cart' for the amazon app",
        "depends": [],
        "expected_effect": "Automatically correct the API call from 'add_to_cart' to 'add_product_to_cart' when querying API documentation.",
        "side_effect_risk": "Minimal risk of incorrectly rewriting if the API name does not accidentally exist elsewhere."
    }
]

def e1_pre_call(prompt, state):
    corrected_prompt = prompt
    if "show_api_doc(" in prompt and "'add_to_cart'" in prompt:
        corrected_prompt = prompt.replace("'add_to_cart'", "'add_product_to_cart'")
    return corrected_prompt
