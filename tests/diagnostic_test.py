#!/usr/bin/env python3
"""
Diagnostic test to understand git commit failures
"""

import requests
import json
import time

LIVE_API_URL = "https://jules-agent-api-production.up.railway.app"

def run_diagnostic_test():
    """Run diagnostic test with minimal git operations"""
    print("🔬 DIAGNOSTIC TEST - Understanding Git Commit Failures")
    print("=" * 60)
    
    # Test with no test command to isolate the git issue
    payload = {
        "prompt": "DIAGNOSTIC: Test git operations",
        "github_repo_url": "https://github.com/mapachekurt/jules-agent-sandbox.git",
        "github_branch": "main"
        # No test_command to avoid additional complexity
    }
    
    print("📤 Starting diagnostic task...")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Start task
    response = requests.post(f"{LIVE_API_URL}/start-task", json=payload)
    if response.status_code != 200:
        print(f"❌ Failed to start task: {response.status_code} - {response.text}")
        return
    
    task_id = response.json()["task_id"]
    print(f"✅ Task started: {task_id}")
    
    # Monitor with more frequent checks
    print("\n⏳ Monitoring task (frequent checks)...")
    for attempt in range(1, 31):  # Check every 2 seconds for 1 minute
        print(f"  Check {attempt}/30...", end=" ")
        
        status_response = requests.get(f"{LIVE_API_URL}/task-status/{task_id}")
        if status_response.status_code == 200:
            status = status_response.json().get("status", "unknown")
            print(f"Status: {status}")
            
            if status in ["completed", "failed"]:
                # Get detailed result
                result_response = requests.get(f"{LIVE_API_URL}/task-result/{task_id}")
                if result_response.status_code == 200:
                    result = result_response.json()
                    print(f"\n📋 FINAL RESULT:")
                    print(f"Status: {result.get('status')}")
                    print(f"Result: {result.get('result')}")
                    
                    # Analyze the error
                    if "git commit" in str(result.get('result', '')):
                        print(f"\n🔍 ANALYSIS:")
                        print("The error is occurring during git commit.")
                        print("Exit status 128 typically means:")
                        print("- Git user.name and user.email are not configured")
                        print("- Or there are no changes to commit")
                        print("- Or there's a permissions issue")
                        
                        print(f"\n💡 RECOMMENDATIONS:")
                        print("1. Configure git user in the Docker container")
                        print("2. Add error handling for empty commits")
                        print("3. Add better logging for git operations")
                break
        else:
            print(f"Status check failed: {status_response.status_code}")
        
        time.sleep(2)
    else:
        print("⏰ Diagnostic test timed out")

if __name__ == "__main__":
    run_diagnostic_test()
