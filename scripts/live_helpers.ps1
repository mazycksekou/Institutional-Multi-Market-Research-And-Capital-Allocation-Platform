$ErrorActionPreference = "Stop"

$script:LiveEndpoint = "https://betting-stock-api-code-integration.onrender.com/api/actions/ticket/screenshot-analysis"
if ([type]::GetType("Net.ServicePointManager")) {
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
}

function Confirm-LiveApiKey {
    if ([string]::IsNullOrWhiteSpace($env:ACTION_API_KEY)) {
        Write-Host "ACTION_API_KEY is missing."
        exit 1
    }
}

function Get-LiveBoard {
    param([Parameter(Mandatory = $true)] $Response)
    $analysis = if ($Response.model_analysis) { $Response.model_analysis } else { $Response }
    if ($analysis.full_board) { return $analysis.full_board }
    if ($analysis.full_board_preview) { return $analysis.full_board_preview }
    if ($Response.full_board) { return $Response.full_board }
    if ($Response.full_board_preview) { return $Response.full_board_preview }
    return $null
}

function Get-LogbookRow {
    param([Parameter(Mandatory = $true)] $Response)
    $analysis = if ($Response.model_analysis) { $Response.model_analysis } else { $Response }
    if ($analysis.logbook_ready_rows -and $analysis.logbook_ready_rows.Count -gt 0) { return $analysis.logbook_ready_rows[0] }
    if ($analysis.logbook_ready_row) { return $analysis.logbook_ready_row }
    if ($Response.logbook_ready_rows -and $Response.logbook_ready_rows.Count -gt 0) { return $Response.logbook_ready_rows[0] }
    return $null
}

function Get-SameSelectionCounts {
    param([Parameter(Mandatory = $true)] $Response)
    $analysis = if ($Response.model_analysis) { $Response.model_analysis } else { $Response }
    $board = Get-LiveBoard -Response $Response
    $confirmed = @($analysis.confirmed_bets)
    if ($confirmed.Count -eq 0 -and $board) { $confirmed = @($board.confirmed_bets) }
    $noBets = @($analysis.no_bets)
    if ($board -and $board.no_bets) { $noBets += @($board.no_bets) }

    $sameNoBets = 0
    foreach ($bet in $confirmed) {
        foreach ($noBet in $noBets) {
            if (
                "$($bet.sport)" -eq "$($noBet.sport)" -and
                "$($bet.event)" -eq "$($noBet.event)" -and
                "$($bet.market)" -eq "$($noBet.market)" -and
                "$($bet.selection)" -eq "$($noBet.selection)"
            ) {
                $sameNoBets += 1
            }
        }
    }
    return [pscustomobject]@{
        ConfirmedCount = $confirmed.Count
        SameSelectionNoBets = $sameNoBets
    }
}

function New-LiveCheckRow {
    param(
        [Parameter(Mandatory = $true)] [string] $Check,
        [Parameter(Mandatory = $true)] $Payload,
        $Response,
        [bool] $Pass,
        [string] $ErrorMessage = ""
    )

    $analysis = if ($Response -and $Response.model_analysis) { $Response.model_analysis } elseif ($Response) { $Response } else { $null }
    $counts = if ($Response) { Get-SameSelectionCounts -Response $Response } else { [pscustomobject]@{ ConfirmedCount = 0; SameSelectionNoBets = 0 } }
    $board = if ($Response) { Get-LiveBoard -Response $Response } else { $null }
    $noBetCount = 0
    if ($analysis -and $analysis.no_bets) { $noBetCount += @($analysis.no_bets).Count }
    if ($board -and $board.no_bets) { $noBetCount += @($board.no_bets).Count }
    $missing = if ($analysis -and $analysis.missing_inputs) { @($analysis.missing_inputs).Count } else { 0 }
    return [pscustomobject]@{
        Check = $Check
        Ok = if ($Response) { [bool]$Response.ok } else { $false }
        Sport = if ($analysis -and $analysis.sport) { $analysis.sport } else { $Payload.sport }
        Market = if ($analysis -and $analysis.market) { $analysis.market } else { $Payload.market }
        Selection = if ($analysis -and $analysis.selection) { $analysis.selection } else { $Payload.selection }
        Model = if ($analysis) { $analysis.model_name } else { "" }
        ModelStatus = if ($analysis) { $analysis.model_status } else { "request_failed" }
        Calibration = if ($analysis) { $analysis.league_calibration_applied } else { "" }
        FinalProbability = if ($analysis) { $analysis.final_probability } else { $null }
        EdgePercent = if ($analysis) { $analysis.edge_percent } else { $null }
        Confidence = if ($analysis) { $analysis.confidence } else { $null }
        Decision = if ($analysis) { $analysis.decision } else { "" }
        Status = if ($analysis) { $analysis.status } else { $ErrorMessage }
        Stake = if ($analysis) { $analysis.stake } else { 0 }
        SuggestedStake = if ($analysis) { $analysis.suggested_stake } else { 0 }
        ConfirmedCount = $counts.ConfirmedCount
        NoBetCount = $noBetCount
        SameSelectionNoBets = $counts.SameSelectionNoBets
        MissingInputs = $missing
        Pass = $Pass
    }
}

