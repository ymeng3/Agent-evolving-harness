HISTORY_LENGTH = 8

def format_prompt(prompt: str, state: dict) -> str:
    # Introduce an adaptive prompt instruction based on the agent's recent performance
    if state.get("recent_action_failure", False):
        additional_instruction = (
            " Recall recent mistakes and focus on selecting from the admissible actions. "
            "Ensure your reasoning aligns with the task requirements."
        )
        return prompt + additional_instruction
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        state["recent_action_failure"] = True
        retry_instruction = (
            " Previous action was inadmissible. Choose wisely from the admissible list."
        )
        return {"extra_instruction": retry_instruction}
    state["recent_action_failure"] = False
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track whether the agent has recently made an invalid action
    state["recent_action_failure"] = False