$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
  python -c "import json, automation_scheduler; r=automation_scheduler.get_scheduler_health(); print(json.dumps({'ok':r.get('ok',True),'dry_run':r.get('dry_run',True),'human_approval_required':r.get('human_approval_required',True),'auto_execution_enabled':r.get('auto_execution_enabled',False),'counts':{'review_queue_count':r.get('review_queue_count',0),'provider_count':r.get('provider_count',0)}}, indent=2))"
}
finally {
  Pop-Location
}