function Invoke-LiveTicketCheck {
    param(
        [Parameter(Mandatory = $true)] [string] $Check,
        [Parameter(Mandatory = $true)] $Payload,
        [Parameter(Mandatory = $true)] [ValidateSet("active", "safe_no_bet")] [string] $Mode,
        [string] $ExpectedModel,
        [string] $ExpectedCalibration
    )

    Confirm-LiveApiKey
    try {
        $json = $Payload | ConvertTo-Json -Depth 80 -Compress
        try {
            $response = Invoke-RestMethod -Method Post -Uri $script:LiveEndpoint -Headers @{ "X-API-Key" = $env:ACTION_API_KEY } -ContentType "application/json" -Body $json -TimeoutSec 60
        } catch {
            $firstError = $_.Exception.Message
            $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
            if (-not $curl) { throw }
            $raw = & curl.exe --max-time 60 --ssl-no-revoke -sS -X POST $script:LiveEndpoint -H "X-API-Key: $env:ACTION_API_KEY" -H "Content-Type: application/json" --data-raw $json 2>&1
            if ($LASTEXITCODE -eq 28) { throw "REQUEST_TIMEOUT" }
            if ($LASTEXITCODE -ne 0) { throw "curl.exe failed with exit code $LASTEXITCODE" }
            $response = $raw | ConvertFrom-Json
        }
        $pass = if ($Mode -eq "active") {
            Assert-ActiveModel -Response $response -ExpectedModel $ExpectedModel -ExpectedCalibration $ExpectedCalibration
        } else {
            Assert-SafeNoBet -Response $response
        }
        return New-LiveCheckRow -Check $Check -Payload $Payload -Response $response -Pass $pass
    } catch {
        $message = $_.Exception.Message
        if ($message -match "timed out|timeout|operation has timed out") {
            $message = "REQUEST_TIMEOUT"
        }
        return New-LiveCheckRow -Check $Check -Payload $Payload -Response $null -Pass $false -ErrorMessage $message
    }
}

function Print-LiveCheckTable {
    param([Parameter(Mandatory = $true)] [array] $Rows)
    foreach ($row in $Rows) {
        Write-Host "CHECK: $($row.Check)"
        Write-Host "PASS: $($row.Pass)"
        Write-Host "SPORT: $($row.Sport)"
        Write-Host "MODEL: $($row.Model)"
        Write-Host "STATUS: $($row.ModelStatus)"
        Write-Host "DECISION: $($row.Decision)"
        Write-Host "STAKE: $($row.Stake)"
        Write-Host "CONFIRMED: $($row.ConfirmedCount)"
        Write-Host "NO_BETS: $($row.NoBetCount)"
        Write-Host "SAME_SELECTION_NO_BETS: $($row.SameSelectionNoBets)"
        Write-Host "MISSING_INPUTS: $($row.MissingInputs)"
        if ($null -ne $row.FinalProbability -or $null -ne $row.EdgePercent -or $null -ne $row.Confidence -or -not [string]::IsNullOrWhiteSpace("$($row.Calibration)")) {
            Write-Host "FINAL_PROBABILITY: $($row.FinalProbability)"
            Write-Host "EDGE_PERCENT: $($row.EdgePercent)"
            Write-Host "CONFIDENCE: $($row.Confidence)"
            Write-Host "CALIBRATION: $($row.Calibration)"
        }
        if (-not [string]::IsNullOrWhiteSpace("$($row.Status)") -and "$($row.Status)" -ne "$($row.ModelStatus)") {
            Write-Host "RESULT_STATUS: $($row.Status)"
        }
        Write-Host "----------------------------------------"
    }
}

function Exit-WithPassFail {
    param(
        [Parameter(Mandatory = $true)] [array] $Rows,
        [string] $Label = "Live smoke"
    )
    $failed = @($Rows | Where-Object { -not $_.Pass })
    if ($failed.Count -eq 0) {
        Write-Host "PASS: $Label checks are clean."
        exit 0
    }
    Write-Host "FAIL: $Label checks need review."
    exit 1
}

function Invoke-LiveSportSmoke {
    param(
        [Parameter(Mandatory = $true)] [string] $Sport,
        [Parameter(Mandatory = $true)] [string] $ExpectedModel,
        [string] $ExpectedCalibration
    )
    $rows = @()
    $rows += Invoke-LiveTicketCheck -Check "missing input safety" -Payload (New-LiveMissingPayload -Sport $Sport) -Mode "safe_no_bet"
    $rows += Invoke-LiveTicketCheck -Check "bad/text input safety" -Payload (New-LiveBadTextPayload -Sport $Sport) -Mode "safe_no_bet"
    $rows += Invoke-LiveTicketCheck -Check "active model" -Payload (New-LiveActivePayload -Sport $Sport) -Mode "active" -ExpectedModel $ExpectedModel -ExpectedCalibration $ExpectedCalibration
    Print-LiveCheckTable -Rows $rows
    Exit-WithPassFail -Rows $rows -Label "$Sport live smoke"
}
