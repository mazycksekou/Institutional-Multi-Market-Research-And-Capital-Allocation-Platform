$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ReportPath = Join-Path $ProjectRoot "reports\json_data_audit\latest_summary.md"
$OutputPath = Join-Path $ProjectRoot "reports\json_data_audit\latest_deepseek_review.md"
$DebugPath = Join-Path $ProjectRoot "reports\json_data_audit\latest_deepseek_error_debug.txt"

if (!(Test-Path $ReportPath)) {
    Write-Host "Report not found: $ReportPath"
    exit 1
}

$Key = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "User")
if (-not $Key) { $Key = $env:DEEPSEEK_API_KEY }

if (-not $Key) {
    Write-Host "Missing DEEPSEEK_API_KEY."
    exit 1
}

$Report = Get-Content $ReportPath -Raw

# Critical fix: remove invalid Unicode/surrogate characters before JSON serialization.
$Report = $Report -replace '[^\x09\x0A\x0D\x20-\x7E]', ' '

# Extra safety: redact obvious secret-like text.
$Report = $Report -replace '(?i)(api[_-]?key|authorization|bearer|token|secret|signature|password)[^\r\n]{0,100}', '$1=[REDACTED]'

$MaxChars = 1200
if ($Report.Length -gt $MaxChars) {
    $CompactReport = $Report.Substring(0, $MaxChars)
} else {
    $CompactReport = $Report
}

$Prompt = @"
Review this JSON audit excerpt for my betting-stock-api project.

Return:
1. strongest data available now
2. messiest data
3. files to clean first
4. schemas to standardize
5. missing fields for calibration
6. safest next task for Codex
7. what DeepSeek can keep reviewing safely

Rules:
- no provider writes
- no live execution
- no bets/trades/orders
- no secrets handling
- no production data migration
- recommend read-only or test-only tasks first

Audit excerpt:
$CompactReport
"@

# Sanitize final prompt too.
$Prompt = $Prompt -replace '[^\x09\x0A\x0D\x20-\x7E]', ' '

$Body = @{
    model = "deepseek-v4-flash"
    messages = @(
        @{
            role = "user"
            content = $Prompt
        }
    )
    stream = $false
    max_tokens = 350
} | ConvertTo-Json -Depth 10 -Compress

try {
    $Res = Invoke-RestMethod `
        -Uri "https://api.deepseek.com/chat/completions" `
        -Method Post `
        -Headers @{
            Authorization = "Bearer $Key"
            "Content-Type" = "application/json"
        } `
        -Body $Body

    $Content = $Res.choices[0].message.content

    if (-not $Content) {
        $Content = "DeepSeek returned an empty response."
    }

    Set-Content $OutputPath "# DeepSeek JSON Audit Review`n`n$Content" -Encoding UTF8

    Write-Host "DeepSeek review created:"
    Write-Host $OutputPath
}
catch {
    $Msg = $_.Exception.Message

    $Debug = @"
DeepSeek request failed.

Message:
$Msg

Request body length:
$($Body.Length)

Report chars:
$($Report.Length)

Prompt chars:
$($Prompt.Length)
"@

    Set-Content $DebugPath $Debug -Encoding UTF8
    Set-Content $OutputPath "# DeepSeek Review Failed`n`n$Debug" -Encoding UTF8

    Write-Host "DeepSeek request failed:"
    Write-Host $Msg
    Write-Host "Debug written:"
    Write-Host $DebugPath
    exit 1
}
