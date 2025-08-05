# Jules-Style Agent API (FastAPI Wrapper)
# testing comment

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uuid
import subprocess
import os
import requests
from typing import Optional

app = FastAPI()
tasks = {}

class TaskRequest(BaseModel):
    prompt: str
    github_repo_url: str
    github_branch: Optional[str] = "main"
    test_command: Optional[str] = None  # e.g., "pytest" or "npm test"

@app.post("/start-task")
def start_task(req: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "running", "result": None}
    background_tasks.add_task(run_agent, task_id, req)
    return {"task_id": task_id}

@app.get("/task-status/{task_id}")
def get_status(task_id: str):
    return tasks.get(task_id, {"status": "unknown"})

@app.get("/task-result/{task_id}")
def get_result(task_id: str):
    task = tasks.get(task_id)
    if task and task["status"] == "completed":
        return {"result": task["result"]}
    return {"status": task["status"]}

def run_agent(task_id: str, req: TaskRequest):
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise EnvironmentError("GITHUB_TOKEN is not set")

        repo_dir = f"/tmp/repo_{task_id}"
        os.makedirs(repo_dir, exist_ok=True)

        repo_url = req.github_repo_url.replace("https://", f"https://{github_token}@")
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True)
        subprocess.run(["git", "checkout", req.github_branch], cwd=repo_dir, check=True)

        new_branch = f"jules-agent-{task_id[:8]}"
        subprocess.run(["git", "checkout", "-b", new_branch], cwd=repo_dir, check=True)

        with open(os.path.join(repo_dir, "README.md"), "a") as f:
            f.write(f"\n\n# Agent Change: {req.prompt}\n")

        if req.test_command:
            test_result = subprocess.run(req.test_command.split(), cwd=repo_dir)
            if test_result.returncode != 0:
                raise RuntimeError("Tests failed. Aborting push.")

        subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"Agent: {req.prompt}"], cwd=repo_dir, check=True)
        subprocess.run(["git", "push", "origin", new_branch], cwd=repo_dir, check=True)

        owner_repo = req.github_repo_url.rstrip(".git").split("github.com/")[-1]
        pr_data = {
            "title": f"Agent PR: {req.prompt[:50]}",
            "head": new_branch,
            "base": req.github_branch,
            "body": f"Changes proposed by agent for prompt: {req.prompt}"
        }
        response = requests.post(
            f"https://api.github.com/repos/{owner_repo}/pulls",
            headers={"Authorization": f"token {github_token}"},
            json=pr_data
        )
        response.raise_for_status()

        tasks[task_id] = {
            "status": "completed",
            "result": f"Pull request created: {response.json().get('html_url')}"
        }

    except Exception as e:
        tasks[task_id] = {"status": "failed", "result": str(e)}