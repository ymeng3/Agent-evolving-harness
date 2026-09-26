def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Modifies the retry strategy by including extra context about the environment situation when the action is invalid.
    """
    if attempt < 2:
        extra_instruction = (
            f"The previous action '{action}' was invalid. Carefully analyze the current environment context and "
            "admissible actions. Provide reasoning for why an action is chosen based on this context."
        )
        return {
            "extra_instruction": extra_instruction,
            "temperature": 0.35 if attempt == 1 else 0.3
        }
    return None

def format_prompt(prompt: str, state: dict) -> str:
    """
    Adds environmental feedback to the prompt, focusing the model on relevant details to improve decision-making.
    """
    environ_context = state.get("last_observation", "")
    if environ_context:
        prompt += f"\nCurrent environment details to consider: {environ_context}."
    return prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Updates the state with the latest observation to maintain context about the environment's latest status.
    """
    state["last_observation"] = next_observation