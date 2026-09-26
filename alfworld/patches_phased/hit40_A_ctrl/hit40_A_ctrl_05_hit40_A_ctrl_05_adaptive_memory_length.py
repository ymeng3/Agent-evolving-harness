HISTORY_LENGTH = 5

def memory_update(state: dict, observation: str, action: str, next_observation: str) -> None:
    # Initialize state memory if not present
    if 'memory' not in state:
        state['memory'] = collections.deque(maxlen=20)
    
    # Append current step (observation, action, next_observation) into memory
    state['memory'].append((observation, action, next_observation))

def format_prompt(prompt: str, state: dict) -> str:
    # Increase history length contextually based on the task
    task_description = re.search(r"Task description:\s*(.*)", prompt)
    
    if task_description:
        task = task_description.group(1).lower()
        history_length = 5
        
        # Adjust history length to 10 for tasks where context is more critical, like 'pick_clean'
        if 'pick_clean' in task:
            history_length = 10
        
        # Use last `history_length` memory entries for the prompt
        state_memory = "\n".join([
            f"Observation: {obs}, Action: {act}, Result: {nxt_obs}" 
            for obs, act, nxt_obs in list(state['memory'])[-history_length:]
        ])
        
        # Append recent memory to the prompt
        prompt += f"\nRecent memory: {state_memory}"
    
    return prompt