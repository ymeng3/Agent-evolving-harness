HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    reasoning_guide = 'Reasoning Guide:\n1. Understand the Task: Identify the ultimate goal and sub-goals.\n2. Assess the Current State: Analyze the current observation and context, focusing on task-related objects and locations.\n3. Determine Next Step: Decide on the most logical action that will progress the task.\n\n'
    return reasoning_guide + prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    if 'recent_actions' not in state:
        state['recent_actions'] = []
    state['recent_actions'].append(action)
    if len(state['recent_actions']) > 5:
        state['recent_actions'].pop(0)
