HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Extend the prompt with explicit guidance on leveraging the current environment and successful action patterns.
    """
    action_guide = state.get("action_guide", "")
    context_hint = state.get("context_hint", "")
    if action_guide:
        prompt += f"\nNote: Consider actions similar to previous successes: {action_guide}."
    if context_hint:
        prompt += f"\nEnvironment context hint: {context_hint}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            # Update action guidance and context hint based on successful choice and observation
            state["action_guide"] = action
            state["context_hint"] = f"Utilize the {action} opportunity effectively."
            return action
    # Default fallback action when no valid action is found
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Update the state after executing each step to improve future action selection with contextual hints.
    """
    if 'action_success' not in state:
        state['action_success'] = []
    if "successfully" in next_observation:
        state['action_success'].append(action)
        state['action_guide'] = action if len(state['action_success']) > 3 else ""

    # Capture useful context information from observations
    if "light" in observation or "receptacle" in observation:
        state['context_hint'] = f"Focus on light and receptacle areas."

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Provide additional context-focused instructions and minor temperature adjustments on retries.
    """
    if attempt == 1:
        extra_instruction = (
            "Recall your observations on environment context and light opportunities. Focus on choosing from admissible options."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    elif attempt == 2:
        extra_instruction = (
            "Attempt to choose an admissible action utilizing context hints from your observations. Maintain focus on success patterns."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None