HISTORY_LENGTH = 15

def format_prompt(prompt: str, state: dict) -> str:
    # Deduplicate essential observation details from prompt history and current observation.
    def summarize(obs: str) -> str:
        return ' '.join(sorted(set(obs.split()), key=lambda x: obs.index(x)))
    
    prompt_lines = prompt.split('\n')
    # Replace current observation line with summarization variant.
    summary = summarize(prompt_lines[3].replace("Your current observation is: ", ""))
    prompt_lines[3] = f"Your summarized observation is: {summary}"
    return '\n'.join(prompt_lines)

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Use an adaptive instruction to mitigate invalid choices:
    extra_instruction = (
        "Invalid choice detected. Focus on taking valid actions from the admissible list. Make sure to reevaluate based on current context."
    )
    if attempt == 1 or attempt == 2:
        return {"extra_instruction": extra_instruction}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Log actions taken that result in no change of observation to detect patterns.
    if action:
        if observation == next_observation:
            state['stuck_actions'] = state.get('stuck_actions', 0) + 1
        else:
            state['stuck_actions'] = 0
        
        # If the agent seems stuck, intervene with higher frequency in retries.
        state['should_intervene'] = state['stuck_actions'] >= 2

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Utilize the state-based intervention to decide if a fallback needs to be different.
    if state.get('should_intervene'):
        # Ideally, select the first actionable verb to break potential loops.
        fallback = next((action for action in admissible if "use" in action or "open" in action), 'look')
        return fallback
    return 'look'