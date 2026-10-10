$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
& .\.venv\Scripts\python.exe scripts/start.py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
