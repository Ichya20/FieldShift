param([switch]$Refresh)
$ErrorActionPreference = 'Stop'
$taskRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$dataDirectory = Join-Path $taskRoot 'data/supplemental/crop-water'
$sourceDirectory = Join-Path $dataDirectory 'sources'
New-Item -ItemType Directory -Force -Path $sourceDirectory | Out-Null
$definitions = @(
    @{ id='fao56-table12'; url='https://www.fao.org/4/x0490e/x0490e0b.htm'; file='fao56-chapter6.html' },
    @{ id='fao56-table22'; url='https://www.fao.org/4/x0490e/x0490e0e.htm'; file='fao56-chapter8.html' }
)
$ledger = @()
foreach ($definition in $definitions) {
    $destination = Join-Path $sourceDirectory $definition.file
    if ($Refresh -or !(Test-Path -LiteralPath $destination)) {
        Invoke-WebRequest -Uri $definition.url -OutFile $destination -TimeoutSec 45
    }
    $ledger += @{
        id=$definition.id; url=$definition.url; path=('sources/' + $definition.file)
        source_snapshot_saved_at_utc=(Get-Item -LiteralPath $destination).LastWriteTimeUtc.ToString('o')
        timing_note='Local snapshot file-write time; a cache reuse is not a fresh network request.'
        bytes=(Get-Item -LiteralPath $destination).Length
        sha256=(Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToLowerInvariant()
        retrieval='HTTPS with system certificate validation; saved response bytes'
    }
}
[System.IO.File]::WriteAllText((Join-Path $dataDirectory 'source-evidence.json'),
    (@{ sources=$ledger } | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
Write-Output "Catalogued $($ledger.Count) official FAO reference sources."
