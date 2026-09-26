import random

def choose_fallback(admissible: list[str], state: dict) -> str:
    """
    A fallback mechanism that selects an admissible action randomly when the model's action is inadmissible.
    This approach introduces variability and might help the agent to recover from undesirable action loops.
    """
    if admissible:
        return random.choice(admissible)
    return "look"