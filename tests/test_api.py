#!/usr/bin/env python3
"""
Jules Agent API Test Suite
Tests the API endpoints and workflows for n8n integration
"""

import requests
import json
import time
import sys
import os
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8000"
LIVE_API_URL = "https://jules-agent-api-production.up.railway.app"

class JulesAgentTester:
    def __init__(self, base_url: str = LIVE_API_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
    def test_health_check(self) -> bool:
        """Test the health check endpoint"""
        print("🔍 Testing health check...")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    def start_task(self, prompt: str, repo_url: str, branch: str = "main", 
                   test_command: str = None) -> Dict[str, Any]:
        """Start a new task"""
        payload = {
            "prompt": prompt,
            "github_repo_url": repo_url,
            "github_branch": branch
        }
        if test_command:
            payload["test_command"] = test_command
            
        print(f"🚀 Starting task: {prompt}")
        print(f"📂 Repository: {repo_url}")
        
        try:
            response = self.session.post(f"{self.base_url}/start-task", json=payload)
            if response.status_code == 200:
                result = response.json()
                task_id = result.get("task_id")
                print(f"✅ Task started with ID: {task_id}")
                return {"success": True, "task_id": task_id}
            else:
                print(f"❌ Failed to start task: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
        except Exception as e:
            print(f"❌ Task start error: {e}")
            return {"success": False, "error": str(e)}
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status"""
        try:
            response = self.session.get(f"{self.base_url}/task-status/{task_id}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get status: {response.status_code}")
                return {"status": "error"}
        except Exception as e:
            print(f"❌ Status check error: {e}")
            return {"status": "error"}
    
    def get_task_result(self, task_id: str) -> Dict[str, Any]:
        """Get task result"""
        try:
            response = self.session.get(f"{self.base_url}/task-result/{task_id}")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ Failed to get result: {response.status_code}")
                return {"status": "error", "result": None}
        except Exception as e:
            print(f"❌ Result check error: {e}")
            return {"status": "error", "result": str(e)}
    
    def monitor_task(self, task_id: str, timeout: int = 300) -> Dict[str, Any]:
        """Monitor a task until completion or timeout"""
        print(f"⏳ Monitoring task {task_id}...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            current_status = status.get("status", "unknown")
            
            print(f"📊 Status: {current_status}")
            
            if current_status in ["completed", "failed"]:
                result = self.get_task_result(task_id)
                if current_status == "completed":
                    print(f"✅ Task completed successfully!")
                    print(f"🔗 Result: {result.get('result', 'No result')}")
                else:
                    print(f"❌ Task failed: {result.get('result', 'No error message')}")
                return result
                
            time.sleep(5)  # Wait 5 seconds before next check
        
        print(f"⏰ Task monitoring timed out after {timeout} seconds")
        return {"status": "timeout", "result": "Monitoring timed out"}
    
    def run_full_test(self, repo_url: str, prompt: str = "Add testing documentation", 
                      test_command: str = "echo 'Tests passed'") -> bool:
        """Run a complete end-to-end test"""
        print("\n" + "="*60)
        print("🧪 RUNNING FULL END-TO-END TEST")
        print("="*60)
        
        # Step 1: Health check
        if not self.test_health_check():
            return False
        
        # Step 2: Start task
        task_result = self.start_task(prompt, repo_url, test_command=test_command)
        if not task_result["success"]:
            return False
        
        task_id = task_result["task_id"]
        
        # Step 3: Monitor task
        final_result = self.monitor_task(task_id)
        
        return final_result.get("status") == "completed"


def test_with_sandbox_repo():
    """Test with the official sandbox repository"""
    tester = JulesAgentTester()
    
    sandbox_repo = "https://github.com/mapachekurt/jules-agent-sandbox.git"
    prompt = "Add API testing instructions to README"
    
    success = tester.run_full_test(sandbox_repo, prompt)
    
    if success:
        print("\n🎉 SANDBOX TEST PASSED!")
    else:
        print("\n💥 SANDBOX TEST FAILED!")
    
    return success


def test_live_vs_local():
    """Compare local vs live API responses"""
    print("\n" + "="*60)
    print("🔄 COMPARING LOCAL VS LIVE API")
    print("="*60)
    
    local_tester = JulesAgentTester(API_BASE_URL)
    live_tester = JulesAgentTester(LIVE_API_URL)
    
    print("Testing local API health...")
    local_health = local_tester.test_health_check()
    
    print("Testing live API health...")
    live_health = live_tester.test_health_check()
    
    if local_health and live_health:
        print("✅ Both APIs are healthy")
    elif live_health:
        print("⚠️  Live API healthy, local API not available")
    else:
        print("❌ API health checks failed")


def simulate_n8n_workflow():
    """Simulate how n8n would interact with the API"""
    print("\n" + "="*60)
    print("🤖 SIMULATING N8N WORKFLOW")
    print("="*60)
    
    # This simulates the typical n8n workflow:
    # 1. HTTP Request node calls /start-task
    # 2. Wait node delays for a few seconds
    # 3. Loop with HTTP Request to check /task-status
    # 4. When complete, HTTP Request to get /task-result
    
    tester = JulesAgentTester()
    
    # n8n would typically get these from workflow variables/forms
    workflow_data = {
        "repo_url": "https://github.com/mapachekurt/jules-agent-sandbox.git",
        "prompt": "Add n8n integration example",
        "branch": "main",
        "test_command": "echo 'n8n test passed'"
    }
    
    print("Step 1: n8n HTTP Request node - Start Task")
    task_result = tester.start_task(
        workflow_data["prompt"], 
        workflow_data["repo_url"],
        workflow_data["branch"],
        workflow_data["test_command"]
    )
    
    if not task_result["success"]:
        print("❌ n8n workflow would fail at task start")
        return False
    
    task_id = task_result["task_id"]
    print(f"📝 n8n would store task_id: {task_id}")
    
    print("Step 2: n8n Wait node - Initial delay")
    time.sleep(3)
    
    print("Step 3: n8n Loop - Status checking")
    max_attempts = 60  # n8n loop limit
    attempt = 0
    
    while attempt < max_attempts:
        attempt += 1
        print(f"  Loop iteration {attempt}: Checking status...")
        
        status = tester.get_task_status(task_id)
        current_status = status.get("status", "unknown")
        
        if current_status in ["completed", "failed"]:
            print("Step 4: n8n HTTP Request - Get final result")
            result = tester.get_task_result(task_id)
            
            if current_status == "completed":
                print("✅ n8n workflow would complete successfully")
                print(f"📤 n8n would output: {result}")
                return True
            else:
                print("❌ n8n workflow would handle failure")
                print(f"🚨 Error details: {result}")
                return False
        
        print(f"  Status: {current_status}, continuing loop...")
        time.sleep(5)  # n8n wait between loops
    
    print("⏰ n8n workflow would timeout")
    return False


if __name__ == "__main__":
    print("🚀 Jules Agent API Test Suite")
    print("="*40)
    
    # Check command line arguments
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        
        if test_type == "health":
            tester = JulesAgentTester()
            tester.test_health_check()
        elif test_type == "sandbox":
            test_with_sandbox_repo()
        elif test_type == "n8n":
            simulate_n8n_workflow()
        elif test_type == "compare":
            test_live_vs_local()
        else:
            print(f"Unknown test type: {test_type}")
            print("Available tests: health, sandbox, n8n, compare")
    else:
        # Run all tests
        print("Running all tests...\n")
        
        # Test API health
        test_live_vs_local()
        
        # Simulate n8n workflow
        n8n_success = simulate_n8n_workflow()
        
        # Test with sandbox repo
        sandbox_success = test_with_sandbox_repo()
        
        print("\n" + "="*60)
        print("📊 FINAL TEST RESULTS")
        print("="*60)
        print(f"n8n Workflow Simulation: {'✅ PASSED' if n8n_success else '❌ FAILED'}")
        print(f"Sandbox Repository Test: {'✅ PASSED' if sandbox_success else '❌ FAILED'}")
        
        if n8n_success and sandbox_success:
            print("\n🎉 ALL TESTS PASSED - Ready for n8n integration!")
            sys.exit(0)
        else:
            print("\n💥 SOME TESTS FAILED - Check the issues above")
            sys.exit(1)
