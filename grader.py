def evaluate_action(action, category):
    keywords = {
        "brute_force": ["block", "rate limit", "lock"],
        "malware": ["scan", "remove", "quarantine"],
        "phishing": ["block", "warn", "report"],
        "dos_attack": ["rate limit", "block", "firewall"],
        "normal": ["no action", "monitor"]
    }

    action = action.lower()

    for word in keywords.get(category, []):
        if word in action:
            return 0.3

    return 0.0


def evaluate_severity(pred, actual):
    if pred == actual:
        return 0.3

    # partial credit
    levels = ["low", "medium", "high"]
    if abs(levels.index(pred) - levels.index(actual)) == 1:
        return 0.15

    return 0.0


def grade_response(predicted, expected):
    score = 0.0

    # category
    if predicted["category"] == expected["category"]:
        score += 0.4

    # severity
    score += evaluate_severity(
        predicted["severity"], expected["severity"]
    )

    # action
    score += evaluate_action(
        predicted["action"], expected["category"]
    )

    return min(score, 1.0)

