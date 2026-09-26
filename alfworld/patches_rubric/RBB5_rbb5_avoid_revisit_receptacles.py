# TARGET: Introduce a state-based mechanism to track visited receptacles and avoid revisiting them unnecessarily.
HISTORY_LENGTH = 6

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state after executing each step to improve future action selection.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""
    
    if 'visited_receptacles' not in state:
        state['visited_receptacles'] = set()
    
    receptacle_keywords = ['cabinet', 'drawer', 'fridge', 'shelf', 'countertop', 'sink']
    for keyword in receptacle_keywords:
        if f"go to {keyword}" in action or f"examine {keyword}" in action:
            if keyword in next_observation.lower():
                state['visited_receptacles'].add(keyword)
                break

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with guidance on the next best action inferred from previous successful attempts and avoid revisiting receptacles.
    """
    action_guide = state.get("action_guide", "")
    visited_receptacles = state.get("visited_receptacles", set())
    
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."
    
    if visited_receptacles:
        prompt += f"\nAvoid unnecessary visits to already checked receptacles: {', '.join(sorted(visited_receptacles))}."
    
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