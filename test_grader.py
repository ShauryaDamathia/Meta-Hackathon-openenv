from grader import grade_response

pred = {
    "category": "brute_force",
    "severity": "high",
    "action": "block IP immediately"
}

expected = {
    "category": "brute_force",
    "severity": "high",
    "action": "block IP and rate limit"
}

print(grade_response(pred, expected))