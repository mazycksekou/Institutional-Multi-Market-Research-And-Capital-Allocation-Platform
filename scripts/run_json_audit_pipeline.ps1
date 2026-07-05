param(
    [string]$ProjectPath = (Split-Path -Parent $PSScriptRoot),
    [switch]$NoDeepSeek,
    [switch]$OpenReport
)

$ErrorActionPreference = "Stop"

$pythonArgs = @("scripts/run_json_audit_pipeline.py", "--project-path", $ProjectPath)
if ($NoDeepSeek) { $pythonArgs += "--no-deepseek" }
if ($OpenReport) { $pythonArgs += "--open-report" }
python @pythonArgs
exit $LASTEXITCODE
