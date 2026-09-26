HISTORY_LENGTH = 8

def format_prompt(prompt: str, state: dict) -> str:
    # Enhance the prompt with a focus on providing clear context and direction for actionable decisions
    emphasis_instruction = (
        "Ensure your reasoning is logical and clearly tied to the current observation and task. "
        "Prioritize actions that closely align with achieving the task goals."
    )
    
    # Insert the additional instruction into the prompt
    context_clarity_prompt = prompt + f"\n{emphasis_instruction}"
    
    return context_clarity_prompt