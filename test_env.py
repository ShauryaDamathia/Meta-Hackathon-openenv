from environment import SecurityEnv

env = SecurityEnv()

obs = env.reset()
print("Observation:", obs)

action = {
    "category": "brute_force",
    "severity": "high",
    "action": "block IP"
}

result = env.step(action)
print("Result:", result)