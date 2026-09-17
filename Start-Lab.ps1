$ErrorActionPreference = 'Stop'
$labPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $labPython)) {
    throw 'Create the .venv environment and install the project using the README quick start first.'
}
Write-Host 'Open http://127.0.0.1:8765 in your browser. Keep this terminal open; Ctrl+C stops the app.'
& $labPython -m decision_lab serve
exit $LASTEXITCODE
