import random

TEMPERATURE = 0.5  # Slightly higher temperature to encourage more exploration and creativity in reasoning.

def format_prompt(prompt: str, state: dict) -> str:
    """
    Curiosity-driven prompt modification to encourage the model to explore less obvious actions.
    Adds an instruction to emphasize exploration for potentially beneficial actions.
    """
    curiosity_instruction = random.choice([
        "Think about the less obvious actions that might yield interesting or beneficial results.",
        "Consider exploring actions that are not the most straightforward.",
        "Reflect on the environment context and think outside the box to find novel solutions."
    ])
    return prompt + f"\n<think>{curiosity_instruction}</think>"

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """
    Encourages revisiting previously unexplored actions on retry.
    On each retry, provides a hint to consider actions that might not have been immediately obvious previously.
    """
    if attempt == 1:
        extra_instruction = (
            "Re-evaluate the possibilities considering actions that might have been overlooked initially."
            " Is there an action that requires a different point of view?"
        )
        return {"extra_instruction": extra_instruction, "temperature": 0.45}
    elif attempt == 2:
        return {"extra_instruction": "Emphasize lateral thinking and come up with creative ways to solve the current challenges.", "temperature": 0.4}
    return None