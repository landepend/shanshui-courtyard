param([switch]$RequireArchitecture)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$pairs = @(
    @{ Source='assets/characters/atang.glb'; Target='unity/Assets/Art/Characters/atang.glb'; Required=$true },
    @{ Source='assets/architecture/courtyard.glb'; Target='unity/Assets/Art/Architecture/courtyard.glb'; Required=[bool]$RequireArchitecture }
)
$records = @()
foreach ($pair in $pairs) {
    $sourcePath = Join-Path $projectRoot $pair.Source
    $targetPath = Join-Path $projectRoot $pair.Target
    if (-not (Test-Path -LiteralPath $sourcePath)) {
        if ($pair.Required) { throw "Missing source asset: $sourcePath" }
        Write-Warning "Architecture is not ready yet: $sourcePath"
        continue
    }
    New-Item -ItemType Directory -Path (Split-Path -Parent $targetPath) -Force | Out-Null
    Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
    $sourceHash = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
    $targetHash = (Get-FileHash -LiteralPath $targetPath -Algorithm SHA256).Hash
    if ($sourceHash -ne $targetHash) { throw "Copy hash mismatch: $targetPath" }
    $records += [pscustomobject]@{source=$pair.Source;target=$pair.Target;bytes=(Get-Item -LiteralPath $targetPath).Length;sha256=$targetHash}
}
$report = Join-Path $projectRoot 'tests/results/unity-asset-sync.json'
New-Item -ItemType Directory -Path (Split-Path -Parent $report) -Force | Out-Null
$records | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $report -Encoding utf8
$records | Format-Table -AutoSize
