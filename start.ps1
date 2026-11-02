param(
    [int]$Port = 8765,
    [string]$Database = ""
)

$ErrorActionPreference = "Stop"
Push-Location -LiteralPath $PSScriptRoot
try {
    $arguments = @("-m", "workspace_app.server", "--port", "$Port")
    if ($Database) { $arguments += @("--database", $Database) }
    & python @arguments
} finally {
    Pop-Location
}
