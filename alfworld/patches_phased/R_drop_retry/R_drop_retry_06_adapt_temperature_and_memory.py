HISTORY_LENGTH = 10

def retry_policy(attempt: int, response: str, action: str, admissible: list[str], state: dict) -> dict | None:
    """This function decides whether to retry generating an action when the current action is not admissible.
       Depending on the attempt number, it adjusts the temperature for re-querying."""
    # If first attempt fails, increase temperature to encourage more exploration.
    if attempt == 1:
        return {"temperature": 0.6}
    # If second attempt fails, decrease temperature to encourage more focused response.
    elif attempt == 2:
        return {"temperature": 0.4}
    return None

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    """Update state memory to keep track of unique receptacles visited."""
    if "visited_receptacles" not in state:
        state["visited_receptacles"] = set()
    
    if "receptacle" in next_observation:
        # Extract the receptacle name from the observation.
        receptacle = next_observation.split("receptacle")[1].strip().split()[0]
        state["visited_receptacles"].add(receptacle)
    
def format_prompt(prompt: str, state: dict) -> str:
    """Append a note in the prompt listing the receptacles already visited to avoid re-checking them."""
    if "visited_receptacles" in state and state["visited_receptacles"]:
        visited_text = "Visited receptacles so far: " + ", ".join(state["visited_receptacles"]) + "."
        prompt += f"\n<Notice>{visited_text}</Notice>"
    return prompt