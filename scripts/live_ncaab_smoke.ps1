$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"
Invoke-LiveSportSmoke -Sport "ncaab" -ExpectedModel "mens_college_basketball_possession_variance_model" -ExpectedCalibration "ncaab"

