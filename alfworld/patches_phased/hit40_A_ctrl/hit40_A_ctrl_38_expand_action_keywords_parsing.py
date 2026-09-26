import re

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    """
    Enhances action extraction by searching for variants of admissible actions.
    """

    # Define the helper inside to ensure it adheres to the harness restriction
    def extract_action_variants(response_text: str) -> str:
        # Attempt to match the action within <action> tags with some permissible variations
        match = re.search(r"<action>\s*(.*?)\s*</action>", response_text, re.IGNORECASE)
        if match:
            candidate_action = match.group(1).strip().lower()
            if candidate_action in admissible:
                return candidate_action

        # Fallback to searching each admissible action directly as a variant of words
        for action in admissible:
            words = action.split()
            for variant in itertools.permutations(words):
                variant_str = " ".join(variant)
                if variant_str in response_text.lower():
                    return action
        
        # Default to a safe choice if extraction fails
        return "look"
    
    # Run the enhanced action extractor and return the result
    return extract_action_variants(response)