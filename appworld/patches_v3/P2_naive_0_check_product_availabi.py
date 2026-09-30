EDITS = [
    {
        "id": "e1",
        "capability": "Verification",
        "impl": "ControlFlow",
        "trigger": "Before adding any product to the amazon cart, verify its availability in Simple Note.",
        "depends": [],
        "expected_effect": "The agent verifies that a product exists in the Simple Note shopping list before attempting to add it to the Amazon cart, preventing unnecessary API calls and potential errors.",
        "side_effect_risk": "Delaying the add-to-cart operation if products are frequently not listed in Simple Note."
    }
]

def e1_setup():
    return """
def is_product_available_in_list(product_name, simple_note_list):
    # Simulate checking the availability of a product in the provided simple note shopping list
    return product_name in simple_note_list

def retrieve_shopping_list():
    # This would realistically retrieve the shopping list from simple note, but we'll simulate
    return [
        "Ray-Ban RB3447 Round Metal Sunglasses",
        "EatSmart Precision Tracker Digital Bathroom Scale",
        "Catan Board Game"
    ]
"""

def e1_pre_call(prompt, state):
    if 'add_product_to_cart' in prompt:
        # Extract product name from the prompt
        product_name = re.search(r"query='(.*?)'", prompt).group(1)
        # Get the user's shopping list from Simple Note
        simple_note_list = retrieve_shopping_list()
        
        # Check if the product is in the Simple Note list
        if not is_product_available_in_list(product_name, simple_note_list):
            raise Exception(f"Product '{product_name}' is not in the Simple Note shopping list, aborting add to cart.")
    
    return prompt
