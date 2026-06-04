# NFL Open Data partial-lane completion runner (v2 resume sessions).
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".\.venv\Scripts\Activate.ps1") {
    & ".\.venv\Scripts\Activate.ps1"
}

$Lanes = @(
    @{ SourceId = "nflverse_team_stats"; MaxFullAssets = 30; MaxSessions = 2 },
    @{ SourceId = "nflverse_weekly_player_stats"; MaxFullAssets = 30; MaxSessions = 2 },
    @{ SourceId = "nflverse_injuries"; MaxFullAssets = 20; MaxSessions = 2 },
    @{ SourceId = "nflverse_snap_counts"; MaxFullAssets = 15; MaxSessions = 2 },
    @{ SourceId = "nflverse_nextgen_stats"; MaxFullAssets = 10; MaxSessions = 2 },
    @{ SourceId = "nflverse_weekly_rosters"; MaxFullAssets = 25; MaxSessions = 3 },
    @{ SourceId = "nflverse_participation"; MaxFullAssets = 10; MaxSessions = 3 },
    @{ SourceId = "nflverse_roster_continuity"; MaxFullAssets = 25; MaxSessions = 3 },
    @{ SourceId = "nflverse_depth_charts"; MaxFullAssets = 6; MaxSessions = 5 },
    @{ SourceId = "nflverse_rosters"; MaxFullAssets = 12; MaxSessions = 8 },
    @{ SourceId = "nflverse_play_by_play"; MaxFullAssets = 6; MaxSessions = 6 },
    @{ SourceId = "nflverse_pace_or_play_volume"; MaxFullAssets = 6; MaxSessions = 6 }
)

$Summary = @()
foreach ($Lane in $Lanes) {
    $sid = $Lane.SourceId
    Write-Host "=== $sid ==="
    $last = $null
    for ($i = 1; $i -le $Lane.MaxSessions; $i++) {
        Write-Host "  session $i / $($Lane.MaxSessions) max_assets=$($Lane.MaxFullAssets)"
        $raw = & python -m automation_scheduler.nfl_open_data_backfill `
            --source-id $sid `
            --mode full_available_backfill `
            --allow-download `
            --max-full-assets $Lane.MaxFullAssets `
            --resume `
            --persist 2>$null
        $text = ($raw | Out-String).Trim()
        $start = $text.LastIndexOf("{")
        if ($start -ge 0) {
            $last = $text.Substring($start) | ConvertFrom-Json
            Write-Host "    ok=$($last.ok) records=$($last.records_validated) downloads=$($last.downloads_succeeded)"
            if ($last.feature_availability) { }
        }
        if ($last -and $last.ok -and $last.downloads_attempted -eq 0) {
            Write-Host "  lane complete (no pending downloads)"
            break
        }
    }
    $Summary += [pscustomobject]@{ SourceId = $sid; LastOk = $last.ok; Downloads = $last.downloads_attempted }
}

$Summary | Format-Table -AutoSize
