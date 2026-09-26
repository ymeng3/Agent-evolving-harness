HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    reasoning_guide = 'Reasoning Guide:\n1. Understand the Task: Identify the ultimate goal and sub-goals.\n2. Assess the Current State: Analyze the current observation and context, focusing on task-related objects and locations.\n3. Determine Next Step: Decide on the most logical action that will progress the task.\n\n'
    return reasoning_guide + prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    if attempt == 1:
        return {'extra_instruction': 'Make sure the action is correctly chosen from the provided list of admissible actions.'}
    if attempt == 2:
        return {'extra_instruction': 'Review your reasoning to ensure it aligns with the current state of the environment.', 'temperature': 0.3}
    return None
