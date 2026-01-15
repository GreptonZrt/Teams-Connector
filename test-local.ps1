# Test script for local Azure Functions

Write-Host "Testing Health Endpoint..." -ForegroundColor Cyan
try {
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:7071/api/health" -Method GET
    Write-Host "✓ Health check successful!" -ForegroundColor Green
    $healthResponse | ConvertTo-Json -Depth 3
} catch {
    Write-Host "✗ Health check failed: $_" -ForegroundColor Red
}

Write-Host "`nTesting Chat Endpoint..." -ForegroundColor Cyan
try {
    $body = @{
        message = "Hello from local test!"
    } | ConvertTo-Json
    
    $chatResponse = Invoke-RestMethod -Uri "http://localhost:7071/api/chat" -Method POST -Body $body -ContentType "application/json"
    Write-Host "✓ Chat request successful!" -ForegroundColor Green
    $chatResponse | ConvertTo-Json -Depth 3
} catch {
    Write-Host "✗ Chat request failed: $_" -ForegroundColor Red
}
