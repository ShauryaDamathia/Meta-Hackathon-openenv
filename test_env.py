from environment import SecurityEnv


env = SecurityEnv()

observation = env.reset()
print("Observation:", observation)
print("Agent prompt:", observation["agent_prompt"])

action = {
    "category": "brute_force",
    "severity": "high",
    "action": "block IP",
}

result = env.step(action)
print("Result:", result)
