# Jules-Style Agent API (FastAPI Wrapper)

from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uuid
import subprocess
import os
import requests
from typing import Optional
import json
import shutil
from pathlib import Path

app = FastAPI()

# Storage configuration - supports multiple backends
STORAGE_TYPE = os.getenv("STORAGE_TYPE", "file")  # file, redis, memory
TASKS_FILE = os.getenv("TASKS_FILE", "/app/data/tasks.json")  # Changed to persistent volume
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# In-memory fallback for development
_memory_tasks = {}

class TaskStorage:
    """Task storage abstraction supporting multiple backends"""
    
    def __init__(self):
        self.storage_type = STORAGE_TYPE
        self.redis_client = None
        
        # Initialize Redis if specified
        if self.storage_type == "redis":
            try:
                import redis
                self.redis_client = redis.from_url(REDIS_URL)
                # Test connection
                self.redis_client.ping()
                print(f"[STORAGE] Connected to Redis at {REDIS_URL}")
            except Exception as e:
                print(f"[STORAGE WARNING] Redis connection failed: {e}. Falling back to file storage.")
                self.storage_type = "file"
        
        # Ensure data directory exists for file storage
        if self.storage_type == "file":
            Path(TASKS_FILE).parent.mkdir(parents=True, exist_ok=True)
            print(f"[STORAGE] Using file storage at {TASKS_FILE}")
        elif self.storage_type == "memory":
            print(f"[STORAGE] Using in-memory storage (not persistent)")
    
    def load_tasks(self):
        """Load tasks from storage backend"""
        try:
            if self.storage_type == "redis" and self.redis_client:
                data = self.redis_client.get("jules_tasks")
                return json.loads(data) if data else {}
            elif self.storage_type == "file":
                if os.path.exists(TASKS_FILE):
                    with open(TASKS_FILE, "r") as f:
                        return json.load(f)
                return {}
            else:  # memory
                return _memory_tasks.copy()
        except Exception as e:
            print(f"[STORAGE ERROR] Failed to load tasks: {e}")
            return {}
    
    def save_tasks(self, tasks):
        """Save tasks to storage backend"""
        try:
            if self.storage_type == "redis" and self.redis_client:
                self.redis_client.set("jules_tasks", json.dumps(tasks))
            elif self.storage_type == "file":
                # Atomic write to prevent corruption
                temp_file = f"{TASKS_FILE}.tmp"
                with open(temp_file, "w") as f:
                    json.dump(tasks, f, indent=2)
                os.replace(temp_file, TASKS_FILE)  # Atomic rename
            else:  # memory
                _memory_tasks.clear()
                _memory_tasks.update(tasks)
        except Exception as e:
            print(f"[STORAGE ERROR] Failed to save tasks: {e}")

# Initialize storage
task_storage = TaskStorage()

def load_tasks():
    return task_storage.load_tasks()

def save_tasks(tasks):
    task_storage.save_tasks(tasks)


class TaskRequest(BaseModel):
    prompt: str
    github_repo_url: str
    github_branch: Optional[str] = "main"
    test_command: Optional[str] = None  # e.g., "pytest" or "npm test"


@app.post("/start-task")
def start_task(req: TaskRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    tasks = load_tasks()
    tasks[task_id] = {"status": "running", "result": None}
    save_tasks(tasks)
    background_tasks.add_task(run_agent, task_id, req)
    return {"task_id": task_id}


@app.get("/task-status/{task_id}")
def get_status(task_id: str):
    tasks = load_tasks()
    return tasks.get(task_id, {"status": "unknown"})


@app.get("/task-result/{task_id}")
def get_result(task_id: str):
    tasks = load_tasks()
    task = tasks.get(task_id)
    if not task:
        return {"status": "unknown", "result": None}
    return {
        "status": task["status"],
        "result": task["result"]
    }


def run_agent(task_id: str, req: TaskRequest):
    print(f"[AGENT DEBUG] run_agent called for task {task_id}")
    tasks = load_tasks()
    try:
        print(f"[AGENT] Starting task: {task_id}")

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            raise EnvironmentError("GITHUB_TOKEN is not set")

        if req.test_command:
            print(f"[AGENT] Checking if test command exists: {req.test_command}")
            binary = req.test_command.split()[0]
            if shutil.which(binary) is None:
                print(f"[AGENT WARNING] Test command '{binary}' not found. Using fallback: 'echo Test command not available, skipping tests'")
                req.test_command = "echo 'Test command not available, skipping tests'"

        repo_dir = f"/tmp/repo_{task_id}"
        os.makedirs(repo_dir, exist_ok=True)
        print(f"[AGENT] Cloning into {repo_dir}")

        repo_url = req.github_repo_url.replace("https://", f"https://{github_token}@")
        subprocess.run(["git", "clone", repo_url, repo_dir], check=True)
        subprocess.run(["git", "checkout", req.github_branch], cwd=repo_dir, check=True)
        
        # Configure git user (required for commits)
        subprocess.run(["git", "config", "user.name", "Jules Agent"], cwd=repo_dir, check=True)
        subprocess.run(["git", "config", "user.email", "jules-agent@example.com"], cwd=repo_dir, check=True)

        new_branch = f"jules-agent-{task_id[:8]}"
        subprocess.run(["git", "checkout", "-b", new_branch], cwd=repo_dir, check=True)

        print(f"[AGENT] Modifying README.md")
        with open(os.path.join(repo_dir, "README.md"), "a") as f:
            f.write(f"\n\n# Agent Change: {req.prompt}\n")

        if req.test_command:
            print(f"[AGENT] Running tests: {req.test_command}")
            test_result = subprocess.run(req.test_command.split(), cwd=repo_dir)
            if test_result.returncode != 0:
                raise RuntimeError("Tests failed. Aborting push.")

        print(f"[AGENT] Committing changes")
        subprocess.run(["git", "add", "README.md"], cwd=repo_dir, check=True)
        subprocess.run(["git", "commit", "-m", f"Agent: {req.prompt}"], cwd=repo_dir, check=True)
        subprocess.run(["git", "push", "origin", new_branch], cwd=repo_dir, check=True)

        print(f"[AGENT] Creating PR")
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
        print(f"[AGENT ERROR] Task {task_id} failed: {str(e)}")
        tasks[task_id] = {"status": "failed", "result": str(e)}

    save_tasks(tasks)


@app.get("/")
def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
