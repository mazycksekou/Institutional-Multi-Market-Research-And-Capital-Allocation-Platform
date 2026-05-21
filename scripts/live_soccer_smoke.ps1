$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
. "$ScriptDir\live_helpers.ps1"
. "$ScriptDir\live_checks.ps1"
. "$ScriptDir\live_payloads.ps1"
Invoke-LiveSportSmoke -Sport "soccer" -ExpectedModel "poisson_dixon_coles_bivariate_goal_model"

