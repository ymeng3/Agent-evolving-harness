HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    """
    Enhances the prompt by emphasizing a structured reasoning approach.
    Introduces additional guidance encouraging the agent to reflect on its previous successful actions.
    """
    # Reflecting on past successful actions might help the agent make more informed decisions.
    reflection_instruction = (
        "Reflect on the successful actions you took in previous similar situations. "
        "Focus on the goal and the most relevant admissible actions for achieving it in this context."
    )
    # Embed the reflection instruction into the original prompt format
    enhanced_prompt = prompt + "\n" + reflection_instruction
    return enhanced_prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Your last action wasn't valid. Focus on selecting one of the admissible actions listed."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None