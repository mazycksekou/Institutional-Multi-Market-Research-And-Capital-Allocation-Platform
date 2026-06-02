param(
    [string]$ProjectPath = "C:\Users\user\betting-stock-api-code-integration\betting stock api code intergration",
    [switch]$NoDeepSeek,
    [switch]$OpenReport
)

$ErrorActionPreference = "Stop"

function Write-LogLine {
    param([string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $line = "[$ts] $Message"
    Write-Host $line
    if ($script:LogPath) {
        Add-Content -Path $script:LogPath -Value $line -Encoding UTF8
    }
}

if (!(Test-Path $ProjectPath)) {
    Write-Host "Project path not found: $ProjectPath"
    exit 1
}

Set-Location $ProjectPath

$ReportDir = Join-Path $ProjectPath "reports\json_data_audit"
New-Item -ItemType Directory -Force $ReportDir | Out-Null
$script:LogPath = Join-Path $ReportDir "automation_log.txt"

Write-LogLine "Starting JSON audit pipeline."
Write-LogLine "ProjectPath=$ProjectPath"

$AuditScript = Join-Path $ProjectPath "scripts\analyze_json_data.py"
if (!(Test-Path $AuditScript)) {
    Write-LogLine "Missing audit script: $AuditScript"
    exit 1
}

$PythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $PythonCmd) {
    $PythonCmd = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $PythonCmd) {
    Write-LogLine "Python was not found. Install Python or add it to PATH."
    exit 1
}

Write-LogLine "Running audit script."
& $PythonCmd.Source $AuditScript
if ($LASTEXITCODE -ne 0) {
    Write-LogLine "Audit script failed with exit code $LASTEXITCODE."
    exit $LASTEXITCODE
}

$SummaryPath = Join-Path $ReportDir "latest_summary.md"
if (!(Test-Path $SummaryPath)) {
    Write-LogLine "Expected report not found: $SummaryPath"
    exit 1
}

Write-LogLine "Audit report created: $SummaryPath"

if (-not $NoDeepSeek) {
    try {
        if (Test-Path $PROFILE) {
            . $PROFILE
        }

        if (Get-Command ds -ErrorAction SilentlyContinue) {
            Write-LogLine "Sending compact report to DeepSeek for review."
            $Report = Get-Content $SummaryPath -Raw
            $Prompt = @"
You are my safe local data-review agent for the betting-stock-api project.

Review this JSON audit report and return:
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

Report:
$Report
"@
            $Review = ds $Prompt
            $ReviewPath = Join-Path $ReportDir "latest_deepseek_review.md"
            $Header = "# DeepSeek JSON Audit Review`r`n`r`nGenerated: $(Get-Date -Format o)`r`n`r`n"
            Set-Content -Path $ReviewPath -Value ($Header + $Review) -Encoding UTF8
            Write-LogLine "DeepSeek review created: $ReviewPath"
        }
        else {
            Write-LogLine "DeepSeek ds command not loaded. Audit completed; review skipped."
        }
    }
    catch {
        Write-LogLine "DeepSeek review failed, but audit completed. Error: $($_.Exception.Message)"
    }
}
else {
    Write-LogLine "DeepSeek review skipped because -NoDeepSeek was used."
}

if ($OpenReport) {
    notepad $SummaryPath
}

Write-LogLine "JSON audit pipeline finished."
