HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed without repeating past actions."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.2}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    format_prompt_initialization(state)
    format_prompt_add_stop_repeated_actions_instruction(prompt, state)
    
    def format_prompt_initialization(state):
        if "actions_history" not in state:
            state["actions_history"] = set()

    def format_prompt_add_stop_repeated_actions_instruction(prompt, state):
        actions_history = state.get("actions_history", set())
        repeated_actions_instruction = f"Note: You've already taken the following actions: {', '.join(actions_history)}. Avoid repeating them when possible."
        return f"{prompt}\n\n{repeated_actions_instruction}"
    
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if "actions_history" not in state:
        state["actions_history"] = set()
    state["actions_history"].add(action)