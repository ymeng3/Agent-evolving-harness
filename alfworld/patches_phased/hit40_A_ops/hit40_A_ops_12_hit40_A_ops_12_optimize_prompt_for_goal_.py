def format_prompt(prompt: str, state: dict) -> str:
    # Modify the prompt to emphasize goal alignment and context awareness
    enhanced_prompt = (
        prompt.replace(
            "Now it's your turn to take an action.",
            "It's crucial to align your actions closely with the overall task goals."
        ).replace(
            "You should first reason step-by-step about the current situation. This reasoning process MUST be enclosed within <think> </think> tags.",
            "Thoroughly reason step-by-step about the current situation, keeping the task goals and context in mind. Enclose this reasoning in <think> </think> tags."
        ).replace(
            "Once you've finished your reasoning, you should choose an admissible action for current step and present it within <action> </action> tags.",
            "After concluding your reasoning, make sure your chosen action aligns with the task goals and context. Clearly present it within <action> </action> tags."
        )
    )
    return enhanced_prompt