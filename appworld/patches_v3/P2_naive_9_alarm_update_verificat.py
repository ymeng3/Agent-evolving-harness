EDITS = [
    {
        "id": "e1",
        "capability": "Verification",
        "impl": "Code",
        "trigger": "apis.phone.update_alarm in code and any result message includes 'Alarm updated successfully.'",
        "depends": [],
        "expected_effect": "Verify that the alarm was updated correctly after a successful update.",
        "side_effect_risk": "Low, as it only verifies post-update."
    },
    {
        "id": "e2",
        "capability": "ToolUse",
        "impl": "Prompt",
        "trigger": "apis.phone.update_alarm in code and before calling complete_task",
        "depends": [],
        "expected_effect": "Ensure correct alarm id and time are set, matching the update requirements.",
        "side_effect_risk": "Medium, due to possible interaction with the model's decision-making."
    }
]

def e1_post_exec(code, out, state):
    # Check if an alarm update was successful
    if "apis.phone.update_alarm" in code and "Alarm updated successfully." in out:
        # Extract the alarm_id and token from code for verification
        pattern = r"alarm_id\s*=\s*(\d+).*?time\s*=\s*['\"](\d{2}:\d{2})['\"]"
        match = re.search(pattern, code, re.S)
        if match:
            alarm_id = match.group(1)
            updated_time = match.group(2)
            # Code to verify the alarm update
            verification_code = (
                f"verified_alarm = apis.phone.show_alarm(alarm_id={alarm_id}, "
                f"access_token=phone_login['access_token'])\n"
                f"assert verified_alarm['time'] == '{updated_time}', 'Alarm time mismatch: expected {updated_time}, got ' + verified_alarm['time']\n"
            )
            # Execute verification code
            exec(verification_code)

def e2_pre_complete(code, state):
    # Ensure alarm update has correct parameters before completing the task
    pattern = r"apis.phone.update_alarm\(alarm_id=(\d+),.*?time=['\"](\d{2}:\d{2})['\"]"
    match = re.search(pattern, code, re.S)
    if match:
        alarm_id = match.group(1)
        updated_time = match.group(2)
        if alarm_id == '431' and updated_time == '09:25':  # based on task's requirements
            return code
        else:
            return (
                "print('Warning: Attempted alarm update does not match the expected alarm_id or time.')\n"
                + code
            )
    return code
