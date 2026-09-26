HISTORY_LENGTH = 7

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize the memory of successful actions if not already done
    if "successful_actions" not in state:
        state["successful_actions"] = []

    # Record the action if it leads to a successful outcome
    if "successfully" in next_observation and action not in state["successful_actions"]:
        state["successful_actions"].append(action)

def format_prompt(prompt: str, state: dict) -> str:
    if state.get("successful_actions"):
        # Add a hint of previously successful actions to the prompt
        hint = "Previously successful actions: " + ', '.join(state["successful_actions"])
        prompt += f"\n{hint}."
    return prompt