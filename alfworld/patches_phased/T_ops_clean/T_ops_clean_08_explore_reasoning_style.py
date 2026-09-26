HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    # Reformat the reasoning style to simplify visualization and focus
    reformatted_prompt = prompt.replace(
        "This reasoning process MUST be enclosed within <think> </think> tags.",
        "Explain your reasoning in a concise bulleted list enclosed within <think> </think> tags."
    )
    return reformatted_prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Remember to select strictly one of the admissible actions provided."
    if attempt == 1:
        return {"extra_instruction": extra_instruction}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None