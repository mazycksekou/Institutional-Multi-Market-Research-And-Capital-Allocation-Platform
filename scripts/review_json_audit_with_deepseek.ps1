param(
    [int]$MaxReportChars = 6000
)

$ErrorActionPreference = "Stop"

$ProjectPath = "C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration"
$ReportPath = Join-Path $ProjectPath "reports\json_data_audit\latest_summary.md"
$JsonPath = Join-Path $ProjectPath "reports\json_data_audit\latest_summary.json"
$OutPath = Join-Path $ProjectPath "reports\json_data_audit\latest_deepseek_review.md"

function Clean-ForDeepSeek {
    param([string]$Text)
    if ($null -eq $Text) { return "" }
    $clean = $Text -replace "[^\u0009\u000A\u000D\u0020-\uD7FF\uE000-\uFFFD]", " "
    return $clean
}

function Read-LimitedText {
    param(
        [string]$Path,
        [int]$Limit
    )
    if (!(Test-Path $Path)) { return "" }
    $text = Get-Content $Path -Raw
    $text = Clean-ForDeepSeek $text
    if ($text.Length -gt $Limit) {
        return $text.Substring(0, $Limit) + "`n`n[TRUNCATED locally to avoid DeepSeek 400 request-size/format errors.]"
    }
    return $text
}

if (!(Test-Path $ReportPath)) {
    Write-Host "Report not found: $ReportPath"
    Write-Host "Run first: python scripts\analyze_json_data.py"
    exit 1
}

$Key = [Environment]::GetEnvironmentVariable("DEEPSEEK_API_KEY", "User")
if (-not $Key) { $Key = $env:DEEPSEEK_API_KEY }
if (-not $Key) {
    Write-Host "Missing DEEPSEEK_API_KEY. Set it before running this script."
    exit 1
}

$Report = Read-LimitedText -Path $ReportPath -Limit $MaxReportChars
$JsonDigest = ""

if (Test-Path $JsonPath) {
    try {
        $parsed = Get-Content $JsonPath -Raw | ConvertFrom-Json
        $digestObj = [ordered]@{}
        foreach ($name in @("files_scanned", "issues_found", "file_count", "issue_count", "summary", "issues", "top_issues", "record_type_counts", "schema_drift", "duplicates")) {
            if ($parsed.PSObject.Properties.Name -contains $name) {
                $digestObj[$name] = $parsed.$name
            }
        }
        if ($digestObj.Count -gt 0) {
            $JsonDigest = ($digestObj | ConvertTo-Json -Depth 8 -Compress)
            if ($JsonDigest.Length -gt 3000) { $JsonDigest = $JsonDigest.Substring(0, 3000) + " [TRUNCATED]" }
        }
    }
    catch {
        $JsonDigest = "Could not parse latest_summary.json: $($_.Exception.Message)"
    }
}

$Prompt = @"
You are my safe data-review agent for the betting-stock-api project.

Review this compact JSON audit report and return a practical build plan.

Return exactly these sections:
1. Strongest data available now
2. Messiest data
3. Files/data areas to clean first
4. Schemas to standardize
5. Missing fields for calibration
6. Safest next Codex task
7. What DeepSeek can keep reviewing safely

Rules:
- no provider writes
- no live execution
- no bets/trades/orders
- no secrets handling
- no production data migration
- recommend read-only or test-only tasks first
- be concrete and concise

Optional JSON digest:
$JsonDigest

Markdown report excerpt:
$Report
"@

$Prompt = Clean-ForDeepSeek $Prompt

$Body = @{
    model = "deepseek-v4-flash"
    messages = @(
        @{
            role = "system"
            content = "You are a concise software/data audit reviewer. Return safe, direct, actionable guidance."
        },
        @{
            role = "user"
            content = $Prompt
        }
    )
    stream = $false
    max_tokens = 1000
} | ConvertTo-Json -Depth 10

try {
    $Response = Invoke-RestMethod `
        -Uri "https://api.deepseek.com/chat/completions" `
        -Method Post `
        -Headers @{ Authorization = "Bearer $Key"; "Content-Type" = "application/json" } `
        -Body $Body

    $Content = $Response.choices[0].message.content
    if (-not $Content) { $Content = "DeepSeek returned an empty response." }
    $Content | Set-Content $OutPath -Encoding UTF8
    Write-Host "DeepSeek review saved to: $OutPath"
}
catch {
    $ErrorText = "DeepSeek request failed:`n$($_.Exception.Message)"
    try {
        if ($_.Exception.Response -and $_.Exception.Response.GetResponseStream()) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $ErrorText += "`n" + $reader.ReadToEnd()
        }
    }
    catch {}

    $ErrorText | Set-Content $OutPath -Encoding UTF8
    Write-Host $ErrorText
    exit 1
}
