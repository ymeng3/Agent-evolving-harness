# TARGET: Improve information gathering by avoiding repetitive examinations of the same observed states.
HISTORY_LENGTH = 6

def format_prompt(prompt: str, state: dict) -> str:
    """
    Adds guidance to prompt to avoid common redundant actions if previously observed to be non-informative.
    """
    redundant_exams = state.get("redundant_exams", set())
    if redundant_exams:
        prompt += f"\nNote: You have already examined these objects to no avail: {', '.join(redundant_exams)}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            return action
    # Default fallback action when no valid action is found
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Memorizes non-informative examine actions to prevent unnecessary repetitions.
    """
    if action.startswith('examine') and "nothing happens" in next_observation:
        state.setdefault("redundant_exams", set()).add(action)
        
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