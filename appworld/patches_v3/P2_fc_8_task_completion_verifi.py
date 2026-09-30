EDITS = [
    {
        "id": "e1",
        "capability": "Verification",
        "impl": "ControlFlow",
        "trigger": "code contains 'apis.spotify.login' without subsequent 'apis.supervisor.complete_task'",
        "depends": [],
        "expected_effect": "Ensure complete_task is called after Spotify account verification and login.",
        "side_effect_risk": "May incorrectly assume task completion if other steps follow."
    }
]

def e1_pre_complete(code, state):
    # Check if the code includes a Spotify login without a complete_task call
    if "apis.spotify.login" in code and "apis.supervisor.complete_task()" not in code:
        # Append a call to complete_task at the end of the current code block
        complete_task_code = "\napis.supervisor.complete_task()"
        code += complete_task_code
    return code
