$ErrorActionPreference = 'Stop'
Push-Location -LiteralPath $PSScriptRoot
try {
    & ./.venv/Scripts/python.exe -m PyInstaller --noconfirm --windowed --onedir --name AntibodyInsight --copy-metadata immunum --add-data "antibody_insight/ui;antibody_insight/ui" --add-data "examples;examples" --add-data "LICENSE;." --add-data "README.md;." --add-data "THIRD_PARTY.md;." antibody_insight/__main__.py
    if ($LASTEXITCODE -ne 0) { throw 'Packaging failed.' }
    $bundle = Join-Path $PSScriptRoot 'dist/AntibodyInsight'
    $archive = Join-Path $PSScriptRoot 'dist/AntibodyInsight-Windows-x64.zip'
    $temporary = "$archive.$([guid]::NewGuid()).tmp"
    try {
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [IO.Compression.ZipFile]::CreateFromDirectory($bundle, $temporary, [IO.Compression.CompressionLevel]::Optimal, $true)
        Move-Item -LiteralPath $temporary -Destination $archive -Force
    } finally {
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary }
    }
} finally { Pop-Location }
