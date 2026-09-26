HISTORY_LENGTH = 10

def format_prompt(prompt: str, state: dict) -> str:
    # Add a note of important objects seen so far
    noted_objects = ", ".join(state.get("important_objects", []))
    if noted_objects:
        additional_context = f" Note: Keep track of these objects for future actions: {noted_objects}."
    else:
        additional_context = ""
    return prompt + additional_context

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Basic memory implementation to store noted objects
    if "important_objects" not in state:
        state["important_objects"] = set()

    # An example rule to identify important objects (this can be refined as needed)
    extract_objects = lambda obs: [obj.strip() for obj in obs.split() if obj.endswith("able")]

    # Extract objects from the observation and next observation
    current_objects = extract_objects(observation)
    next_objects = extract_objects(next_observation)

    # Store any new important objects
    state["important_objects"].update(current_objects + next_objects)