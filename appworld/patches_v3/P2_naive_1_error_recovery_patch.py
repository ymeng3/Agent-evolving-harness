EDITS = [
    {
        "id": "e1",
        "capability": "Recovery",
        "impl": "ControlFlow",
        "trigger": "Execution failed with 'reset_password' API call",
        "depends": [],
        "expected_effect": "Automatically retry the 'reset_password' call with the latest password reset code",
        "side_effect_risk": "May cause repeated attempts if the actual cause of failure is not addressed"
    }
]

def e1_post_exec(code, out, state):
    if "reset_password" in code and "Execution failed" in str(out):
        # Retrieve the latest email thread ID that contains the password reset code
        inbox_threads_sorted = state.get("inbox_threads_sorted", [])
        
        if inbox_threads_sorted:
            latest_thread = inbox_threads_sorted[0]
            latest_email_id = latest_thread["email_ids"][-1]
            
            # Get the email content to retrieve the latest password reset code
            email_content = apis.gmail.show_email(email_id=latest_email_id, access_token=state["login_result"]["access_token"])
            latest_code = extract_reset_code(email_content["body"])
            
            # Store the latest code in the state for re-execution
            state["retry_reset_code"] = latest_code
            state["retry_required"] = True

def e1_pre_complete(code, state):
    if state.get("retry_required", False):
        # Modify the 'reset_password' code snippet with the latest password reset code
        latest_code = state.get("retry_reset_code", "")
        
        if latest_code:
            new_code = code.replace(re.search(r'password_reset_code=\'.*?\'', code).group(),
                                    f"password_reset_code='{latest_code}'")
            return new_code
    return code

def extract_reset_code(email_body):
    # Extract the reset code from the email body using regex
    import re
    match = re.search(r'[a-f0-9]{7}', email_body)
    if match:
        return match.group()
    return ""
