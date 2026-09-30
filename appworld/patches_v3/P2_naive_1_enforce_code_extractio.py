EDITS = [
    {
        "id": "e1",
        "capability": "Recovery",
        "impl": "Code",
        "trigger": "execution failure at cell 13 using an incorrect password reset code",
        "depends": [],
        "expected_effect": "Re-extract and use the correct, most recent password reset code.",
        "side_effect_risk": "Minimal risk as it targets specific failure scenarios and recent data."
    }
]

def e1_post_exec(code, out, state):
    if "Execution failed" in out and "reset_password" in code:
        # Attempt recovery: sort threads by timestamp and extract the correct code
        last_threads_query = code.split('query="Venmo Password Reset Code", page_limit=20)')[1].split('\n# Sort by created_at descending to get the newest')
        if last_threads_query:
            # Extract the correct newest email code
            recent_email_id = max(int(line.strip().split('[')[1].split(']')[0])
                                  for line in last_threads_query.split('\n') if '[' in line)
            # Rebuild the extraction code to fetch correct email and extract the reset code
            recovery_code = f"""
email_content = apis.gmail.show_email(email_id={recent_email_id}, access_token=login_result["access_token"])
print(email_content)
reset_code = extract_reset_code(email_content)
reset_result = apis.venmo.reset_password(email='anita.burch@gmail.com', password_reset_code=reset_code, new_password='aQAdQp')
print(reset_result)
"""
            # Execute the recovery code
            exec(recovery_code, globals(), state)
