HISTORY_LENGTH = 8
TEMPERATURE = 0.45

def format_prompt(prompt: str, state: dict) -> str:
    # Enhance the existing instruction for clarity in reasoning and selection process
    enhanced_instruction = (
        "Think carefully about the task requirements and the current environmental context."
        " Ensure that your action aligns with the admissible actions provided."
    )
    return prompt + "\n" + enhanced_instruction

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        # Provide additional guidance when the first attempt fails
        extra_instruction = "Review the environmental context and admissible actions. Choose wisely."
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    elif attempt == 2:
        # Further reduce temperature and refine instruction if second attempt fails
        extra_instruction = "It's critical now to select an action from the admissible list."
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None