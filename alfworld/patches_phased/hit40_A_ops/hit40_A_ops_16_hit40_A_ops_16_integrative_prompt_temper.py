HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    """
    Enhances the prompt by emphasizing the need to select from the admissible actions
    and maintaining coherence with the task goal.
    """
    enhanced_prompt = (
        prompt.replace("Now it's your turn to take an action.",
                       "Now it's your turn to think carefully and take an action.")
              .replace("You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.",
                       "Think step-by-step about the current situation, the task goal, and the admissible actions. Put this reasoning in <think> </think> tags.")
              .replace("Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.",
                       "After reasoning, review the admissible actions attentively and specify your action within <action> </action> tags.")
    )
    return enhanced_prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Integrates temperature adjustment and proactive guidance to encourage prompt adherence.
    """
    if attempt == 1:
        extra_instruction = (
            "The action was not valid. Focus on picking an action listed as admissible."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    elif attempt == 2:
        extra_instruction = (
            "This action must be selected from the admissible list. Review carefully."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    return None