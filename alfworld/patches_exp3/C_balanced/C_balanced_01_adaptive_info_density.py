HISTORY_LENGTH = 5
TEMPERATURE = 0.4

def format_prompt(prompt: str, state: dict) -> str:
    # Dynamically adjust information density based on task difficulty (perceived via previous actions and observations)
    task_type = state.get("task_type", "simple")
    
    def classify_task(current_observation: str, state: dict) -> str:
        # Nested function to classify task difficulty based on observation patterns, action history length
        if len(state.get("action_history", [])) > 4:
            return "complex"
        elif any(word in current_observation.lower() for word in ["dark", "cluttered", "obstacles"]):
            return "complex"
        return "simple"
    
    task_type = classify_task(state.get("current_observation", ""), state)
    state["task_type"] = task_type
    
    if task_type == "complex":
        # Providing enhanced context or guidance if task is recognized as complex
        detailed_instruction = (
            "Given the complexity of your current task, ensure you thoroughly evaluate your environment and the task goal."
            " Carefully consider previous unsuccessful attempts and their outcomes."
        )
        return prompt + "\n" + detailed_instruction
    
    # If task is simple, use default prompt structure
    return prompt


def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Track action history needed for task classification
    action_history = state.get("action_history", [])
    action_history.append(action)
    
    current_observation = state.get("current_observation", "")
    state.update({
        "action_history": action_history[-5:],  # Keep only last 5 actions to conserve memory
        "current_observation": next_observation,
    })