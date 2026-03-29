import json


ALLOWED_CATEGORIES = ["brute_force", "malware", "phishing", "dos_attack", "normal"]
ALLOWED_SEVERITIES = ["low", "medium", "high"]
RESPONSE_EXAMPLE = {
    "category": "brute_force",
    "severity": "high",
    "action": "block source IP and enable rate limiting",
}

BASE_AGENT_INSTRUCTIONS = (
    "You are a cybersecurity log analysis agent. Analyze the provided system name "
    "and log entry, then return only a JSON object with exactly three keys: "
    "`category`, `severity`, and `action`. "
    f"`category` must be one of {ALLOWED_CATEGORIES}. "
    f"`severity` must be one of {ALLOWED_SEVERITIES}. "
    "`action` should be a short, concrete mitigation step. "
    "Do not add markdown, code fences, explanations, or extra keys."
)


def build_agent_prompt(log, system):
    example_json = json.dumps(RESPONSE_EXAMPLE)
    return (
        f"{BASE_AGENT_INSTRUCTIONS}\n\n"
        f"System: {system}\n"
        f"Log: {log}\n\n"
        "Return a response in this shape:\n"
        f"{example_json}"
    )


def build_agent_context(log, system):
    return {
        "instructions": BASE_AGENT_INSTRUCTIONS,
        "allowed_categories": ALLOWED_CATEGORIES,
        "allowed_severities": ALLOWED_SEVERITIES,
        "response_example": RESPONSE_EXAMPLE,
        "agent_prompt": build_agent_prompt(log, system),
    }
