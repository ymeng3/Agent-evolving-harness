HISTORY_LENGTH = 10
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    split_prompt = (
        prompt.replace("Now it's your turn to take an action.",
                       "Now it's your turn to reason and take an action.")
              .replace("You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.",
                       "First, reason step-by-step about the current situation, considering the goal and admissible actions. Enclose this reasoning within <think> </think> tags.")
              .replace("Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.",
                       "After reasoning, review admissible actions again, then decide and clearly specify your action within <action> </action> tags.")
    )
    return split_prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    extra_instruction = "Please focus on selecting an action that is admissible. Use reasoned decision-making and ensure coherence with the scenario."
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.6}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.5}
    return None