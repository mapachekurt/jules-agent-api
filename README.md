# 🧠 Jules-Style Agent API

An autonomous coding agent backend inspired by Google Jules. This FastAPI-based microservice clones a GitHub repository, makes changes (via an AI agent or simulated logic), runs tests, and creates a Pull Request—all via an API.

## 🚀 Features

- 🔁 GitHub integration (clone → branch → commit → PR)
- ✅ Optional test execution (e.g., `pytest`, `npm test`)
- 🧠 Agent prompt support for natural language task input
- 🔐 Secure GitHub token via environment variable
- ☁️ Railway-ready deployment (`Dockerfile` + `railway.json` included)

## 🧩 How It Works

1. POST a task to `/start-task` with your prompt and repo info
2. Agent clones the repo, creates a new branch
3. Simulated changes are made to `README.md`
4. Runs your test command if provided
5. Creates a PR with the result if tests pass

## 📦 API Endpoints

### `POST /start-task`

Start a new autonomous agent task.

**Body:**

```json
{
  "prompt": "Add a function to parse markdown files",
  "github_repo_url": "https://github.com/your/repo.git",
  "github_branch": "main",
  "test_command": "pytest"
}
```

**Response:**
```json
{
  "task_id": "generated-task-id"
}
```

---

### `GET /task-status/{task_id}`

Check the status of a submitted task (`running`, `completed`, `failed`).

---

### `GET /task-result/{task_id}`

Retrieve the result (e.g., link to the Pull Request or error output).

---

## 🔐 Environment Variables

Set the following in your Railway project settings:

- `GITHUB_TOKEN` — A GitHub personal access token with `repo` and `pull_request` scopes

---

## 🛠 Local Dev (Optional)

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

---

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Python comprehensive tests
python tests/test_api.py

# PowerShell quick test
.\tests\test_live.ps1

# Diagnostic test
python tests/diagnostic_test.py
```

## 🚀 READY FOR N8N INTEGRATION

The Jules Agent API is now fully compatible with n8n automations and workflows. For detailed integration instructions, see `TEST_RESULTS.md`. The current live API endpoint can be accessed at:
```
https://jules-agent-api-production.up.railway.app
```

---

## 📝 License

MIT