def format_prompt(prompt: str, state: dict) -> str:
    # Modify the prompt to sequentially guide the 'think' and 'act' process with clarifying instructions
    revised_prompt = (
        prompt.replace(
            "Now it's your turn to take an action.",
            "Commence by understanding your environment and goal. Then proceed with your reasoning and action."
        ).replace(
            "You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.",
            "Initially, reflect on the task requirements, the history of actions, and the environment's status; your reasoning should be enclosed in <think>...</think>."
        ).replace(
            "Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.",
            "After thorough reasoning, consult the admissible actions anew, then choose and specify your action in <action>...</action>."
        )
    )
    return revised_prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        extra_instruction = (
            "The previous action was not valid. "
            "Emphasize choosing one from the admissible actions' list."
            " Cross-verify your selection with the environment's current state."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    elif attempt == 2:
        extra_instruction = (
            "Final chance to rectify; focus thoroughly on the context and admissible actions."
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.3}
    return None