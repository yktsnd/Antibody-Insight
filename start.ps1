param(
    [int]$Port = 8765,
    [string]$Database = ""
)

$ErrorActionPreference = "Stop"
Push-Location -LiteralPath $PSScriptRoot
try {
    $arguments = @("-m", "workspace_app.server", "--port", "$Port")
    if ($Database) { $arguments += @("--database", $Database) }
    $taskPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
    if (Test-Path -LiteralPath $taskPython) { & $taskPython @arguments } else { & python @arguments }
} finally {
    Pop-Location
}
