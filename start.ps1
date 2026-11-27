param([string]$Project)
$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    $arguments = @('-m', 'antibody_insight')
    if ($Project) { $arguments += $Project }
    & ./.venv/Scripts/python.exe @arguments
    if ($LASTEXITCODE -ne 0) { throw 'Antibody Insight exited with an error.' }
} finally { Pop-Location }
