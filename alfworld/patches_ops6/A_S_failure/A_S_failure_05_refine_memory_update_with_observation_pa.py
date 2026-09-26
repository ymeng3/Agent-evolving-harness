HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts.
    """
    action_guide = state.get("action_guide", "")
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Update action guidance based on successful choice
            state["action_guide"] = action
            return action
    # Default fallback action when no valid action is found
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state after executing each step to improve future action selection.
    Include additional logic to monitor specific observation patterns.
    """
    # Track successful actions
    if 'action_success' not in state:
        state['action_success'] = []
    
    # New: Track observation patterns for success
    if 'observation_patterns' not in state:
        state['observation_patterns'] = set()

    # Identify observation patterns that lead to success
    observation_keywords = ["found", "picked up", "successfully", "goal achieved", "placed"]
    if any(keyword in next_observation for keyword in observation_keywords):
        state['action_success'].append(action)
        state['observation_patterns'].add(observation)
    
    # Use patterns to inform action guidance
    if len(state['action_success']) > 3:
        state['action_guide'] = action
    else:
        # Check if we're in a similar observation pattern on the next step
        for pattern in state['observation_patterns']:
            if pattern in observation:
                state['action_guide'] = action
                break

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional instructions and minor temperature adjustments on retries.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall the guidance on successful actions. Focus on choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Choose an action from admissible options that aligns with previous successes."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None