param([switch]$Refresh)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$dataDirectory = Join-Path $taskRoot 'data/supplemental/regional-context'
$sourceDirectory = Join-Path $dataDirectory 'sources'
New-Item -ItemType Directory -Force -Path $sourceDirectory | Out-Null
$sourceDefinitions = @(
    @{ id='bmkg-klaten-forecast'; url='https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4=33.10.25.1003'; file='bmkg-klaten-forecast.json' },
    @{ id='bmkg-forecast-docs'; url='https://data.bmkg.go.id/prakiraan-cuaca/'; file='bmkg-forecast-docs.html' },
    @{ id='bmkg-klaten-location'; url='https://www.bmkg.go.id/cuaca/prakiraan-cuaca/33.10.25.1003'; file='bmkg-klaten-location.html' }
)
$ledgerPath = Join-Path $dataDirectory 'source-evidence.json'
$previous = @{}
if (Test-Path -LiteralPath $ledgerPath) {
    foreach ($entry in (Get-Content -LiteralPath $ledgerPath -Raw | ConvertFrom-Json).sources) {
        $previous[$entry.id] = $entry
    }
}
$ledger = @()
foreach ($definition in $sourceDefinitions) {
    $destination = Join-Path $sourceDirectory $definition.file
    if (!$Refresh -and (Test-Path -LiteralPath $destination) -and $previous.ContainsKey($definition.id)) {
        $ledger += $previous[$definition.id]
        continue
    }
    $fetchedAt = [DateTimeOffset]::UtcNow.ToString('o')
    $response = Invoke-WebRequest -Uri $definition.url -OutFile $destination -PassThru -TimeoutSec 45
    $ledger += @{
        id=$definition.id; url=$definition.url; retrieved_at_utc=$fetchedAt
        path=('sources/' + $definition.file); http_status=[int]$response.StatusCode
        bytes=(Get-Item -LiteralPath $destination).Length
        sha256=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        retrieval='HTTPS with system certificate validation; saved response bytes'
    }
}
$json = @{ sources=$ledger; retrieval_policy='Cached unless -Refresh is passed; no background refresh or backend is installed.' } | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($ledgerPath, $json, [System.Text.UTF8Encoding]::new($false))
Write-Output "Saved $($ledger.Count) official BMKG sources."
