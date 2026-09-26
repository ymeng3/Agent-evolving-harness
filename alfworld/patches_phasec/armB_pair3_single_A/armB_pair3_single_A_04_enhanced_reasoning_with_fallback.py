HISTORY_LENGTH = 10
TEMPERATURE = 0.35

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Maintains a retry policy with tailored instructions for the model when an invalid action is suggested
    and slightly adjusted temperature settings for better exploration. Additionally, updates the state for
    tracking retries.
    """
    retries = {
        1: {
            "extra_instruction": " The selected action was not valid. Re-evaluate the scenario, choose an action from the admissible list, and ensure it directly contributes to the task at hand.",
            "temperature": 0.3
        },
        2: {
            "extra_instruction": " Final attempt: Use all context clues to select one action from the admissible list that progresses the task effectively.",
            "temperature": 0.25
        }
    }
    state["retry_count"] = attempt
    return retries.get(attempt, None)

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """
    Updates state with action history and observation changes to keep track of visited states
    and identify potential loops or redundant actions.
    """
    if "history" not in state:
        state["history"] = []
    state["history"].append((observation, action))
    state["latest_observation"] = next_observation

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    Chooses fallback based on common strategies like exploring the environment
    with 'look' or using action history to find the most frequent successful action.
    """
    fallback_action = "look"
    
    # Analyze history to find the most frequent successful action
    if state.get("history"):
        action_counter = collections.Counter(action for _, action in state["history"])
        for action in action_counter.most_common():
            if action[0] in admissible:
                fallback_action = action[0]
                break
    
    return fallback_action