from fastapi import FastAPI

from agent_contract import (
    ALLOWED_CATEGORIES,
    ALLOWED_SEVERITIES,
    BASE_AGENT_INSTRUCTIONS,
    RESPONSE_EXAMPLE,
)
from environment import SecurityEnv
from grader import grade_response

app = FastAPI(
    root_path="/",
    docs_url="/docs",
    redoc_url="/redoc"
)
env = SecurityEnv()

@app.get("/")
def root():
    return {"message": "Security Log OpenEnv is running"}

@app.get("/reset")
def reset():
    return env.reset()


@app.post("/step")
def step(action: dict):
    # ✅ Safe extraction (prevents crashes)
    safe_action = {
        "category": str(action.get("category", "")).strip().lower(),
        "severity": str(action.get("severity", "")).strip().lower(),
        "action": str(action.get("action", "")).strip()
    }

    return env.step(safe_action)


@app.get("/state")
def state():
    return env.state()


@app.get("/tasks")
def tasks():
    return {
        "tasks": [
            {
                "name": "easy",
                "description": "Detect normal vs attack",
            },
            {
                "name": "medium",
                "description": "Classify category",
            },
            {
                "name": "hard",
                "description": "Category + severity + action",
            },
        ],
        "output_contract": {
            "instructions": BASE_AGENT_INSTRUCTIONS,
            "allowed_categories": ALLOWED_CATEGORIES,
            "allowed_severities": ALLOWED_SEVERITIES,
            "response_example": RESPONSE_EXAMPLE,
        },
    }


@app.post("/grader")
def grader(data: dict):
    predicted = data["predicted"]
    expected = data["expected"]
    score = grade_response(predicted, expected)

    return {"score": score}


@app.get("/baseline")
def baseline():
    sample = env.reset()
    action = {
        "category": "normal",
        "severity": "low",
        "action": "monitor",
    }
    result = env.step(action)

    return {
        "observation": sample,
        "result": result,
    }
