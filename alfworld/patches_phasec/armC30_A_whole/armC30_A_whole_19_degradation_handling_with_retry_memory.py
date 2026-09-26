HISTORY_LENGTH = 8
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    # Update the prompt to reflect the previous action successes.
    success_rate = state.get('success_rate', 0)
    degraded_prompt = "Note: Previous actions have faced challenges. Increase precision and focus."
    if success_rate < 0.3:
        prompt += "\n" + degraded_prompt
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Track failed attempts in state and refine retry approach.
    if "retry_attempts" not in state:
        state["retry_attempts"] = 0
    state["retry_attempts"] += 1

    extra_instruction = f"Your last action wasn't valid. Here's another chance to select an action from the admissible list."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        return {
            "extra_instruction": extra_instruction + " Consider environmental factors for choosing the next action.",
            "temperature": 0.25
        }
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update state based on success of actions.
    if "successful_steps" not in state:
        state["successful_steps"] = 0

    if not observation == next_observation:
        state["successful_steps"] += 1

    # Calculate a proxy success rate to influence future attempts.
    total_attempts = state.get("retry_attempts", 0) + state["successful_steps"]
    state["success_rate"] = (state["successful_steps"] / total_attempts) if total_attempts else 0

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Prioritize fallback action based on previously successful actions
    if 'goal_related_actions' in state:
        for action in state['goal_related_actions']:
            if action in admissible:
                return action
    return 'look'