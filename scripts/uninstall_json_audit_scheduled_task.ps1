param(
    [string]$TaskName = "BettingStockApiJsonAudit"
)

$ErrorActionPreference = "Stop"

python scripts/uninstall_json_audit_scheduled_task.py --task-name $TaskName
exit $LASTEXITCODE
