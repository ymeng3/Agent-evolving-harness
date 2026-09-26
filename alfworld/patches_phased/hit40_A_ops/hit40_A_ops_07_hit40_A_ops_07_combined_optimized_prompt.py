HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Enhance the prompt by focusing more on the reasoning process and ensuring clarity.
    optimized_prompt = (
        prompt.replace("Now it's your turn to take an action.",
                       "Now it's your turn to reason carefully and take an appropriate action.")
              .replace("You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.",
                       "First, reason step-by-step considering the task goals and the environment context. Your reasoning process MUST be enclosed within <think> </think> tags.")
              .replace("Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.",
                       "After reasoning, review the admissible actions thoroughly and specify your chosen action within <action> </action> tags.")
    )
    return optimized_prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Adjust the retry strategy with enhanced instructions and varying temperature settings.
    retry_instructions = "Ensure you select an action from the admissible list. Review your reasoning and the current situation carefully."
    if attempt == 1:
        return {"extra_instruction": retry_instructions, "temperature": 0.5}
    elif attempt == 2:
        return {"extra_instruction": retry_instructions + " It's crucial to make a precise decision now.", "temperature": 0.3}
    return None