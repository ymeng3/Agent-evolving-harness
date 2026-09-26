HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Retry with a focus on re-querying, especially for the tasks that Change 1 struggles with.
    if attempt < 2:
        extra_instruction = "Please rethink your previous reasoning as it did not result in a valid action. Focus on selecting a clearly admissible action this time."
        return {
            "extra_instruction": extra_instruction,
            "temperature": 0.6
        }
    return None

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Extract the action from <action></action> and check if it matches an admissible action.
    import re
    action_candidate = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if action_candidate:
        action_text = action_candidate.group(1).strip().lower()
        if action_text in admissible:
            return action_text
    
    # If default parsing fails, attempt a fuzzy match as fallback.
    matches = [action for action in admissible if action.startswith(action_candidate.group(1)[:3].lower())]
    if matches:
        return matches[0]

    # Default fallback if fuzzy match fails, allowing retry mechanism to capture the error.
    return admissible[0]

def format_prompt(prompt: str, state: dict) -> str:
    # Add a motivational aspect to encourage optimal performance, leveraging the broader admissibility.
    additional_context = "Remember, acting with precision is crucial for achieving success in this environment. Logical reasoning is key here."
    return prompt + "\n" + additional_context