HISTORY_LENGTH = 10
TEMPERATURE = 0.5

def format_prompt(prompt: str, state: dict) -> str:
    # Statement to initialize goals from task description if not already set
    if 'goals' not in state:
        task_string = prompt.split('Your task is to: ')[1].split('Prior to this step')[0]
        state['goals'] = task_string.lower().split(", ")

    # Include current goals and state in prompt
    goals_statement = "Your current goals are: " + ", ".join(state['goals'])
    extended_prompt = goals_statement + "\n" + prompt

    return extended_prompt

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Capture recent actions and observations to update goals and focus.
    if 'recent_actions' not in state:
        state['recent_actions'] = []
    state['recent_actions'].append(action)

    # Update goals: each action that successfully aligns with a goal removes that goal.
    for goal in state['goals']:
        if goal in action.lower():
            state['goals'].remove(goal)
            break

    # Keep the last few actions for reference (bounded memory)
    state['recent_actions'] = state['recent_actions'][-HISTORY_LENGTH:]