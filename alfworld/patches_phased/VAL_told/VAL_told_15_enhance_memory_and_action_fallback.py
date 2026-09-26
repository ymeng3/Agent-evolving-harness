HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # No changes to prompt format, keeping default for consistency.
    return prompt

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Extract the action from <action> tags and match it to admissible actions.
    import re
    action_match = re.search(r"<action>(.*?)</action>", response)
    action = action_match.group(1).strip().lower() if action_match else ""
    return action if action in admissible else ""

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Adapt retry policy to encourage smart retries with incremental temperature adjustment.
    extra_instruction = "Your last action wasn't valid. Please choose an action from the admissible list with care."
    temperature_adjustment = [0.4, 0.35]  # Gradually decrease temperature for focus.
    if attempt in {1, 2}:
        return {"extra_instruction": extra_instruction, "temperature": temperature_adjustment[attempt - 1]}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Update memory with current observation and action.
    visited = state.setdefault("visited", set())
    visited.add(observation)

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Choose a fallback action that prioritizes exploration rather than repeatedly looking.
    if 'look' in admissible and len(admissible) > 1:
        admissible.remove('look')
    return random.choice(admissible)