import json
import random
from grader import grade_response


class SecurityEnv:
    def __init__(self, dataset_path="dataset.json"):
        with open(dataset_path, "r") as f:
            self.data = json.load(f)

        self.current_sample = None
        self.step_count = 0

    def reset(self):
        self.current_sample = random.choice(self.data)
        self.step_count = 0

        return {
            "log": self.current_sample["log"],
            "system": self.current_sample["system"]
        }

    def step(self, action):
        expected = self.current_sample["expected"]

        reward = grade_response(action, expected)

        self.step_count += 1

        done = True  # one-step episode

        return {
            "observation": None,
            "reward": reward,
            "done": done,
            "info": {
                "expected": expected
            }
        }

    def state(self):
        return {
            "step_count": self.step_count
        }