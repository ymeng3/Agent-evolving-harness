HISTORY_LENGTH = 15
TEMPERATURE = 0.45

def format_prompt(prompt: str, state: dict) -> str:
    # Simplify the prompt by excluding less relevant parts of the observation history.
    if len(state.get("history", [])) > 5:
        stripped_prompt = "\n".join(prompt.split("\n")[-8:])
        stripped_prompt = "Remember to adapt to the environment based on past actions.\n" + stripped_prompt
        return stripped_prompt
    return prompt

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    # Tailoring retry policy with adaptive instruction and prompt tweaking.
    extra_instruction = "Remember: Choose the action by considering the admissible options closely. Analyses are key!"
    if attempt == 1:
        return {"extra_instruction": extra_instruction, "temperature": 0.4}
    elif attempt == 2:
        return {"extra_instruction": extra_instruction, "temperature": 0.35}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Keep track of actions and observations, filter non-informative feedback
    state.setdefault("history", []).append((observation, action))
    act = action.strip().lower()
    if "nothing happens" in next_observation.lower():
        state.setdefault("noop_counter", collections.Counter())[act] += 1

def parse_action(response: str, admissible: list[str], state: dict) -> str:
    # Enhance action parsing by refining strategy to avoid repetitive invalid actions.
    actions = re.findall(r"<action>(.*?)</action>", response, re.S | re.I)
    if actions:
        chosen_action = actions[-1].strip().lower()
    else:
        return random.choice(admissible)

    if chosen_action in admissible:
        noop_counter = state.get("noop_counter", {})
        recent_actions = [a for _, a in state.get("history", [])][-3:]
        
        if noop_counter.get(chosen_action, 0) >= 2 or chosen_action in recent_actions:
            alternatives = [a for a in admissible if a != chosen_action]
            if alternatives:
                return random.choice(alternatives)
    return chosen_action

def choose_fallback(admissible: list[str], state: dict) -> str:
    # Smart fallback that prefers new actions over repeating recent mistakes.
    recent_actions = {a for _, a in state.get("history", [])[-5:]}
    possible_actions = [a for a in admissible if a not in recent_actions]
    return random.choice(possible_actions) if possible_actions else random.choice(admissible)