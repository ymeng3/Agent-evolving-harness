HISTORY_LENGTH = 5

def format_prompt(prompt: str, state: dict) -> str:
    reasoning_guide = (
        "Reasoning Guide:\n"
        "1. Understand the Task: Identify the ultimate goal and sub-goals.\n"
        "2. Assess the Current State: Analyze the current observation and context, focusing on task-related objects and locations.\n"
        "3. Determine Next Step: Decide on the most logical action that will progress the task.\n\n"
    )
    return reasoning_guide + prompt
