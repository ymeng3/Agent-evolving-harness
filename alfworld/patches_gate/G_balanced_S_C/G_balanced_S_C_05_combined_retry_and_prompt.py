HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt < 2:
        extra_instruction = (
            "Your previous action was not admissible."
            " Ensure your selected action is one of the admissible actions."
            " Reason carefully and ensure you're considering the environment context."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    return None

def format_prompt(prompt: str, state: dict) -> str:
    # Splitting the reasoning and action phases with clear instructions
    split_prompt = (
        prompt.replace("Now it's your turn to take an action.",
                       "Now it's your turn to reason and take an action.")
              .replace("You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.",
                       "First, reason step-by-step about the current situation, considering the goal and admissible actions. Enclose this reasoning within <think> </think> tags.")
              .replace("Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.",
                       "After reasoning, review admissible actions again, then decide and clearly specify your action within <action> </action> tags.")
    )
    return split_prompt