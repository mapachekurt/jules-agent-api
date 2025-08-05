# Jules Agent API: Development Summary for CLI Integration

## Overview
This project implements a FastAPI-based autonomous agent inspired by [Google Jules](https://jules.google/docs). Its purpose is to allow AI systems to automate development tasks by interacting with GitHub repositories programmatically through a REST API.

The agent performs the following steps:
- Accepts a prompt describing a desired code change
- Clones a specified GitHub repo
- Creates a new branch
- Modifies the code (e.g. appends to README)
- Runs optional tests (e.g., pytest)
- Commits the changes and pushes to GitHub
- Opens a pull request with the changes

This API is hosted on Railway and is triggered via simple HTTP calls.

---

## Key API Endpoints

### `POST /start-task`
Triggers a background agent task.

**Body Parameters:**
```json
{
  "prompt": "Describe the change you want",
  "github_repo_url": "https://github.com/mapachekurt/jules-agent-sandbox.git",
  "github_branch": "main",
  "test_command": "pytest"  // optional
}
```

**Response:**
```json
{ "task_id": "UUID" }
```

### `GET /task-status/{task_id}`
Returns the current status of the task: `running`, `completed`, or `failed`.

### `GET /task-result/{task_id}`
Returns the result (success message or error reason).

---

## GitHub Repositories

### [`jules-agent-api`](https://github.com/mapachekurt/jules-agent-api)
This repo contains the full backend service logic implemented with FastAPI. It’s responsible for processing incoming requests, managing tasks, and running the Git automation logic.

Deployed live at:
```
https://jules-agent-api-production.up.railway.app
```

### [`jules-agent-sandbox`](https://github.com/mapachekurt/jules-agent-sandbox)
This is the sandbox repo used by the agent to simulate real-world dev workflows. The agent:
- Clones this repo
- Appends content to the README
- Optionally runs tests
- Commits changes and opens pull requests

---

## Implementation Details

- Uses `uuid` to track task state
- Task status and results are stored in `/tmp/tasks.json` to survive container redeploys (limited persistence)
- GitHub actions require a valid `GITHUB_TOKEN` environment variable in Railway with `repo` scope
- Test command (e.g., `pytest`) is optional and will be skipped if the binary isn't available in the Docker container

---

## Known Issues & Workarounds
- If the test command binary isn’t installed, the task fails. The agent now checks if the test command exists before running it.
- State is lost on Railway container restart if `/tmp/tasks.json` is wiped. Redis or database support is a future improvement.
- Ensure test commands like `pytest` are available in the container or use a placeholder like `echo 'test passed'` during testing.

---

## Example CLI Usage
```bash
curl -X POST https://jules-agent-api-production.up.railway.app/start-task   -H "Content-Type: application/json"   -d '{
    "prompt": "Add usage instructions to README",
    "github_repo_url": "https://github.com/mapachekurt/jules-agent-sandbox.git",
    "github_branch": "main",
    "test_command": "echo 'tests passed'"
  }'

# Then poll:
curl https://jules-agent-api-production.up.railway.app/task-result/{task_id}
```

---

This summary is intended to help CLI-based AI tools quickly understand and interact with the project.