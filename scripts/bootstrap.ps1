$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
py -3.12 scripts/bootstrap.py @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
