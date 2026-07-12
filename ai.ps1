Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Set-Location $PSScriptRoot is unnecessary here because the delegated script resolves its own root.
& (Join-Path $PSScriptRoot "scripts\deepseek_data_pull_check.ps1") @args
exit $LASTEXITCODE
