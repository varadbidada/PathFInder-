# Test script for MongoDB integration

Write-Host "`n=== Testing MongoDB Integration ===" -ForegroundColor Cyan

# 1. Test health endpoint
Write-Host "`n1. Testing health endpoint..." -ForegroundColor Yellow
$health = Invoke-RestMethod -Uri "http://localhost:8081/health" -Method Get
Write-Host "Status: $($health.status)" -ForegroundColor Green
Write-Host "MongoDB: $($health.mongodb.status) - $($health.mongodb.message)" -ForegroundColor Green

# 2. Start a session
Write-Host "`n2. Starting a counseling session..." -ForegroundColor Yellow
$sessionBody = @{
    exam_type = "jee_main"
    jee_rank = 15000
    budget_lakh = 10
    preferred_location = "Mumbai"
    name = "Test User"
    email = "testuser@example.com"
} | ConvertTo-Json

$session = Invoke-RestMethod -Uri "http://localhost:8081/session/start" -Method Post -Body $sessionBody -ContentType "application/json"
Write-Host "Session ID: $($session.session_id)" -ForegroundColor Green
Write-Host "First Question: $($session.first_question)" -ForegroundColor Cyan

$sessionId = $session.session_id

# 3. Send chat messages
Write-Host "`n3. Sending chat messages..." -ForegroundColor Yellow

$messages = @(
    "I prefer working on coding projects",
    "I enjoy solving complex problems",
    "I like hardware and building things"
)

foreach ($msg in $messages) {
    Write-Host "`nUser: $msg" -ForegroundColor Magenta
    
    $chatBody = @{
        session_id = $sessionId
        user_message = $msg
    } | ConvertTo-Json
    
    $response = Invoke-RestMethod -Uri "http://localhost:8081/chat" -Method Post -Body $chatBody -ContentType "application/json"
    Write-Host "AI: $($response.assistant_message)" -ForegroundColor Cyan
    Write-Host "Confidence: $([math]::Round($response.overall_confidence * 100, 2))%" -ForegroundColor Green
    Write-Host "Complete: $($response.is_complete)" -ForegroundColor Yellow
    
    Start-Sleep -Seconds 1
}

# 4. Check persisted data
Write-Host "`n4. Checking persisted data..." -ForegroundColor Yellow

# Get user profile
Write-Host "`nUser Profile:" -ForegroundColor Yellow
$user = Invoke-RestMethod -Uri "http://localhost:8081/api/persistence/user/$sessionId" -Method Get
Write-Host "User ID: $($user.user_id)" -ForegroundColor Green
Write-Host "Email: $($user.email)" -ForegroundColor Green
Write-Host "JEE Rank: $($user.jee_rank)" -ForegroundColor Green
Write-Host "Budget: $($user.budget_lakh) Lakh" -ForegroundColor Green
Write-Host "Location: $($user.preferred_location)" -ForegroundColor Green

# Get chat history
Write-Host "`nChat History:" -ForegroundColor Yellow
$history = Invoke-RestMethod -Uri "http://localhost:8081/api/persistence/chat-history/$sessionId" -Method Get
Write-Host "Total Messages: $($history.total_messages)" -ForegroundColor Green
foreach ($chat in $history.messages) {
    Write-Host "Q: $($chat.question)" -ForegroundColor Magenta
    Write-Host "A: $($chat.answer.Substring(0, [Math]::Min(80, $chat.answer.Length)))..." -ForegroundColor Cyan
}

# Get user summary
Write-Host "`nUser Summary:" -ForegroundColor Yellow
$summary = Invoke-RestMethod -Uri "http://localhost:8081/api/persistence/user-summary/$sessionId" -Method Get
Write-Host "Total Chats: $($summary.statistics.total_chat_messages)" -ForegroundColor Green
Write-Host "Total Resumes: $($summary.statistics.total_resumes)" -ForegroundColor Green
Write-Host "Total Roadmaps: $($summary.statistics.total_roadmaps)" -ForegroundColor Green

Write-Host "`n=== MongoDB Integration Test Complete! ===" -ForegroundColor Cyan
