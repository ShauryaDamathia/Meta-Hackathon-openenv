# Meta Hackathon OpenEnv - Cyber Security Log Analysis

This project exposes a small cybersecurity log-analysis environment with a FastAPI
server, a local environment class, and an agent evaluation script.

## Output contract

The agent must return only JSON with exactly these keys:

```json
{
  "category": "brute_force",
  "severity": "high",
  "action": "block source IP and enable rate limiting"
}
```

Allowed `category` values:

- `brute_force`
- `malware`
- `phishing`
- `dos_attack`
- `normal`

Allowed `severity` values:

- `low`
- `medium`
- `high`

`action` should be a short, concrete mitigation step.

## API endpoints

- `GET /reset` returns a random sample plus `instructions`, `allowed_categories`,
  `allowed_severities`, `response_example`, and `agent_prompt`.
- `POST /step` accepts the agent JSON payload and returns the normalized reward.
- `GET /state` returns the current step count.
- `GET /tasks` describes the task tiers and output contract.
- `POST /grader` scores a `predicted` payload against an `expected` payload.
- `GET /baseline` runs one simple baseline action against a fresh sample.

## Local setup

```bash
python -m venv .venv
. .venv/Scripts/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 7860
```

For PowerShell activation, use:

```powershell
.venv\Scripts\Activate.ps1
```

## Agent evaluation runner

`test_grader.py` is the local runner that calls a chat completions API, parses the
model output, grades it, and appends a record to `agent_eval_log.jsonl`.

Create a local `.env` file with:

```env
AGENT_API_KEY=your_api_key
AGENT_API_URL=https://api.openai.com/v1/chat/completions
```

Then run:

```bash
python test_grader.py
```

## Docker

Build and run the API container with:

```bash
docker build -t security-log-env .
docker run --rm -p 7860:7860 security-log-env
```

## Scoring

Scoring uses cosine similarity between vectorized predicted and expected responses.
The raw cosine value is mapped from `[-1, 1]` into the reward range `[0, 1]`:

- aligned vectors score `1`
- opposite vectors score `0`
