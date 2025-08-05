# Jules Agent API Quick Test Script
# Tests the API endpoints using curl commands

param(
    [string]$BaseUrl = "https://jules-agent-api-production.up.railway.app",
    [string]$RepoUrl = "https://github.com/mapachekurt/jules-agent-sandbox.git",
    [string]$Prompt = "Add quick test documentation"
)

Write-Host "🚀 Jules Agent API Quick Test" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl" -ForegroundColor Yellow
Write-Host ""

# Test 1: Health Check
Write-Host "🔍 Testing health check..." -ForegroundColor Green
try {
    $healthResponse = Invoke-RestMethod -Uri "$BaseUrl/" -Method Get
    Write-Host "✅ Health check passed: $($healthResponse.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 2: Start Task
Write-Host ""
Write-Host "🚀 Starting task..." -ForegroundColor Green
$taskPayload = @{
    prompt = $Prompt
    github_repo_url = $RepoUrl
    github_branch = "main"
    test_command = "echo 'PowerShell test passed'"
} | ConvertTo-Json

try {
    $taskResponse = Invoke-RestMethod -Uri "$BaseUrl/start-task" -Method Post -Body $taskPayload -ContentType "application/json"
    $taskId = $taskResponse.task_id
    Write-Host "✅ Task started with ID: $taskId" -ForegroundColor Green
} catch {
    Write-Host "❌ Failed to start task: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# Test 3: Monitor Task Status
Write-Host ""
Write-Host "⏳ Monitoring task status..." -ForegroundColor Yellow
$maxAttempts = 60
$attempt = 0

do {
    $attempt++
    Write-Host "  Attempt $attempt of $maxAttempts..." -ForegroundColor Gray
    
    try {
        $statusResponse = Invoke-RestMethod -Uri "$BaseUrl/task-status/$taskId" -Method Get
        $status = $statusResponse.status
        Write-Host "  Status: $status" -ForegroundColor Yellow
        
        if ($status -eq "completed" -or $status -eq "failed") {
            break
        }
        
        Start-Sleep -Seconds 5
    } catch {
        Write-Host "  ❌ Status check failed: $($_.Exception.Message)" -ForegroundColor Red
        Start-Sleep -Seconds 5
    }
} while ($attempt -lt $maxAttempts)

# Test 4: Get Final Result
Write-Host ""
Write-Host "📋 Getting final result..." -ForegroundColor Green
try {
    $resultResponse = Invoke-RestMethod -Uri "$BaseUrl/task-result/$taskId" -Method Get
    $finalStatus = $resultResponse.status
    $result = $resultResponse.result
    
    if ($finalStatus -eq "completed") {
        Write-Host "✅ Task completed successfully!" -ForegroundColor Green
        Write-Host "🔗 Result: $result" -ForegroundColor Cyan
    } else {
        Write-Host "❌ Task failed: $result" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Failed to get result: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Test completed!" -ForegroundColor Cyan
