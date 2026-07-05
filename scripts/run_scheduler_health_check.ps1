$ErrorActionPreference = "Stop"
python scripts/run_scheduler_health_check.py
exit $LASTEXITCODE
