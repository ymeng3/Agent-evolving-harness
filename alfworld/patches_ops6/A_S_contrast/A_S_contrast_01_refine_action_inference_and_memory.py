HISTORY_LENGTH = 8
TEMPERATURE = 0.45

def format_prompt(prompt: str, state: dict) -> str:
    """Enhance prompt with consistent advice from previously successful actions."""
    if "recommended_actions" in state:
        advice = ", ".join(state["recommended_actions"][-3:])
        prompt += f"\nWhen deciding, consider these past effective actions: {advice}."
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    """Extract action from response and reinforce recommended actions."""
    import re
    match = re.search(r"<action>(.*?)</action>", response, re.IGNORECASE)
    if match:
        action = match.group(1).strip().lower()
        if action in admissible:
            if "recommended_actions" not in state:
                state["recommended_actions"] = []
            if action not in state["recommended_actions"]:
                state["recommended_actions"].append(action)
            return action
    # Default fallback action when no valid action is found
    return "examine"

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """Adjust memory to cunningly inform future steps."""
    if "success_memory" not in state:
        state["success_memory"] = []
    if "successfully" in next_observation and action not in state["success_memory"]:
        state["success_memory"].append(action)
        if len(state["success_memory"]) >= 3:
            state.setdefault("recommended_actions", []).extend(state["success_memory"][-3:])

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """Modify temperature and prompt retries with learned guidance."""
    if attempt == 1:
        return {
            "extra_instruction": (
                "Reflect on earlier guidance and focus on an admissible choice."
            ),
            "temperature": 0.35
        }
    elif attempt == 2:
        return {
            "extra_instruction": (
                "Concentrate on actions that have previously been successful and are admissible."
            ),
            "temperature": 0.3
        }
    return None