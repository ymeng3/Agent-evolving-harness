HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Enhance prompt to clarify steps and emphasize reasoning depth
    enhanced_prompt = (
        prompt.replace("Now it's your turn to take an action.",
                       "Now you must carefully reason and take an informed action.")
              .replace("You should first reason step-by-step about the current situation.",
                       "Please think through each aspect of the current situation meticulously.")
              .replace("Once you've finished your reasoning, you should choose an admissible action for current step",
                       "After deliberate reasoning, re-evaluate the admissible actions and make a decisive choice for the current step")
    )
    return enhanced_prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Consider the admissible actions and aim for the one that best achieves the task."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None