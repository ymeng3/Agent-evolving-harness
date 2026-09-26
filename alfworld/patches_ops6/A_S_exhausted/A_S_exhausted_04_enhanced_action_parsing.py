HISTORY_LENGTH = 10

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    
    # Extract the action from within <action> tags
    action_match = re.search(r'<action>(.*?)</action>', response, re.IGNORECASE)
    if action_match:
        extracted_action = action_match.group(1).strip().lower()

        # Attempt to clean the extracted action to match admissible formats
        normalized_action = extracted_action.replace("_", " ").strip()

        # Consider the first word of the extracted action to try and identify the most intended action
        split_action = extracted_action.split()
        if split_action:
            shortest_distance = float('inf')
            closest_action = ""
            for adm_action in admissible:
                distance = len(set(split_action) ^ set(adm_action.split()))
                if distance < shortest_distance:
                    shortest_distance = distance
                    closest_action = adm_action
        
            if closest_action in admissible:
                return closest_action

    # Default fallback if no match is found
    return admissible[0]