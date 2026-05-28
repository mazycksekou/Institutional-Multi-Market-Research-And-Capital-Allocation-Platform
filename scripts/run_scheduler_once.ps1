$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

Push-Location $repoRoot
try {
@'
import json
import automation_scheduler

result = automation_scheduler.run_scheduler_once()
print(json.dumps(result, indent=2, sort_keys=True))
'@ | python -
}
finally {
    Pop-Location
}
