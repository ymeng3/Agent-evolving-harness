HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    """
    Enhance the prompt with explicit focus on crafting solutions and selecting valid actions.
    Emphasize reasoning and admissible actions for optimal step-by-step planning.
    """
    prompt += "\nAs you consider your actions, prioritize logical reasoning and the feasibility of choices among admissible actions."
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
    return "look"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Strategically update the state based on successful actions to refine future prompts.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 5 else ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Implement structured retries with clear emphasis on admissible actions and reduced temperature.
    """
    extra_instruction = "Your last choice was invalid. Concentrate on selecting a valid action from the admissible ones listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None