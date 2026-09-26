HISTORY_LENGTH = 10

def retry_policy(attempt, response, action, admissible, state):
    return {'extra_instruction': 'pick an admissible action'} if attempt < 3 else None
