import json
import random
from pathlib import Path

from agent_contract import build_agent_context
from grader import grade_response


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET_PATH = BASE_DIR / "Dataset.json"


class SecurityEnv:
    def __init__(self, dataset_path=None):
        dataset_file = Path(dataset_path) if dataset_path else DEFAULT_DATASET_PATH
        if not dataset_file.is_absolute():
            dataset_file = BASE_DIR / dataset_file

        with dataset_file.open("r", encoding="utf-8") as handle:
            self.data = json.load(handle)

        self.current_sample = None
        self.step_count = 0

    def reset(self):
        self.current_sample = random.choice(self.data)
        self.step_count = 0

        observation = {
            "log": self.current_sample["log"],
            "system": self.current_sample["system"],
        }
        observation.update(
            build_agent_context(
                log=self.current_sample["log"],
                system=self.current_sample["system"],
            )
        )
        return observation

    def step(self, action):
        expected = self.current_sample["expected"]
        reward = grade_response(action, expected)
        self.step_count += 1

        return {
            "observation": None,
            "reward": reward,
            "done": True,
            "info": {
                "expected": expected,
            },
        }

    def state(self):
        return {
            "step_count": self.step_count,
        }
