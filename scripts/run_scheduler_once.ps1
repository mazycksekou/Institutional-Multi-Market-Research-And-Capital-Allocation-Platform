$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
  python -c "import json; from automation_scheduler.scheduler_runner import run_scheduler_once; r=run_scheduler_once(dry_run=True); print(json.dumps({'run_id':r.get('run_id'),'dry_run':r.get('dry_run'),'report_path':(r.get('report') or {}).get('path'),'review_count':r.get('review_queue_size',0),'skipped_count':r.get('skipped_count',0)}, indent=2))"
}
finally {
  Pop-Location
}
