HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Enhanced retry policy that adapts the prompt more explicitly when an invalid action is chosen
    # Include specific instruction to double-check the list of admissible actions
    if attempt == 1:
        return {
            "extra_instruction": "Your action was invalid. Please re-evaluate your reasoning and ensure you choose an action from the list of admissible actions provided.",
            "temperature": 0.3
        }
    elif attempt == 2:
        return {
            "extra_instruction": "This is your final attempt. Carefully review the list of admissible actions and make a considered choice.",
            "temperature": 0.2
        }
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Extract action by splitting and searching explicitly for the <action>...</action> tags
    start_tag = "<action>"
    end_tag = "</action>"
    start_idx = response.find(start_tag)
    end_idx = response.find(end_tag, start_idx + len(start_tag))
    
    if start_idx != -1 and end_idx != -1:
        action_str = response[start_idx + len(start_tag): end_idx].strip().lower()
    else:
        action_str = "look"  # fallback action if parsing fails
        
    # Ensure the parsed action is within the list of admissible actions
    return action_str if action_str in admissible else "look"