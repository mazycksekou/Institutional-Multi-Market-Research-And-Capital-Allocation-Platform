param(
    [ValidateSet("quick", "full", "compile", "all")]
    [string]$Mode = "quick",
    [switch]$FallbackUnittest
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

function Test-PytestInstalled {
    python -m pytest --version *> $null
    return ($LASTEXITCODE -eq 0)
}

function Invoke-PytestRequired {
    param([string[]]$PytestArgs)
    if (-not (Test-PytestInstalled)) {
        if ($FallbackUnittest) {
            Write-Host "pytest not installed. Falling back to unittest because -FallbackUnittest was passed."
            python -m unittest discover -s tests -v
            exit $LASTEXITCODE
        }
        Write-Host "pytest not installed. Run .\scripts\setup_dev.ps1"
        exit 2
    }
    python -m pytest @PytestArgs
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Invoke-Compile {
    $Modules = @(
        "automation_scheduler/ops_workflow.py",
        "automation_scheduler/outcome_migration.py",
        "automation_scheduler/outcome_store.py",
        "automation_scheduler/paper_decision_ledger.py",
        "automation_scheduler/ncaaf_collegefootballdata_adapter.py",
        "automation_scheduler/budget_gates.py",
        "automation_scheduler/derived_feature_planner.py",
        "automation_scheduler/data_availability_tiers.py",
        "automation_scheduler/prediction_market_outcome_candidates.py",
        "automation_scheduler/deepseek_data_pull_check.py",
        "scripts/ops_check.py",
        "automation_scheduler/data_paths.py",
        "automation_scheduler/response_compactor.py",
        "main.py"
    )
    python -m py_compile @Modules
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

function Invoke-Quick {
    $Targets = @(
        "tests/test_data_paths.py",
        "tests/test_collector_scheduled_runner.py",
        "tests/test_data_source_registry.py",
        "tests/test_budget_gates.py",
        "tests/test_data_availability_tiers.py",
        "tests/test_derived_feature_planner.py",
        "tests/test_deepseek_data_pull_check_contract.py",
        "tests/test_ncaaf_collegefootballdata_adapter.py",
        "tests/test_data_source_endpoints.py",
        "tests/test_model_input_coverage.py",
        "tests/test_response_compactor.py",
        "tests/test_execution_later_gate.py",
        "tests/test_human_approval_gate.py",
        "tests/test_ops_workflow.py",
        "tests/test_ops_scripts_contract.py"
    )
    $ExistingTargets = @($Targets | Where-Object { Test-Path $_ })
    Invoke-PytestRequired -PytestArgs $ExistingTargets
}

switch ($Mode) {
    "quick" {
        Invoke-Quick
    }
    "full" {
        Invoke-PytestRequired -PytestArgs @()
    }
    "compile" {
        Invoke-Compile
    }
    "all" {
        Invoke-Quick
        Invoke-PytestRequired -PytestArgs @()
        Invoke-Compile
    }
}

exit 0
