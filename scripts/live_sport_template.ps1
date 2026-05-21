$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"

# Starter template for a future active sport.
# 1. Add a New-<Sport>Payload function in live_payloads.ps1.
# 2. Register it in New-LiveActivePayload.
# 3. Set the expected model and optional calibration below.
# 4. Save this as scripts/live_<sport>_smoke.ps1.
# 5. Add the new script to live_all_smoke.ps1 once the sport is active.

$Sport = "future_sport_key"
$ExpectedModel = "future_model_family_name"
$ExpectedCalibration = ""

$rows = @()
$rows += Invoke-LiveTicketCheck -Check "missing input safety" -Payload (New-LiveMissingPayload -Sport $Sport) -Mode "safe_no_bet"
$rows += Invoke-LiveTicketCheck -Check "bad/text input safety" -Payload (New-LiveBadTextPayload -Sport $Sport) -Mode "safe_no_bet"
$rows += Invoke-LiveTicketCheck -Check "active model" -Payload (New-LiveActivePayload -Sport $Sport) -Mode "active" -ExpectedModel $ExpectedModel -ExpectedCalibration $ExpectedCalibration
Print-LiveCheckTable -Rows $rows
Exit-WithPassFail -Rows $rows -Label "$Sport live smoke"

