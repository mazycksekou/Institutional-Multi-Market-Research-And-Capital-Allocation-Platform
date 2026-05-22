$ErrorActionPreference = "Stop"

function Assert-NoSameSelectionOverlap {
    param(
        [Parameter(Mandatory = $true)] $Response
    )
    $counts = Get-SameSelectionCounts -Response $Response
    return ($counts.ConfirmedCount -eq 0 -or $counts.SameSelectionNoBets -eq 0)
}

function Assert-ActiveModel {
    param(
        [Parameter(Mandatory = $true)] $Response,
        [Parameter(Mandatory = $true)] [string] $ExpectedModel,
        [string] $ExpectedCalibration
    )

    $analysis = if ($Response.model_analysis) { $Response.model_analysis } else { $Response }
    if (-not $Response.ok) { return $false }
    if ($analysis.model_status -ne "active") { return $false }
    if ($analysis.model_name -ne $ExpectedModel) { return $false }
    if ($ExpectedCalibration -and $analysis.league_calibration_applied -ne $ExpectedCalibration) { return $false }
    if ($null -eq $analysis.final_probability) { return $false }
    if ($analysis.decision -eq "manual_review_required") { return $false }
    if ($analysis.status -eq "manual_review_required") { return $false }
    if (-not (Assert-NoSameSelectionOverlap -Response $Response)) { return $false }
    return $true
}

function Assert-SafeNoBet {
    param(
        [Parameter(Mandatory = $true)] $Response
    )

    $analysis = if ($Response.model_analysis) { $Response.model_analysis } else { $Response }
    if (-not $Response.ok) { return $false }
    if (($Response.confirmed_bets | Measure-Object).Count -ne 0) { return $false }
    if (($analysis.confirmed_bets | Measure-Object).Count -ne 0) { return $false }
    $stake = if ($null -ne $analysis.stake) { [double]$analysis.stake } else { 0 }
    $suggestedStake = if ($null -ne $analysis.suggested_stake) { [double]$analysis.suggested_stake } else { 0 }
    if ($stake -ne 0) { return $false }
    if ($suggestedStake -ne 0) { return $false }
    return $true
}
