[CmdletBinding()]
param(
    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'
$workspace = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $workspace 'tests/results/unity-csharp-syntax.json'
}
$OutputPath = [System.IO.Path]::GetFullPath($OutputPath)

# Reuse the Roslyn libraries already shipped with the running PowerShell host.
# This performs syntax parsing only; it does not download an SDK or load Unity assemblies.
$codeAnalysisPath = Join-Path $PSHOME 'Microsoft.CodeAnalysis.dll'
$csharpPath = Join-Path $PSHOME 'Microsoft.CodeAnalysis.CSharp.dll'
[System.Reflection.Assembly]::LoadFrom($codeAnalysisPath) | Out-Null
$csharpAssembly = [System.Reflection.Assembly]::LoadFrom($csharpPath)

$checkFiles = @(
    Get-ChildItem -LiteralPath (Join-Path $workspace 'unity/Assets/Scripts') -Filter '*.cs' -Recurse
    Get-ChildItem -LiteralPath (Join-Path $workspace 'unity/Assets/Editor') -Filter '*.cs'
) | Sort-Object FullName

$results = foreach ($checkFile in $checkFiles) {
    # Parse and hash the same byte snapshot so an independently edited file cannot
    # silently give the report a hash from a different revision than the parsed source.
    $bytes = [System.IO.File]::ReadAllBytes($checkFile.FullName)
    $source = [System.Text.Encoding]::UTF8.GetString($bytes).TrimStart([char]0xFEFF)
    $sha256 = [System.Convert]::ToHexString([System.Security.Cryptography.SHA256]::HashData($bytes))
    $tree = [Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree]::ParseText($source)
    $diagnostics = @($tree.GetDiagnostics())
    $errors = @($diagnostics | Where-Object Severity -eq 'Error')
    [pscustomobject][ordered]@{
        path = [System.IO.Path]::GetRelativePath($workspace, $checkFile.FullName).Replace('\', '/')
        sha256 = $sha256
        bytes = $bytes.Length
        errorCount = $errors.Count
        diagnosticCount = $diagnostics.Count
        diagnostics = @($diagnostics | ForEach-Object { $_.ToString() })
    }
}

$totalErrors = ($results | Measure-Object -Property errorCount -Sum).Sum
$report = [ordered]@{
    checkedAtUtc = [DateTime]::UtcNow.ToString('o')
    checker = 'Microsoft.CodeAnalysis.CSharp.CSharpSyntaxTree.ParseText'
    scope = 'C# syntax parsing only. This is NOT Unity assembly compilation, API/type checking, a build, or Play Mode validation.'
    powershellVersion = $PSVersionTable.PSVersion.ToString()
    roslynAssemblyVersion = $csharpAssembly.GetName().Version.ToString()
    roslynAssemblyPath = $csharpPath
    parseLanguageVersion = [Microsoft.CodeAnalysis.CSharp.CSharpParseOptions]::Default.LanguageVersion.ToString()
    invocationFromWorkspace = 'pwsh -NoProfile -File ./tools/check-unity-csharp-syntax.ps1'
    checkedFileCount = @($results).Count
    totalSyntaxErrors = [int]$totalErrors
    unityEditorCompilePerformed = $false
    unityApiOrTypeCheckPerformed = $false
    playModePerformed = $false
    files = @($results)
}

$outputDirectory = Split-Path -Parent $OutputPath
[System.IO.Directory]::CreateDirectory($outputDirectory) | Out-Null
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $OutputPath -Encoding utf8
$results | Select-Object path, errorCount, sha256 | Format-Table -AutoSize
Write-Output "Syntax report: $OutputPath"
Write-Output "Checked $(@($results).Count) files; syntax errors: $totalErrors. Unity compilation and Play Mode were NOT performed."
if ($totalErrors -gt 0) { exit 1 }
