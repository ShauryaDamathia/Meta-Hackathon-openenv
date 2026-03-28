from fastapi import FastAPI
from environment import SecurityEnv

app = FastAPI()

env = SecurityEnv()


@app.get("/reset")
def reset():
    return env.reset()


@app.post("/step")
def step(action: dict):
    return env.step(action)


@app.get("/state")
def state():
    return env.state()


# 🔹 Required: tasks endpoint
@app.get("/tasks")
def tasks():
    return {
        "tasks": [
            {
                "name": "easy",
                "description": "Detect normal vs attack"
            },
            {
                "name": "medium",
                "description": "Classify category"
            },
            {
                "name": "hard",
                "description": "Category + severity + action"
            }
        ]
    }


# 🔹 Required: grader endpoint
@app.post("/grader")
def grader(data: dict):
    predicted = data["predicted"]
    expected = data["expected"]

    from grader import grade_response
    score = grade_response(predicted, expected)

    return {"score": score}


# 🔹 Required: baseline endpoint
@app.get("/baseline")
def baseline():
    # dummy baseline (random guess for now)
    sample = env.reset()

    action = {
        "category": "normal",
        "severity": "low",
        "action": "monitor"
    }

    result = env.step(action)

    return {
        "observation": sample,
        "result": result
    }